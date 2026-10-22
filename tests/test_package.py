import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile


def test_reproducible_package_has_no_runtime_data():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("build", root / "scripts" / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = module.build()
    first = hashlib.sha256(output.read_bytes()).digest()
    module.build()
    assert hashlib.sha256(output.read_bytes()).digest() == first
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert "__init__.py" in names
        assert "manifest.json" in names
        assert "LICENSE.txt" in names
        assert "bridge.py" in names
        assert "setup_help.md" in names
        assert "setup_dialog.py" in names
        assert "ai_guide.json" in names
        assert "usage_help.md" in names
        assert not any("user_files" in name or "__pycache__" in name or "token" in name for name in names)
        assert b'"token": ""' in archive.read("config.json")
    bundle = module.build_mcpb()
    first_bundle = hashlib.sha256(bundle.read_bytes()).digest()
    module.build_mcpb()
    assert hashlib.sha256(bundle.read_bytes()).digest() == first_bundle
    with zipfile.ZipFile(bundle) as archive:
        extension = json.loads(archive.read("manifest.json"))
    with zipfile.ZipFile(output) as archive:
        addon = json.loads(archive.read("manifest.json"))
    assert extension["version"] == addon["version"] == module.VERSION
