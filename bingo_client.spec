# Build with: pyinstaller bingo_client.spec

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from pathlib import Path

# Your script name
script_path = Path("bingo_client.py")

# Include all PyQt5 modules + data (including platform plugins)
hidden_imports = collect_submodules("PyQt5")
hidden_imports += collect_submodules("websockets")

datas = collect_data_files("PyQt5")
datas = collect_data_files("websockets")

datas += [(str(p), os.path.join("resources", os.path.basename(p))) 
          for p in Path("resources").rglob("*") if p.is_file()]

a = Analysis(
    [str(script_path)],
    pathex=[str(script_path.parent)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="Bingo",
    console=False,
    icon="resources/icons/icon.ico",
    debug=False,
    strip=False,
    upx=False,
)
