# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Build Spec for ARUN Bot V1
a = Analysis(
    ['kickstart_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('database/', 'database/'),
        ('settings_default.json', '.'),
        ('config_table.csv', '.'),
        ('nifty50.py', '.'),
    ],
    hiddenimports=[
        'PIL',
        'PIL._tkinter_finder',
        'pandas',
        'numpy',
        'sqlite3',
        'cryptography',
        'customtkinter',
        'yfinance',
        'requests',
        'pytz',
        'disclaimer_gui',
        'settings_gui',
        'settings_manager',
        'risk_manager',
        'state_manager',
        'database.trades_db',
        'getRSI',
        'kickstart',
        'nifty50'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# CustomTkinter data files
from customtkinter import get_appearance_mode_or_theme
import customtkinter
import os
ctk_path = os.path.dirname(customtkinter.__file__)
a.datas += Tree(ctk_path, prefix='customtkinter')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ARUN_Bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Set True to see logs for debugging, False for GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
