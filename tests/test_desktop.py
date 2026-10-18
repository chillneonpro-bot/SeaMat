import os
from pathlib import Path

import desktop


def test_desktop_data_directories_are_platform_specific(tmp_path):
    assert desktop.user_data_dir('Windows',{'LOCALAPPDATA':str(tmp_path)},tmp_path)==tmp_path/'SeaMat'
    assert desktop.user_data_dir('Darwin',{},tmp_path)==tmp_path/'Library'/'Application Support'/'SeaMat'
    assert desktop.user_data_dir('Linux',{'XDG_DATA_HOME':str(tmp_path/'xdg')},tmp_path)==tmp_path/'xdg'/'SeaMat'


def test_desktop_environment_keeps_mutable_files_outside_bundle(tmp_path,monkeypatch):
    previous=Path.cwd()
    for name in ('SEAMAT_DATA_DIR','SEAMAT_DB','SEAMAT_DOCUMENTS_DIR','SEAMAT_BACKUP_DIR'):
        monkeypatch.delenv(name,raising=False)
    try:
        root=desktop.configure_environment(tmp_path/'profile')
        assert root==tmp_path/'profile'
        assert Path(os.environ['SEAMAT_DB'])==root/'seamat.sqlite3'
        assert Path(os.environ['SEAMAT_DOCUMENTS_DIR'])==root/'documents'
        assert Path(os.environ['SEAMAT_BACKUP_DIR'])==root/'backups'/'daily'
    finally:
        os.chdir(previous)
