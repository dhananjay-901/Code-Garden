"""
AVI -> MP4 batch converter with PyQt5 GUI, multithreading, drag-and-drop,
per-file progress, auto-scan/watch folder, and cancellation.

Save as avi_to_mp4_gui.py and run: python avi_to_mp4_gui.py
"""
import sys
import os
import re
import shutil
import subprocess
import math
from pathlib import Path
from functools import partial

from PyQt5.QtCore import (
    Qt, QObject, pyqtSignal, QRunnable, QThreadPool, QSize,
    QFileSystemWatcher, QTimer
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QListWidget, QListWidgetItem, QProgressBar,
    QMessageBox, QCheckBox, QLineEdit, QSpinBox, QComboBox, QStyle,
    QFrame
)

# --------------------
# Worker + Signals
# --------------------
class WorkerSignals(QObject):
    progress = pyqtSignal(float)         # 0..100
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)    # success, output_path
    started = pyqtSignal()

class ConvertWorker(QRunnable):
    """
    Worker that runs ffmpeg for one file and emits progress events.
    """
    def __init__(self, input_path: str, output_path: str, ffmpeg_path="ffmpeg", ffprobe_path="ffprobe", preset_args=None):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.signals = WorkerSignals()
        self.ffmpeg_path = ffmpeg_path or "ffmpeg"
        self.ffprobe_path = ffprobe_path or "ffprobe"
        self._is_killed = False
        self.preset_args = preset_args or ["-c:v", "libx264", "-c:a", "aac", "-y"]

    def kill(self):
        self._is_killed = True
        # The subprocess will be killed via attribute if stored; but we manage via returning.

    def _get_duration(self):
        try:
            proc = subprocess.run(
                [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", self.input_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            out = proc.stdout.strip()
            if out:
                return float(out)
        except Exception:
            pass
        return None

    @staticmethod
    def _time_to_seconds(tstr):
        # format: HH:MM:SS.micro
        try:
            parts = tstr.split(":")
            h, m = int(parts[0]), int(parts[1])
            s = float(parts[2])
            return h*3600 + m*60 + s
        except Exception:
            return 0.0

    def run(self):
        self.signals.started.emit()
        duration = self._get_duration()
        if duration is None:
            self.signals.log.emit("Could not determine duration (ffprobe missing or failed). Progress may be unavailable.")
            # We'll still parse ffmpeg time; progress may not be accurate.

        # Build ffmpeg command
        cmd = [self.ffmpeg_path, "-i", self.input_path] + self.preset_args + [self.output_path]

        # run ffmpeg and parse stderr for time=...
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        except FileNotFoundError:
            self.signals.log.emit("ffmpeg executable not found. Please ensure ffmpeg is installed and in PATH or set the path in settings.")
            self.signals.finished.emit(False, "")
            return
        except Exception as e:
            self.signals.log.emit(f"Failed to start ffmpeg: {e}")
            self.signals.finished.emit(False, "")
            return

        # read stderr lines progressively
        time_pattern = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
        last_percent = 0.0
        try:
            for raw_line in process.stderr:
                if self._is_killed:
                    try:
                        process.kill()
                    except Exception:
                        pass
                    self.signals.log.emit("Cancelled.")
                    self.signals.finished.emit(False, "")
                    return

                line = raw_line.strip()
                if line:
                    self.signals.log.emit(line)
                m = time_pattern.search(line)
                if m:
                    tstr = m.group(1)
                    secs = self._time_to_seconds(tstr)
                    if duration and duration > 0:
                        percent = min(100.0, (secs / duration) * 100.0)
                        # avoid spamming identical values
                        if percent - last_percent >= 0.5 or percent == 100.0:
                            last_percent = percent
                            self.signals.progress.emit(percent)
            process.wait()
            rc = process.returncode
            if rc == 0:
                # set progress to 100
                self.signals.progress.emit(100.0)
                self.signals.finished.emit(True, self.output_path)
            else:
                self.signals.log.emit(f"ffmpeg exited with code {rc}")
                self.signals.finished.emit(False, "")
        except Exception as e:
            try:
                process.kill()
            except Exception:
                pass
            self.signals.log.emit(f"Error during conversion: {e}")
            self.signals.finished.emit(False, "")

# --------------------
# UI: File list item widget
# --------------------
class FileItemWidget(QWidget):
    def __init__(self, file_path: str, output_path: str):
        super().__init__()
        self.file_path = file_path
        self.output_path = output_path
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        self.lbl_name = QLabel(os.path.basename(file_path))
        self.lbl_name.setToolTip(file_path)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.btn_cancel = QPushButton()
        self.btn_cancel.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.btn_cancel.setFixedSize(QSize(26, 26))
        self.btn_cancel.setToolTip("Cancel conversion")
        self.lbl_status = QLabel("Queued")
        self.lbl_status.setFixedWidth(120)

        left = QVBoxLayout()
        left.addWidget(self.lbl_name)
        left.addWidget(self.progress)

        layout.addLayout(left)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.btn_cancel)
        self.setLayout(layout)

    def set_progress(self, percent: float):
        self.progress.setValue(int(percent))
        self.lbl_status.setText(f"{percent:.1f}%")

    def set_done(self, success: bool, outpath: str):
        if success:
            self.progress.setValue(100)
            self.lbl_status.setText("Done")
        else:
            self.lbl_status.setText("Failed")

# --------------------
# Main Window
# --------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AVI → MP4 Converter (PyQt)")
        self.resize(800, 600)
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(max(1, os.cpu_count() or 2))
        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"
        self.items = {}  # input_path -> { widget_item, widget, worker (optional) }
        self.watcher = QFileSystemWatcher()
        self.watched_folders = set()

        self._build_ui()

    def _build_ui(self):
        vl = QVBoxLayout()
        control_row = QHBoxLayout()

        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_start_all = QPushButton("Start All")
        self.btn_stop_all = QPushButton("Stop All")
        self.chk_watch = QCheckBox("Watch folders (auto-add new .avi)")
        self.lbl_threads = QLabel("Threads:")
        self.spin_threads = QSpinBox()
        self.spin_threads.setMinimum(1)
        self.spin_threads.setMaximum(max(1, (os.cpu_count() or 2) * 2))
        self.spin_threads.setValue(self.threadpool.maxThreadCount())

        control_row.addWidget(self.btn_add_files)
        control_row.addWidget(self.btn_add_folder)
        control_row.addWidget(self.btn_start_all)
        control_row.addWidget(self.btn_stop_all)
        control_row.addWidget(self.chk_watch)
        control_row.addStretch()
        control_row.addWidget(self.lbl_threads)
        control_row.addWidget(self.spin_threads)

        path_row = QHBoxLayout()
        self.line_ffmpeg = QLineEdit(self.ffmpeg_path)
        self.line_ffmpeg.setPlaceholderText("ffmpeg path (leave as 'ffmpeg' if in PATH)")
        btn_browse_ffmpeg = QPushButton("Browse ffmpeg")
        self.btn_browse_ffmpeg = btn_browse_ffmpeg

        path_row.addWidget(QLabel("FFmpeg:"))
        path_row.addWidget(self.line_ffmpeg)
        path_row.addWidget(btn_browse_ffmpeg)

        self.list_widget = QListWidget()
        self.list_widget.setAcceptDrops(False)

        # overall progress
        overall_row = QHBoxLayout()
        self.overall_progress = QProgressBar()
        self.lbl_overall = QLabel("Overall: 0/0")
        overall_row.addWidget(self.lbl_overall)
        overall_row.addWidget(self.overall_progress)

        # log area (simple)
        self.log_label = QLabel("Log:")
        self.log_area = QLabel()
        self.log_area.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.log_area.setMinimumHeight(100)
        self.log_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.log_area.setWordWrap(True)

        vl.addLayout(control_row)
        vl.addLayout(path_row)
        vl.addWidget(QLabel("Drop files or folders onto this window"))
        vl.addWidget(self.list_widget)
        vl.addLayout(overall_row)
        vl.addWidget(self.log_label)
        vl.addWidget(self.log_area)

        self.setLayout(vl)

        # connect signals
        self.btn_add_files.clicked.connect(self.add_files_dialog)
        self.btn_add_folder.clicked.connect(self.add_folder_dialog)
        self.btn_start_all.clicked.connect(self.start_all)
        self.btn_stop_all.clicked.connect(self.stop_all)
        self.btn_browse_ffmpeg.clicked.connect(self.browse_ffmpeg)
        self.spin_threads.valueChanged.connect(self.update_threads)
        self.chk_watch.stateChanged.connect(self.update_watch)

        self.watcher.directoryChanged.connect(self._on_directory_changed)

        # drag & drop
        self.setAcceptDrops(True)

        # timer to refresh overall progress
        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._refresh_overall)
        self.timer.start()

    # --------------------
    # Drag & drop handlers
    # --------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for u in urls:
            path = u.toLocalFile()
            if os.path.isdir(path):
                self._add_folder(path)
            else:
                self._add_file(path)

    # --------------------
    # Add files/folders
    # --------------------
    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select AVI files", "", "AVI Files (*.avi);;All Files (*)")
        for f in files:
            self._add_file(f)

    def add_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._add_folder(folder)

    def _add_file(self, filepath):
        if not filepath.lower().endswith(".avi"):
            return
        abs_path = os.path.abspath(filepath)
        if abs_path in self.items:
            return
        outpath = os.path.splitext(abs_path)[0] + ".mp4"
        widget = FileItemWidget(abs_path, outpath)
        list_item = QListWidgetItem()
        list_item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, widget)
        self.items[abs_path] = {"list_item": list_item, "widget": widget, "worker": None, "status": "queued"}
        # connect cancel
        widget.btn_cancel.clicked.connect(partial(self._cancel_item, abs_path))
        self._log(f"Queued: {abs_path}")

    def _add_folder(self, folderpath):
        folderpath = os.path.abspath(folderpath)
        # scan for .avi
        added = 0
        for root, _, files in os.walk(folderpath):
            for fn in files:
                if fn.lower().endswith(".avi"):
                    self._add_file(os.path.join(root, fn))
                    added += 1
        self._log(f"Scanned folder {folderpath}: found {added} .avi files")
        # watch folder if checkbox enabled
        if self.chk_watch.isChecked():
            self._watch_folder(folderpath)

    # --------------------
    # Watcher
    # --------------------
    def _watch_folder(self, folderpath):
        if folderpath in self.watched_folders:
            return
        try:
            self.watcher.addPath(folderpath)
            self.watched_folders.add(folderpath)
            self._log(f"Watching folder: {folderpath}")
        except Exception as e:
            self._log(f"Failed to watch folder: {e}")

    def _on_directory_changed(self, path):
        # quick rescan of that folder for new .avi
        self._log(f"Folder changed: {path} — rescanning")
        for fn in os.listdir(path):
            if fn.lower().endswith(".avi"):
                full = os.path.join(path, fn)
                if full not in self.items:
                    self._add_file(full)

    def update_watch(self, state):
        if state == Qt.Checked:
            # add existing watched folders again
            for path in list(self.watched_folders):
                if os.path.exists(path):
                    try:
                        self.watcher.addPath(path)
                    except Exception:
                        pass
        else:
            for p in list(self.watched_folders):
                try:
                    self.watcher.removePath(p)
                except Exception:
                    pass
            self.watched_folders.clear()
            self._log("Stopped watching folders.")

    # --------------------
    # Conversion control
    # --------------------
    def start_all(self):
        # update ffmpeg paths from UI
        self.ffmpeg_path = self.line_ffmpeg.text().strip() or "ffmpeg"
        self.ffprobe_path = shutil.which("ffprobe") or "ffprobe"
        # apply thread count
        self.update_threads(self.spin_threads.value())

        queued = [p for p, meta in self.items.items() if meta["status"] in ("queued", "failed")]
        if not queued:
            QMessageBox.information(self, "Nothing to do", "No queued AVI files to convert.")
            return

        for path in queued:
            self._start_conversion(path)

    def _start_conversion(self, input_path):
        meta = self.items.get(input_path)
        if not meta:
            return
        widget = meta["widget"]
        outpath = meta["widget"].output_path
        worker = ConvertWorker(input_path, outpath, ffmpeg_path=self.ffmpeg_path, ffprobe_path=self.ffprobe_path)
        meta["worker"] = worker
        meta["status"] = "running"
        widget.lbl_status.setText("Starting...")
        # connect signals
        worker.signals.progress.connect(partial(self._on_progress, input_path))
        worker.signals.log.connect(partial(self._on_log, input_path))
        worker.signals.finished.connect(partial(self._on_finished, input_path))
        worker.signals.started.connect(partial(self._on_started, input_path))
        self.threadpool.start(worker)
        self._log(f"Started conversion: {input_path}")

    def _on_started(self, input_path):
        meta = self.items.get(input_path)
        if meta:
            meta["widget"].lbl_status.setText("Running")

    def _on_progress(self, input_path, percent):
        meta = self.items.get(input_path)
        if meta:
            meta["widget"].set_progress(percent)

    def _on_log(self, input_path, text):
        self._log(f"{os.path.basename(input_path)}: {text}")

    def _on_finished(self, input_path, success, output_path):
        meta = self.items.get(input_path)
        if meta:
            meta["widget"].set_done(success, output_path)
            meta["status"] = "done" if success else "failed"
            meta["worker"] = None
            if success:
                self._log(f"Finished: {input_path} → {output_path}")
            else:
                self._log(f"Failed: {input_path}")

    def stop_all(self):
        # try to cancel running workers
        for path, meta in list(self.items.items()):
            if meta.get("worker"):
                try:
                    meta["worker"].kill()
                    meta["widget"].lbl_status.setText("Cancelling")
                except Exception:
                    pass
        self._log("Stop requested for running conversions.")

    def _cancel_item(self, input_path):
        meta = self.items.get(input_path)
        if not meta:
            return
        worker = meta.get("worker")
        if worker:
            worker.kill()
            meta["widget"].lbl_status.setText("Cancelling")
        else:
            # if queued but not started, mark as cancelled/removed
            self._remove_item(input_path)

    def _remove_item(self, input_path):
        meta = self.items.pop(input_path, None)
        if meta:
            item = meta["list_item"]
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)
            self._log(f"Removed: {input_path}")

    # --------------------
    # Utility / UI helpers
    # --------------------
    def _refresh_overall(self):
        total = len(self.items)
        if total == 0:
            self.overall_progress.setValue(0)
            self.lbl_overall.setText("Overall: 0/0")
            return
        done_count = sum(1 for m in self.items.values() if m["status"] == "done")
        # compute average progress
        total_percent = 0.0
        for m in self.items.values():
            widget = m["widget"]
            total_percent += widget.progress.value()
        avg = total_percent / total if total > 0 else 0
        self.overall_progress.setValue(int(avg))
        self.lbl_overall.setText(f"Overall: {done_count}/{total} ({avg:.1f}%)")

    def _log(self, text):
        # append to simple log area (keep last ~5000 chars)
        cur = self.log_area.text()
        new = cur + ("\n" if cur else "") + text
        if len(new) > 5000:
            new = new[-5000:]
        self.log_area.setText(new)

    def browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ffmpeg executable", "", "Executables (*.exe);;All Files (*)")
        if path:
            self.line_ffmpeg.setText(path)
            self.ffmpeg_path = path

    def update_threads(self, n):
        self.threadpool.setMaxThreadCount(n)

# --------------------
# Run
# --------------------
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
