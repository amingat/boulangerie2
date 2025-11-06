# TrouvesTonPain.spec
# PyInstaller spec pour macOS (assets + PDF embarqués)

block_cipher = None

a = Analysis(
    ['app.py'],  # <-- adapte si ton fichier principal a un autre nom
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('CV - Arnaud MINGAT - Alternance -Développeur GenAI.pdf', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TrouvesTonPain',
    console=False,   # fenêtre terminal masquée
    disable_windowed_traceback=False,
    target_arch=None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, upx_exclude=[], name='TrouvesTonPain'
)

app = BUNDLE(
    coll,
    name='TrouvesTonPain.app',
    icon=None,   # tu peux mettre un .icns ici si tu as une icône
    bundle_identifier='com.tonorg.trouvestonpain',
)
