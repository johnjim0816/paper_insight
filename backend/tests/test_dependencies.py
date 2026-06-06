from pathlib import Path
import tomllib


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_backend_httpx_installs_socks_proxy_support():
    pyproject = tomllib.loads((ROOT_DIR / "backend" / "pyproject.toml").read_text())
    dependencies = pyproject["project"]["dependencies"]

    assert any(dependency.startswith("httpx[socks]") for dependency in dependencies)


def test_lockfile_includes_socksio():
    lockfile = tomllib.loads((ROOT_DIR / "backend" / "uv.lock").read_text())
    packages = {package["name"] for package in lockfile["package"]}

    assert "socksio" in packages
