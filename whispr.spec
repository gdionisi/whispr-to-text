"""PyInstaller spec file for Whispr."""

a = Analysis(
    ["whispr/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "whispr.recorder",
        "whispr.transcriber",
        "whispr.typer",
        "pywhispercpp",
        "sounddevice",
        "pynput",
        "rumps",
        "numpy",
        "AppKit",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Whispr",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Whispr",
)

app = BUNDLE(
    coll,
    name="Whispr.app",
    bundle_identifier="com.whispr.app",
    info_plist={
        "CFBundleName": "Whispr",
        "CFBundleDisplayName": "Whispr",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "LSUIElement": True,
        "NSMicrophoneUsageDescription": "Whispr needs microphone access to record speech for transcription.",
    },
)
