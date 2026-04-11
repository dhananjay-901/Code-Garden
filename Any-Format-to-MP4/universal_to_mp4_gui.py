"""
Universal → MP4 batch converter (PyQt5)

Save as universal_to_mp4_gui.py and run:
    python universal_to_mp4_gui.py

Features:
- Accepts many input formats (avi, mkv, mov, wmv, flv, mts, mpg, ...).
- Drag & drop, add files/folders, auto-watch folders.
- Multithreaded conversions, per-file + overall progress.
- PyInstaller-friendly: auto-detect bundled ffmpeg/ffprobe in sys._MEIPASS.
"""

import sys
import os
import re
import shutil
import subprocess
from functools import partial

from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, QThreadPool, QSize, QFileSystemWatcher, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QListWidget, QListWidgetItem, QProgressBar, QMessageBox,
    QCheckBox, QLineEdit, QStyle, QFrame, QSpinBox
)

# Allowed input ext list (common video formats)
INPUT_EXTS = {".avi", ".mkv", ".mov", ".wmv", ".flv", ".mts", ".mpg", ".mpeg", ".mp4", ".m4v", ".3gp", ".3g2", ".ts", ".webm", ".vob"}

# ---------------------------
# Worker Signals
# ---------------------------
class WorkerSignals(QObject):
    progress = pyqtSignal(float)         # percent 0..100
    log = pyqtSignal(str)               # single-line log
    finished = pyqtSignal(bool, str)    # success, output_path
    started = pyqtSignal()

# ---------------------------
# Convert Worker
# ---------------------------
class ConvertWorker(QRunnable):
    def __init__(self, input_path, output_path, ffmpeg_path="ffmpeg", ffprobe_path="ffprobe", preset_args=None):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.signals = WorkerSignals()
        self._cancel = False
        self.preset_args = preset_args or ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "128k", "-y"]

    def kill(self):
        self._cancel = True

    def _get_duration(self):
        try:
            p = subprocess.run(
                [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", self.input_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8
            )
            out = p.stdout.strip()
            if out:
                return float(out)
        except Exception:
            pass
        return None

    @staticmethod
    def _time_to_seconds(tstr):
        try:
            h, m, s = tstr.split(":")
            return int(h)*3600 + int(m)*60 + float(s)
        except Exception:
            return 0.0

    def run(self):
        self.signals.started.emit()
        duration = self._get_duration()
        if duration is None:
            self.signals.log.emit("Could not read duration (ffprobe). Progress will be approximate.")

        cmd = [self.ffmpeg_path, "-i", self.input_path] + self.preset_args + [self.output_path]

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        except FileNotFoundError:
            self.signals.log.emit("ffmpeg not found. Set path or bundle ffmpeg with the app.")
            self.signals.finished.emit(False, "")
            return
        except Exception as e:
            self.signals.log.emit(f"Failed to start ffmpeg: {e}")
            self.signals.finished.emit(False, "")
            return

        time_re = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
        last = 0.0

        try:
            for line in proc.stderr:
                if self._cancel:
                    try: proc.kill()
                    except: pass
                    self.signals.log.emit("Conversion cancelled.")
                    self.signals.finished.emit(False, "")
                    return

                s = line.strip()
                if s:
                    self.signals.log.emit(s)

                m = time_re.search(s)
                if m and duration:
                    secs = self._time_to_seconds(m.group(1))
                    percent = min(100.0, (secs / duration) * 100.0)
                    if percent - last >= 0.5 or percent == 100.0:
                        last = percent
                        self.signals.progress.emit(percent)

            proc.wait()
            rc = proc.returncode
            if rc == 0:
                self.signals.progress.emit(100.0)
                self.signals.finished.emit(True, self.output_path)
            else:
                self.signals.log.emit(f"ffmpeg exited with code {rc}")
                self.signals.finished.emit(False, "")
        except Exception as e:
            try: proc.kill()
            except: pass
            self.signals.log.emit(f"Error: {e}")
            self.signals.finished.emit(False, "")

# ---------------------------
# Per-file widget
# ---------------------------
class FileItemWidget(QWidget):
    def __init__(self, src_path, dst_path):
        super().__init__()
        self.src = src_path
        self.dst = dst_path

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)

        self.lbl = QLabel(os.path.basename(src_path))
        self.lbl.setToolTip(src_path)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status = QLabel("Queued")
        self.status.setFixedWidth(120)
        self.btn_cancel = QPushButton()
        self.btn_cancel.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.btn_cancel.setFixedSize(QSize(28,28))

        left = QVBoxLayout()
        left.addWidget(self.lbl)
        left.addWidget(self.progress)

        layout.addLayout(left)
        layout.addWidget(self.status)
        layout.addWidget(self.btn_cancel)
        self.setLayout(layout)

    def set_progress(self, p):
        self.progress.setValue(int(p))
        self.status.setText(f"{p:.1f}%")

    def set_done(self, ok):
        if ok:
            self.progress.setValue(100)
            self.status.setText("Done")
        else:
            self.status.setText("Failed")

# ---------------------------
# Main window
# ---------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal → MP4 Converter")
        self.resize(900, 650)
        self.threadpool = QThreadPool()
        self.items = {}  # src_path -> metadata
        self.ffmpeg_path, self.ffprobe_path = self._detect_bundled_ffmpeg()
        self.watcher = QFileSystemWatcher()
        self.watched = set()
        self._build_ui()

    def _detect_bundled_ffmpeg(self):
        """If running from PyInstaller onefile, check sys._MEIPASS for ffmpeg/ffprobe."""
        bundled = getattr(sys, "_MEIPASS", None)
        if bundled:
            # Windows: ffmpeg.exe; Linux/mac: ffmpeg
            cand = []
            if os.name == "nt":
                cand.append(os.path.join(bundled, "ffmpeg.exe"))
                cand.append(os.path.join(bundled, "ffprobe.exe"))
            else:
                cand.append(os.path.join(bundled, "ffmpeg"))
                cand.append(os.path.join(bundled, "ffprobe"))
            # if they exist, return them; else fall back to PATH names
            ffmpeg = cand[0] if os.path.exists(cand[0]) else "ffmpeg"
            ffprobe = cand[1] if os.path.exists(cand[1]) else "ffprobe"
            return ffmpeg, ffprobe
        # default to PATH
        return "ffmpeg", "ffprobe"

    def _build_ui(self):
        v = QVBoxLayout()

        top_row = QHBoxLayout()
        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_start = QPushButton("Start All")
        self.btn_stop = QPushButton("Stop All")
        self.chk_watch = QCheckBox("Watch folders (auto-add new files)")
        top_row.addWidget(self.btn_add_files)
        top_row.addWidget(self.btn_add_folder)
        top_row.addWidget(self.btn_start)
        top_row.addWidget(self.btn_stop)
        top_row.addWidget(self.chk_watch)
        top_row.addStretch()
        top_row.addWidget(QLabel("Threads:"))
        self.spin_threads = QSpinBox(); self.spin_threads.setMinimum(1); self.spin_threads.setMaximum(max(1, (os.cpu_count() or 2) * 2))
        self.spin_threads.setValue(self.threadpool.maxThreadCount())
        top_row.addWidget(self.spin_threads)

        path_row = QHBoxLayout()
        self.line_ffmpeg = QLineEdit(self.ffmpeg_path)
        self.line_ffmpeg.setPlaceholderText("ffmpeg path (leave as 'ffmpeg' if in PATH)")
        self.btn_browse_ffmpeg = QPushButton("Browse ffmpeg")
        path_row.addWidget(QLabel("FFmpeg:"))
        path_row.addWidget(self.line_ffmpeg)
        path_row.addWidget(self.btn_browse_ffmpeg)

        self.list_widget = QListWidget()
        self.list_widget.setAcceptDrops(False)

        overall_row = QHBoxLayout()
        self.overall = QProgressBar()
        self.lbl_overall = QLabel("Overall: 0/0")
        overall_row.addWidget(self.lbl_overall)
        overall_row.addWidget(self.overall)

        self.log = QLabel()
        self.log.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.log.setMinimumHeight(140)
        self.log.setWordWrap(True)
        self.log.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        v.addLayout(top_row)
        v.addLayout(path_row)
        v.addWidget(QLabel("Drag/drop files or folders onto this window"))
        v.addWidget(self.list_widget)
        v.addLayout(overall_row)
        v.addWidget(QLabel("Log:"))
        v.addWidget(self.log)

        self.setLayout(v)

        # connections
        self.btn_add_files.clicked.connect(self.add_files_dialog)
        self.btn_add_folder.clicked.connect(self.add_folder_dialog)
        self.btn_start.clicked.connect(self.start_all)
        self.btn_stop.clicked.connect(self.stop_all)
        self.btn_browse_ffmpeg.clicked.connect(self.browse_ffmpeg)
        self.spin_threads.valueChanged.connect(self._set_threads)
        self.chk_watch.stateChanged.connect(self._toggle_watch)
        self.watcher.directoryChanged.connect(self._on_folder_changed)
        self.setAcceptDrops(True)

        # periodic overall progress refresh
        t = QTimer()
        t.setInterval(500)
        t.timeout.connect(self._refresh_overall)
        t.start()

    # Drag & drop
    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()
    def dropEvent(self, ev):
        for u in ev.mimeData().urls():
            p = u.toLocalFile()
            if os.path.isdir(p):
                self._scan_folder(p)
            else:
                self._add_file(p)

    # Add files/folder
    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select video files", "", "Videos (*.avi *.mkv *.mov *.wmv *.flv *.mts *.mpg *.mpeg *.mp4 *.m4v *.3gp *.3g2 *.ts *.webm *.vob);;All files (*)")
        for f in files:
            self._add_file(f)

    def add_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            self._scan_folder(folder)

    def _add_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in INPUT_EXTS:
            # still allow other files if user insists? For safety, skip.
            return
        path = os.path.abspath(path)
        if path in self.items:
            return
        out = os.path.splitext(path)[0] + ".mp4"
        widget = FileItemWidget(path, out)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        widget.btn_cancel.clicked.connect(partial(self._cancel_item, path))
        self.items[path] = {"widget": widget, "item": item, "worker": None, "status": "queued"}
        self._log(f"Queued: {path}")

    def _scan_folder(self, folder):
        count = 0
        for root, _, files in os.walk(folder):
            for fn in files:
                if os.path.splitext(fn)[1].lower() in INPUT_EXTS:
                    self._add_file(os.path.join(root, fn))
                    count += 1
        self._log(f"Scanned {folder}: {count} files found.")
        if self.chk_watch.isChecked():
            self._watch_folder(folder)

    # folder watcher
    def _watch_folder(self, folder):
        if folder in self.watched: return
        try:
            self.watched.add(folder)
            self.watcher.addPath(folder)
            self._log(f"Watching: {folder}")
        except Exception as e:
            self._log(f"Watcher error: {e}")

    def _on_folder_changed(self, folder):
        self._log(f"Folder changed: {folder} — rescanning")
        self._scan_folder(folder)

    def _toggle_watch(self, state):
        if state == 0:
            for f in list(self.watched):
                try: self.watcher.removePath(f)
                except: pass
            self.watched.clear()
            self._log("Stopped watching folders.")

    # start / stop
    def start_all(self):
        self.ffmpeg_path = self.line_ffmpeg.text().strip() or self.ffmpeg_path
        self.ffprobe_path = shutil.which("ffprobe") or self.ffprobe_path
        queue = [p for p, m in self.items.items() if m["status"] in ("queued", "failed")]
        if not queue:
            QMessageBox.information(self, "Nothing to convert", "No queued files.")
            return
        for p in queue:
            self._start_conversion(p)

    def _start_conversion(self, src_path):
        meta = self.items.get(src_path)
        if not meta: return
        widget = meta["widget"]
        out = widget.dst
        worker = ConvertWorker(src_path, out, ffmpeg_path=self.ffmpeg_path, ffprobe_path=self.ffprobe_path)
        meta["worker"] = worker
        meta["status"] = "running"
        widget.status.setText("Starting...")
        worker.signals.progress.connect(partial(self._on_progress, src_path))
        worker.signals.log.connect(self._log)
        worker.signals.finished.connect(partial(self._on_finished, src_path))
        worker.signals.started.connect(partial(self._on_started, src_path))
        self.threadpool.start(worker)
        self._log(f"Started: {src_path}")

    def _on_started(self, src):
        m = self.items.get(src)
        if m: m["widget"].status.setText("Running")

    def _on_progress(self, src, percent):
        m = self.items.get(src)
        if m: m["widget"].set_progress(percent)

    def _on_finished(self, src, ok, outpath):
        m = self.items.get(src)
        if not m: return
        m["status"] = "done" if ok else "failed"
        m["worker"] = None
        m["widget"].set_done(ok)
        if ok:
            self._log(f"Finished: {src} → {outpath}")
        else:
            self._log(f"Failed: {src}")

    def stop_all(self):
        for p, m in list(self.items.items()):
            if m.get("worker"):
                try:
                    m["worker"].kill()
                    m["widget"].status.setText("Cancelling...")
                except:
                    pass
        self._log("Stop requested.")

    def _cancel_item(self, src):
        m = self.items.get(src)
        if not m: return
        if m.get("worker"):
            m["worker"].kill()
            m["widget"].status.setText("Cancelling...")
        else:
            # remove queued item
            self._remove_item(src)

    def _remove_item(self, src):
        meta = self.items.pop(src, None)
        if meta:
            row = self.list_widget.row(meta["item"])
            self.list_widget.takeItem(row)
            self._log(f"Removed: {src}")

    # utilities
    def _set_threads(self, n):
        self.threadpool.setMaxThreadCount(n)

    def _refresh_overall(self):
        total = len(self.items)
        if total == 0:
            self.overall.setValue(0)
            self.lbl_overall.setText("Overall: 0/0")
            return
        done = sum(1 for m in self.items.values() if m["status"] == "done")
        avg = sum(m["widget"].progress.value() for m in self.items.values()) / total
        self.overall.setValue(int(avg))
        self.lbl_overall.setText(f"Overall: {done}/{total} ({avg:.1f}%)")

    def _log(self, text):
        cur = self.log.text()
        new = cur + ("\n" if cur else "") + text
        if len(new) > 8000: new = new[-8000:]
        self.log.setText(new)

    def browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ffmpeg executable", "", "Executables (*.exe);;All Files (*)")
        if path:
            self.line_ffmpeg.setText(path)
            self.ffmpeg_path = path

# ---------------------------
# Run
# ---------------------------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
