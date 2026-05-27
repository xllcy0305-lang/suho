# -*- coding: utf-8 -*-
"""认证与会话管理"""

import streamlit as st

from db import verify_user, log_action, update_online, remove_online
from config import ROLES


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
