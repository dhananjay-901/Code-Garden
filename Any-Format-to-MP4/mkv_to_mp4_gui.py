"""
MKV -> MP4 batch converter with PyQt5 GUI, multithreading, drag-and-drop,
per-file progress, auto-scan/watch folder, and cancellation.

Save as mkv_to_mp4_gui.py and run: python mkv_to_mp4_gui.py
"""

import sys
import os
import re
import shutil
import subprocess
from functools import partial

from PyQt5.QtCore import (
    Qt, QObject, pyqtSignal, QRunnable, QThreadPool, QSize,
    QFileSystemWatcher, QTimer
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QListWidget, QListWidgetItem, QProgressBar,
    QMessageBox, QCheckBox, QLineEdit, QSpinBox, QStyle, QFrame
)

# ============================================================
# Worker Signals
# ============================================================
class WorkerSignals(QObject):
    progress = pyqtSignal(float)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    started = pyqtSignal()


# ============================================================
# Conversion Worker
# ============================================================
class ConvertWorker(QRunnable):

    def __init__(self, input_path, output_path, ffmpeg_path="ffmpeg", ffprobe_path="ffprobe"):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.signals = WorkerSignals()
        self.cancelled = False

    def kill(self):
        self.cancelled = True

    def get_duration(self):
        try:
            p = subprocess.run(
                [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", self.input_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return float(p.stdout.strip())
        except:
            return None

    def run(self):
        self.signals.started.emit()

        duration = self.get_duration()
        if duration is None:
            self.signals.log.emit("Could not read duration (ffprobe error). Progress may be inaccurate.")

        cmd = [
            self.ffmpeg_path, "-i", self.input_path,
            "-c:v", "libx264", "-c:a", "aac",
            "-y",
            self.output_path
        ]

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1
            )
        except FileNotFoundError:
            self.signals.log.emit("FFmpeg not found! Set correct ffmpeg path.")
            self.signals.finished.emit(False, "")
            return

        time_re = re.compile(r"time=(\d+:\d+:\d+\.\d+)")

        def t2s(t):
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)

        last_percent = 0

        for line in process.stderr:
            if self.cancelled:
                try: process.kill()
                except: pass
                self.signals.finished.emit(False, "")
                return

            line = line.strip()
            if line:
                self.signals.log.emit(line)

            m = time_re.search(line)
            if m and duration:
                current = t2s(m.group(1))
                percent = min(100, (current / duration) * 100)
                if percent - last_percent >= 0.5:
                    last_percent = percent
                    self.signals.progress.emit(percent)

        process.wait()

        if process.returncode == 0:
            self.signals.progress.emit(100)
            self.signals.finished.emit(True, self.output_path)
        else:
            self.signals.finished.emit(False, "")


# ============================================================
# Per-file widget
# ============================================================
class FileItemWidget(QWidget):
    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)

        self.lbl = QLabel(os.path.basename(input_path))
        self.lbl.setToolTip(input_path)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.status = QLabel("Queued")
        self.status.setFixedWidth(120)

        self.btn_cancel = QPushButton()
        self.btn_cancel.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        self.btn_cancel.setFixedSize(QSize(28, 28))

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


# ============================================================
# Main Window
# ============================================================
class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MKV → MP4 Converter (PyQt5)")

        self.threadpool = QThreadPool()
        self.items = {}  # path → dict
        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"
        self.watcher = QFileSystemWatcher()
        self.watched = set()

        self.build_ui()
    def browse_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(
        self,
        "Select ffmpeg executable",
        "",
        "Executable Files (*.exe);;All Files (*)"
        )
        if path:
            self.line_ffmpeg.setText(path)

    # ---------------------------------------------
    # GUI BUILD
    # ---------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout()

        row = QHBoxLayout()
        self.btn_add_files = QPushButton("Add MKV Files")
        self.btn_add_folder = QPushButton("Add Folder")
        self.btn_start = QPushButton("Start All")
        self.btn_stop = QPushButton("Stop All")

        self.chk_watch = QCheckBox("Auto-watch folders (add new MKV files)")

        row.addWidget(self.btn_add_files)
        row.addWidget(self.btn_add_folder)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        row.addWidget(self.chk_watch)
        row.addStretch()

        path_row = QHBoxLayout()
        self.line_ffmpeg = QLineEdit(self.ffmpeg_path)
        btn_browse = QPushButton("Browse ffmpeg")

        path_row.addWidget(QLabel("FFmpeg:"))
        path_row.addWidget(self.line_ffmpeg)
        path_row.addWidget(btn_browse)

        self.list = QListWidget()

        prog_row = QHBoxLayout()
        self.overall = QProgressBar()
        self.lbl_overall = QLabel("Overall: 0/0")
        prog_row.addWidget(self.lbl_overall)
        prog_row.addWidget(self.overall)

        self.log = QLabel()
        self.log.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.log.setMinimumHeight(120)
        self.log.setAlignment(Qt.AlignTop)
        self.log.setWordWrap(True)

        layout.addLayout(row)
        layout.addLayout(path_row)
        layout.addWidget(QLabel("Drag MKV files or folders here"))
        layout.addWidget(self.list)
        layout.addLayout(prog_row)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log)

        self.setLayout(layout)

        # signals
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_start.clicked.connect(self.start_all)
        self.btn_stop.clicked.connect(self.stop_all)
        btn_browse.clicked.connect(self.browse_ffmpeg)
        self.chk_watch.stateChanged.connect(self.toggle_watch)

        self.watcher.directoryChanged.connect(self.folder_changed)

        # overall progress update
        t = QTimer()
        t.setInterval(500)
        t.timeout.connect(self.update_overall)
        t.start()

        self.setAcceptDrops(True)

    # ---------------------------------------------
    # Drag and Drop
    # ---------------------------------------------
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            p = u.toLocalFile()
            if os.path.isdir(p):
                self.scan_folder(p)
            else:
                self.add_file(p)

    # ---------------------------------------------
    # File add
    # ---------------------------------------------
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MKV Files", "", "MKV Files (*.mkv)"
        )
        for f in files:
            self.add_file(f)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if folder:
            self.scan_folder(folder)

    def add_file(self, path):
        if not path.lower().endswith(".mkv"):
            return

        path = os.path.abspath(path)
        if path in self.items:
            return

        out = os.path.splitext(path)[0] + ".mp4"

        widget = FileItemWidget(path, out)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())

        self.list.addItem(item)
        self.list.setItemWidget(item, widget)

        widget.btn_cancel.clicked.connect(partial(self.cancel_item, path))

        self.items[path] = {
            "widget": widget,
            "item": item,
            "worker": None,
            "status": "queued"
        }

        self.log_msg(f"Queued: {path}")

    # ---------------------------------------------
    # Folder scan
    # ---------------------------------------------
    def scan_folder(self, folder):
        count = 0
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(".mkv"):
                    self.add_file(os.path.join(root, f))
                    count += 1

        self.log_msg(f"Scanned {folder}: {count} MKV files found.")

        if self.chk_watch.isChecked():
            self.watch_folder(folder)

    # ---------------------------------------------
    # Watcher
    # ---------------------------------------------
    def watch_folder(self, folder):
        if folder not in self.watched:
            self.watched.add(folder)
            self.watcher.addPath(folder)
            self.log_msg(f"Watching folder: {folder}")

    def folder_changed(self, folder):
        self.log_msg(f"Folder changed: {folder} — rescanning...")
        self.scan_folder(folder)

    def toggle_watch(self, state):
        if state == 0:
            for f in self.watched:
                try: self.watcher.removePath(f)
                except: pass
            self.watched.clear()
            self.log_msg("Stopped watching folders.")

    # ---------------------------------------------
    # Start conversions
    # ---------------------------------------------
    def start_all(self):
        self.ffmpeg_path = self.line_ffmpeg.text().strip() or "ffmpeg"
        self.ffprobe_path = shutil.which("ffprobe") or "ffprobe"

        queue = [p for p, m in self.items.items() if m["status"] in ("queued", "failed")]

        if not queue:
            QMessageBox.information(self, "Nothing to convert", "No MKV files queued.")
            return

        for p in queue:
            self.start_conversion(p)

    def start_conversion(self, path):
        meta = self.items[path]
        widget = meta["widget"]
        meta["status"] = "running"
        widget.status.setText("Running")

        worker = ConvertWorker(path, widget.output_path, self.ffmpeg_path, self.ffprobe_path)
        meta["worker"] = worker

        worker.signals.progress.connect(partial(self.progress_update, path))
        worker.signals.log.connect(self.log_msg)
        worker.signals.finished.connect(partial(self.finished, path))
        worker.signals.started.connect(partial(self.started, path))

        self.threadpool.start(worker)

    def started(self, path):
        self.items[path]["widget"].status.setText("Running")

    def progress_update(self, path, p):
        self.items[path]["widget"].set_progress(p)

    def finished(self, path, ok, out):
        meta = self.items[path]
        meta["status"] = "done" if ok else "failed"
        meta["widget"].set_done(ok)
        meta["worker"] = None

    # ---------------------------------------------
    # Cancel
    # ---------------------------------------------
    def stop_all(self):
        for p, m in self.items.items():
            if m["worker"]:
                m["worker"].kill()
                m["widget"].status.setText("Cancelling...")

    def cancel_item(self, path):
        m = self.items[path]
        if m["worker"]:
            m["worker"].kill()
            m["widget"].status.setText("Cancelling...")
        else:
            self.remove_item(path)

    def remove_item(self, path):
        meta = self.items.pop(path)
        row = self.list.row(meta["item"])
        self.list.takeItem(row)

    # ---------------------------------------------
    # Utilities
    # ---------------------------------------------
    def update_overall(self):
        total = len(self.items)
        if total == 0:
            self.overall.setValue(0)
            self.lbl_overall.setText("Overall: 0/0")
            return

        done = sum(1 for m in self.items.values() if m["status"] == "done")
        percent = sum(m["widget"].progress.value() for m in self.items.values()) / total

        self.lbl_overall.setText(f"Overall: {done}/{total} ({percent:.1f}%)")
        self.overall.setValue(int(percent))

    def log_msg(self, msg):
        cur = self.log.text()
        new = cur + ("\n" if cur else "") + msg
        if len(new) > 6000:
            new = new[-6000:]
        self.log.setText(new)


# ============================================================
# MAIN
# ============================================================
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
