# -*- coding: utf-8 -*-
"""NORVIK SHOP AI OS — 全局配置"""

import os
from pathlib import Path

# ── 路径 ──
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "norvik_shop.db"
LOG_DIR = DATA_DIR / "logs"
LEXICON_PATH = DATA_DIR / "thai_keywords_lexicon.json"
BACKUP_DIR = DATA_DIR / "lexicon_backups"

# 兼容旧位置
if not LEXICON_PATH.exists() and (BASE_DIR / "thai_keywords_lexicon.json").exists():
    LEXICON_PATH = BASE_DIR / "thai_keywords_lexicon.json"

# 确保目录存在
for d in [DATA_DIR, LOG_DIR, BACKUP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── 安全 ──
SECRET_SALT = os.environ.get("NORVIK_SECRET", "NORVIK2026xThaiShop")
SESSION_TIMEOUT_MIN = int(os.environ.get("SESSION_TIMEOUT", "120"))
MAX_LOGIN_ATTEMPTS = 5

# ── 生成 ──
TARGET_TITLE_COUNT = 50
MAX_SAMPLE_COMBOS = 2000

# ── 平台 ──
PLATFORM_LIMITS = {
    "shopee_th":     {"max_chars": 120, "name_cn": "Shopee泰国站", "flag": " "},
    "lazada_th":     {"max_chars": 130, "name_cn": "Lazada泰国站", "flag": " "},
    "tiktok_global": {"max_chars": 100, "name_cn": "TikTok海外",   "flag": " "},
    "temu":          {"max_chars": 150, "name_cn": "Temu",          "flag": " "},
    "amazon":        {"max_chars": 200, "name_cn": "Amazon",        "flag": " "},
    "taobao":        {"max_chars": 60,  "name_cn": "淘宝",          "flag": " "},
    "pinduoduo":     {"max_chars": 120, "name_cn": "拼多多",        "flag": " "},
    "douyin":        {"max_chars": 55,  "name_cn": "抖音",          "flag": " "},
}

THAI_PLATFORMS = {"shopee_th", "lazada_th", "tiktok_global", "temu", "amazon"}
CN_PLATFORMS = {"taobao", "pinduoduo", "douyin"}

# ── 中文爆款词 ──
CN_QUALITIES = [
    "高品质", "热销爆款", "户外专用", "便携轻量", "大容量",
    "加厚加固", "新款上市", "厂家直销", "特价优惠", "限量版",
]
CN_FEATURES = [
    "快速折叠", "一秒收纳", "防水防潮", "抗风稳固", "人体工学设计",
    "多档调节", "承重300斤", "免安装", "静音防滑", "透气舒适",
]

# ── 角色 ──
ROLES = {
    "super_admin": "超级管理员",
    "admin": "管理员",
    "supervisor": "主管",
    "operator": "运营",
}

# ── 默认管理员 ──
DEFAULT_ADMIN = {
    "username": "admin",
    "password": os.environ.get("ADMIN_PASSWORD", "NORVIK2026"),
    "role": "super_admin",
    "display_name": "系统管理员",
}
