"""Where the external programs are, so the tools work without Homebrew or a restarted shell.

rive:   on PATH, else the default install (~/.rive/bin/rive).
ffmpeg: on PATH, else the binary bundled with the imageio-ffmpeg package in the project venv.
usage from a shell: python bins.py rive|ffmpeg   (prints the path)
"""
import os
import shutil
import sys


def rive():
    return shutil.which("rive") or os.path.expanduser("~/.rive/bin/rive")


def ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


if __name__ == "__main__":
    print({"rive": rive, "ffmpeg": ffmpeg}[sys.argv[1]]())
