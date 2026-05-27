# -*- coding: utf-8 -*-
"""utils 包 — 自动将父目录加入 sys.path"""
import sys
from pathlib import Path
_parent = str(Path(__file__).resolve().parent.parent)
if _parent not in sys.path:
    sys.path.insert(0, _parent)
