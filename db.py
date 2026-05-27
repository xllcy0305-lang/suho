# -*- coding: utf-8 -*-
"""数据库层 — SQLite 持久化"""

import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

from config import DB_PATH, SECRET_SALT, DEFAULT_ADMIN, ALL_FEATURE_KEYS

logger = logging.getLogger(__name__)


@contextmanager
def get_conn():
    """安全数据库连接上下文管理器"""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化所有表（幂等，不使用 executescript 避免长锁）"""
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'operator',
            display_name TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            login_attempts INTEGER DEFAULT 0,
            locked_until TEXT DEFAULT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            last_login TEXT DEFAULT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            week_label TEXT NOT NULL,
            max_uses INTEGER DEFAULT 999,
            used_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_by TEXT DEFAULT 'system',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            expires_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS lexicon_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_by TEXT DEFAULT 'system',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS online_users (
            username TEXT PRIMARY KEY,
            last_active TEXT DEFAULT (datetime('now','localtime')),
            page TEXT DEFAULT 'main'
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON operation_logs(username)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_time ON operation_logs(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_codes_week ON activation_codes(week_label)")
        conn.execute("""CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            feature_key TEXT NOT NULL,
            granted INTEGER NOT NULL DEFAULT 1,
            updated_by TEXT DEFAULT 'system',
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(username, feature_key)
        )""")

        admin = conn.execute(
            "SELECT id FROM users WHERE username=?", (DEFAULT_ADMIN["username"],)
        ).fetchone()
        if not admin:
            pw_hash = hash_password(DEFAULT_ADMIN["password"])
            conn.execute(
                "INSERT INTO users (username,password_hash,role,display_name) VALUES (?,?,?,?)",
                (DEFAULT_ADMIN["username"], pw_hash, DEFAULT_ADMIN["role"], DEFAULT_ADMIN["display_name"]),
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 用户操作
# ═══════════════════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256(f"{password}{SECRET_SALT}".encode()).hexdigest()


def verify_user(username: str, password: str) -> dict | None:
    """验证用户登录，返回用户信息或 None"""
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user:
            return None

        # 检查锁定
        if user["locked_until"]:
            locked_until = datetime.strptime(user["locked_until"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < locked_until:
                return None
            else:
                conn.execute(
                    "UPDATE users SET locked_until = NULL, login_attempts = 0 WHERE username = ?",
                    (username,),
                )

        if not user["is_active"]:
            return None

        pw_hash = hash_password(password)
        if pw_hash != user["password_hash"]:
            attempts = user["login_attempts"] + 1
            locked = None
            if attempts >= 5:
                locked = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "UPDATE users SET login_attempts = ?, locked_until = ? WHERE username = ?",
                (attempts, locked, username),
            )
            return None

        # 登录成功
        conn.execute(
            "UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = datetime('now','localtime') WHERE username = ?",
            (username,),
        )
        return dict(user)


def create_user(username: str, password: str, role: str, display_name: str = "") -> tuple[bool, str]:
    with get_conn() as conn:
        exists = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            return False, "用户名已存在"
        conn.execute(
            "INSERT INTO users (username, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), role, display_name),
        )
    return True, "创建成功"


def get_all_users() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, role, display_name, is_active, last_login, created_at FROM users ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def update_user_status(username: str, is_active: int) -> bool:
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_active = ? WHERE username = ?", (is_active, username))
    return True


def reset_password(username: str, new_password: str) -> bool:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (hash_password(new_password), username),
        )
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 激活码
# ═══════════════════════════════════════════════════════════════════════════════

def generate_activation_code(week_offset: int = 0, created_by: str = "system") -> dict:
    """生成指定周的激活码"""
    now = datetime.now() + timedelta(weeks=week_offset)
    y, w, _ = now.isocalendar()
    week_label = f"{y}-W{w:02d}"
    raw = f"{week_label}-NORVIKSHOP"
    code = hashlib.sha256(raw.encode()).hexdigest()[:12].upper()
    expires = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    with get_conn() as conn:
        exists = conn.execute("SELECT id FROM activation_codes WHERE code = ?", (code,)).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO activation_codes (code, week_label, max_uses, expires_at, created_by) VALUES (?, ?, 999, ?, ?)",
                (code, week_label, expires, created_by),
            )
    return {"code": code, "week": week_label, "expires": expires}


def verify_activation_code(code: str) -> bool:
    """验证激活码（允许当前周、上周、下周）"""
    code = code.strip().upper()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM activation_codes WHERE code = ? AND is_active = 1", (code,)
        ).fetchone()
        if not row:
            # 自动尝试生成并匹配
            for offset in [0, -1, 1]:
                now = datetime.now() + timedelta(weeks=offset)
                y, w, _ = now.isocalendar()
                week_label = f"{y}-W{w:02d}"
                raw = f"{week_label}-NORVIKSHOP"
                auto_code = hashlib.sha256(raw.encode()).hexdigest()[:12].upper()
                if code == auto_code:
                    return True
            return False
        # 检查过期
        expires = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expires:
            return False
        # 检查次数
        if row["used_count"] >= row["max_uses"]:
            return False
        conn.execute("UPDATE activation_codes SET used_count = used_count + 1 WHERE id = ?", (row["id"],))
    return True


def get_all_codes() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM activation_codes ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def revoke_code(code_id: int) -> bool:
    with get_conn() as conn:
        conn.execute("UPDATE activation_codes SET is_active = 0 WHERE id = ?", (code_id,))
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 操作日志
# ═══════════════════════════════════════════════════════════════════════════════

def log_action(username: str, action: str, detail: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO operation_logs (username, action, detail) VALUES (?, ?, ?)",
            (username, action, detail),
        )


def get_logs(limit: int = 200, username: str = None) -> list[dict]:
    with get_conn() as conn:
        if username:
            rows = conn.execute(
                "SELECT * FROM operation_logs WHERE username = ? ORDER BY id DESC LIMIT ?",
                (username, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# 在线用户
# ═══════════════════════════════════════════════════════════════════════════════

def update_online(username: str, page: str = "main"):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO online_users (username, last_active, page) VALUES (?, datetime('now','localtime'), ?)",
            (username, page),
        )


def get_online_users(timeout_min: int = 5) -> list[dict]:
    cutoff = (datetime.now() - timedelta(minutes=timeout_min)).strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute("DELETE FROM online_users WHERE last_active < ?", (cutoff,))
        rows = conn.execute("SELECT * FROM online_users ORDER BY last_active DESC").fetchall()
    return [dict(r) for r in rows]


def remove_online(username: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM online_users WHERE username = ?", (username,))


# ═══════════════════════════════════════════════════════════════════════════════
# 用户权限
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_permissions(username: str) -> dict[str, bool]:
    """获取用户的 DB 权限覆盖项 {feature_key: granted}"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT feature_key, granted FROM user_permissions WHERE username = ?",
            (username,),
        ).fetchall()
    return {r["feature_key"]: bool(r["granted"]) for r in rows}


def set_user_permissions(username: str, permissions: dict[str, bool],
                         updated_by: str = "admin") -> bool:
    """批量设置用户权限（upsert）"""
    with get_conn() as conn:
        for key, granted in permissions.items():
            if key not in ALL_FEATURE_KEYS:
                continue
            conn.execute(
                """INSERT INTO user_permissions (username, feature_key, granted, updated_by)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(username, feature_key) DO UPDATE SET
                   granted=excluded.granted, updated_by=excluded.updated_by,
                   updated_at=datetime('now','localtime')""",
                (username, key, int(granted), updated_by),
            )
    return True


def delete_user_permissions(username: str) -> bool:
    """删除用户所有权限覆盖（恢复角色默认）"""
    with get_conn() as conn:
        conn.execute("DELETE FROM user_permissions WHERE username = ?", (username,))
    return True
