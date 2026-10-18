"""Native desktop entry point used by the Windows and macOS packages."""
from __future__ import annotations

import os
import platform
from multiprocessing import freeze_support
from pathlib import Path


def user_data_dir(system: str | None = None, environ: dict[str,str] | None = None,
                  home: Path | None = None) -> Path:
    """Return a persistent, user-writable SeaMat data folder."""
    system=system or platform.system()
    environ=environ if environ is not None else os.environ
    home=home or Path.home()
    if system=='Windows':
        base=Path(environ.get('LOCALAPPDATA') or environ.get('APPDATA') or home/'AppData'/'Local')
        return base/'SeaMat'
    if system=='Darwin':
        return home/'Library'/'Application Support'/'SeaMat'
    return Path(environ.get('XDG_DATA_HOME') or home/'.local'/'share')/'SeaMat'


def configure_environment(data_dir: Path | None = None) -> Path:
    """Route every mutable file outside the application bundle."""
    root=Path(data_dir or os.environ.get('SEAMAT_DATA_DIR') or user_data_dir()).expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault('SEAMAT_DATA_DIR',str(root))
    os.environ.setdefault('SEAMAT_DB',str(root/'seamat.sqlite3'))
    os.environ.setdefault('SEAMAT_DOCUMENTS_DIR',str(root/'documents'))
    os.environ.setdefault('SEAMAT_BACKUP_DIR',str(root/'backups'/'daily'))
    os.environ.setdefault('SEAMAT_HOST','127.0.0.1')
    os.environ.setdefault('SEAMAT_SHOW_BROWSER','0')
    os.chdir(root)
    return root


if __name__=='__main__':
    freeze_support()
    configure_environment()
    from main import run_application
    native_mode=os.environ.get('SEAMAT_DESKTOP_NATIVE','1').lower() not in {'0','false','no'}
    run_application(native_mode=native_mode)
