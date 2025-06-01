# bina_cshera.spec
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None
APP_NAME = 'bina_cshera'
MAIN_SCRIPT = 'src/__main__.py'
FFMPEG_SOURCE_PATH = 'src/resources/ffmpeg/ffmpeg.exe'
FFMPEG_DEST_SUBDIR = '.'

# Collect data files
datas_to_collect = []

# Add FFmpeg binary if it exists
if os.path.exists(FFMPEG_SOURCE_PATH):
    datas_to_collect.append((FFMPEG_SOURCE_PATH, FFMPEG_DEST_SUBDIR))

# Add PySide6 plugins and resources
try:
    import PySide6
    pyside_path = Path(PySide6.__file__).parent
    
    # Add Qt plugins
    plugins_path = pyside_path / "Qt" / "plugins"
    if plugins_path.exists():
        datas_to_collect.append((str(plugins_path), "PySide6/Qt/plugins"))
    
    # Add Qt libraries
    qt_libs_path = pyside_path / "Qt" / "bin"
    if qt_libs_path.exists():
        datas_to_collect.append((str(qt_libs_path), "PySide6/Qt/bin"))
        
except ImportError:
    print("Warning: PySide6 not found, some features may not work in the executable")

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[
        os.getcwd(),
        os.path.join(os.getcwd(), 'src'),
    ],
    binaries=[], 
    datas=datas_to_collect, 
    hiddenimports=[
        'PySide6', 
        'PySide6.QtCore', 
        'PySide6.QtGui', 
        'PySide6.QtWidgets', 
        'PySide6.QtMultimedia',
        'PySide6.QtOpenGL',
        'PySide6.QtNetwork',
        'PySide6.QtSvg',
        'numpy',
        'scipy',
        'librosa',
        # Qt platform plugins for Windows
        'PySide6.plugins.platforms.qwindows',
        'PySide6.plugins.styles.qwindowsvistastyle',
        # Image format plugins
        'PySide6.plugins.imageformats.qgif',
        'PySide6.plugins.imageformats.qico',
        'PySide6.plugins.imageformats.qjpeg',
        'PySide6.plugins.imageformats.qpng',
        'PySide6.plugins.imageformats.qsvg',
        # Multimedia plugins for Windows
        'PySide6.plugins.multimedia.windowsaudioplugin',
        'PySide6.plugins.mediaservice.dsengine',
        'PySide6.plugins.mediaservice.wmfengine',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False, 
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    icon=None,  # Add icon path here if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas, 
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
