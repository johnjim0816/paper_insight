from pathlib import Path


def test_start_script_exists_and_starts_both_apps():
    script = Path(__file__).resolve().parents[2] / "start.sh"

    assert script.exists()
    assert script.stat().st_mode & 0o111

    content = script.read_text()
    assert "command -v uv" in content
    assert "uv sync --extra dev" in content
    assert "uv run uvicorn app.main:app" in content
    assert "pip install" not in content
    assert "python3 -m venv" not in content
    assert "npm --prefix" in content
    assert 'FRONTEND_DIR="$ROOT_DIR/frontend"' in content
    assert "run dev" in content
    assert "trap cleanup" in content
