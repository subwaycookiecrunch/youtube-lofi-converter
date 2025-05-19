import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'desktop_app.py',
    '--name=LoFi_Converter',
    '--onefile',
    '--windowed',
    '--add-data=music.py;.',
    '--icon=NONE',
    '--clean',
    '--noconfirm'
]) 