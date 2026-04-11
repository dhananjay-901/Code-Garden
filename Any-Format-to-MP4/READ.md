Notes & tips

The program converts everything to H.264 (libx264) + AAC (widely compatible). You can modify preset_args in ConvertWorker to change bitrate, CRF, etc. (e.g. use -crf 23 -preset medium instead of -b:v).
Progress uses ffprobe to get duration (if available), then parses time= lines from ffmpeg to update progress. If ffprobe is missing or fails for a file, progress is approximate.
If you get ffmpeg not found on Windows, either:
install FFmpeg and add to PATH; or
bundle ffmpeg.exe/ffprobe.exe with the exe (see below). The program auto-detects bundled ffmpeg when run after PyInstaller.

Quick requirements

Python 3.8+
PyQt5: pip install PyQt5
FFmpeg & ffprobe available (or bundle them when building an exe — instructions below)


