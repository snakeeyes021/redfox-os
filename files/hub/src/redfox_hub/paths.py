"""Where Hub's own files are, installed or run from the source tree.

meson writes build_config.py with the install prefix's data folder. Run
from the source tree (tests, a quick try), the data folder is
files/hub/data next to the code.
"""

import os
from pathlib import Path

try:
    from .build_config import PKGDATADIR, VERSION
except ImportError:
    PKGDATADIR = str(Path(__file__).resolve().parents[2] / "data")
    VERSION = "0.1.0-dev"

DATA = Path(os.environ.get("REDFOX_HUB_DATA", PKGDATADIR))
STYLE = DATA / "style.css"
LAYOUTS = DATA / "layouts"
MANUAL = Path(os.environ.get("REDFOX_MANUAL_DIR", DATA / "manual"))


def host_state_dir():
    """~/.local/state/redfox, shared with the first-login script."""
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    return Path(base) / "redfox"
