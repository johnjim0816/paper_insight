from pathlib import Path

from app.core.config import default_data_dir, get_settings


def test_default_data_dir_uses_paper_insight_onedrive_paths():
    assert default_data_dir("windows") == Path("C:/Users/Administrator/OneDrive/ASELF/Data/PaperInsight/")
    assert default_data_dir("linux") == Path("/home/jj/OneDrive/ASELF/Data/PaperInsight/")
    assert default_data_dir("darwin") == Path(
        "/Users/johnjim/Library/CloudStorage/OneDrive-个人/ASELF/Data/PaperInsight/"
    )


def test_empty_data_dir_env_uses_default_path(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DATA_DIR", "")

    assert get_settings().data_dir == default_data_dir()
    get_settings.cache_clear()
