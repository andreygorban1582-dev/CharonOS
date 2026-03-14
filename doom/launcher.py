import subprocess
import os
import shutil

# Root folder of the project (one level above this file's directory)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def launch_doom():
    """
    Launches DOOM using an external engine (Chocolate Doom or DOSBox).
    Place doom1.wad in the project root directory, or install Chocolate Doom
    which looks for it in ~/.local/share/chocolate-doom/ on Linux.
    """
    doom_exe = shutil.which('chocolate-doom')
    if doom_exe is None:
        print("Chocolate Doom not found. Trying DOSBox...")
        dosbox = shutil.which('dosbox')
        if dosbox:
            # Assume DOOM.EXE and doom1.wad are placed in the project root
            doom_exe_path = os.path.join(_PROJECT_ROOT, 'DOOM.EXE')
            if os.path.exists(doom_exe_path):
                subprocess.Popen([dosbox, doom_exe_path], cwd=_PROJECT_ROOT)
            else:
                print(
                    "Please place DOOM shareware files (DOOM.EXE, doom1.wad) "
                    "in the project root folder."
                )
        else:
            print(
                "Neither Chocolate Doom nor DOSBox found. "
                "Install one of them and put doom1.wad in the project root folder."
            )
    else:
        # Look for doom1.wad in the project root or in standard locations
        wad_path = os.path.join(_PROJECT_ROOT, 'doom1.wad')
        if not os.path.exists(wad_path):
            wad_path = os.path.expanduser('~/.local/share/chocolate-doom/doom1.wad')
        if os.path.exists(wad_path):
            subprocess.Popen([doom_exe, '-iwad', wad_path])
        else:
            print(
                "doom1.wad not found. "
                "Please download the shareware version and place it in the project root folder."
            )
