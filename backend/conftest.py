"""
pytest configuration — runs before any test module is imported.

Sets FFMPEG_PATH from the known WinGet installation location if ffmpeg
is not already on PATH, so integration tests can find it.
"""

import os
import shutil

# Absolute path where winget installs FFmpeg on this machine
_WINGET_FFMPEG = (
    r"C:\Users\TANISHA SHARMA\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
)

if not shutil.which("ffmpeg"):
    if os.path.isfile(_WINGET_FFMPEG):
        # Inject into PATH so shutil.which() finds it for the test session
        ffmpeg_dir = os.path.dirname(_WINGET_FFMPEG)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        os.environ.setdefault("FFMPEG_PATH", _WINGET_FFMPEG)
