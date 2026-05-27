# -*- coding: utf-8 -*-
"""认证与会话管理 — RBAC 权限控制"""

import streamlit as st

from db import verify_user, log_action, update_online, remove_online, get_user_permissions
from config import ROLES, ALL_FEATURE_KEYS

# ── 各角色默认权限 ──
_ALL_TRUE = {k: True for k in ALL_FEATURE_KEYS}

ROLE_DEFAULTS = {
    "super_admin": dict(_ALL_TRUE),
    "admin": dict(_ALL_TRUE),
    "supervisor": {
        "seo": True, "roi": True, "export": True, "keywords": True,
        "lexicon": False, "admin": False,
        "sales": True, "competitor": True, "ads_dashboard": True, "product_report": True,
        "platform_shopee": True, "platform_lazada": True,
        "platform_tiktok": True, "platform_temu": True,
        "platform_amazon": True, "platform_taobao": True,
        "platform_pdd": True, "platform_douyin": True,
    },
    "operator": {
        "seo": True, "roi": True, "export": True, "keywords": False,
        "lexicon": False, "admin": False,
        "sales": True, "competitor": True, "ads_dashboard": False, "product_report": False,
        "platform_shopee": True, "platform_lazada": True,
        "platform_tiktok": True, "platform_temu": True,
        "platform_amazon": True, "platform_taobao": True,
        "platform_pdd": True, "platform_douyin": True,
    },
}

PLATFORM_KEYS = [k for k in ALL_FEATURE_KEYS if k.startswith("platform_")]


def do_login(username: str, password: str) -> bool:
    user = verify_user(username, password)
    if not user:
        return False
    st.session_state["logged_in"] = True
    st.session_state["username"] = user["username"]
    st.session_state["role"] = user["role"]
    st.session_state["display_name"] = user.get("display_name", username)
    log_action(username, "登录", "登录成功")
    update_online(username)
    return True


def do_logout():
    username = st.session_state.get("username", "unknown")
    try:
        remove_online(username)
        log_action(username, "退出", "用户退出登录")
    except Exception:
        pass
    for key in ("logged_in", "username", "role", "display_name", "login_time", "code_verified"):
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in"))


def get_current_user() -> str:
    return st.session_state.get("username", "")


def get_current_role() -> str:
    return st.session_state.get("role", "operator")


def get_role_name(role: str) -> str:
    return ROLES.get(role, role)


def has_permission(min_role: str) -> bool:
    role_order = {"operator": 0, "supervisor": 1, "admin": 2, "super_admin": 3}
    current = role_order.get(get_current_role(), 0)
    required = role_order.get(min_role, 0)
    return current >= required


def get_user_all_permissions(username: str, role: str) -> dict[str, bool]:
    """合并角色默认 + DB 覆盖的最终权限表"""
    defaults = ROLE_DEFAULTS.get(role, ROLE_DEFAULTS["operator"])
    merged = dict(defaults)
    overrides = get_user_permissions(username)
    merged.update(overrides)
    return merged


def can_access(feature_key: str) -> bool:
    """检查当前用户是否有权限访问某功能"""
    role = get_current_role()
    username = get_current_user()

    # super_admin 永远有权限
    if role == "super_admin":
        return True

    perms = get_user_all_permissions(username, role)
    return perms.get(feature_key, False)


def get_accessible_platforms() -> list[str]:
    """返回当前用户可访问的平台 key 列表（如 shopee_th, temu 等）"""
    # feature_key → platform_key 映射
    _FEAT_TO_PLAT = {
        "platform_shopee": "shopee_th", "platform_lazada": "lazada_th",
        "platform_tiktok": "tiktok_global", "platform_temu": "temu",
        "platform_amazon": "amazon", "platform_taobao": "taobao",
        "platform_pdd": "pinduoduo", "platform_douyin": "douyin",
    }

    role = get_current_role()
    if role == "super_admin":
        return list(_FEAT_TO_PLAT.values())

    username = get_current_user()
    perms = get_user_all_permissions(username, role)
    return [_FEAT_TO_PLAT[k] for k in PLATFORM_KEYS if perms.get(k, False)]
