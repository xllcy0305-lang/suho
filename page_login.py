# -*- coding: utf-8 -*-
"""登录页面 — 激活码验证 + 用户名密码登录"""

import hashlib
from datetime import datetime, timedelta

import streamlit as st
from auth_mod import do_login, is_logged_in
from config import BRAND_NAME


def _check_code(user_input: str) -> bool:
    """本地验证激活码（SHA256 时间算法，不依赖数据库）"""
    user_input = user_input.strip().upper()
    for offset in [0, -1, 1]:
        now = datetime.now() + timedelta(weeks=offset)
        y, w, _ = now.isocalendar()
        raw = f"{y}-W{w:02d}-NORVIKSHOP"
        expected = hashlib.sha256(raw.encode()).hexdigest()[:12].upper()
        if user_input == expected:
            return True
    return False


def render():
    if is_logged_in():
        return

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown(f"###   登录 {BRAND_NAME}")
        st.caption("跨境电商 AI 运营平台 — 请登录以继续")

        # ── 第一步：激活码验证 ──
        if not st.session_state.get("code_verified"):
            st.markdown("#####  请输入激活码")
            code = st.text_input(
                "激活码", placeholder="请输入 12 位激活码",
                max_chars=12, key="act_code_input",
            )

            if st.button("  验证激活码", use_container_width=True):
                if not code:
                    st.warning("请输入激活码")
                elif _check_code(code):
                    st.session_state["code_verified"] = True
                    st.success("激活码验证通过！")
                    st.rerun()
                else:
                    st.error("激活码无效或已过期，请联系管理员获取本周激活码")
            return

        # ── 第二步：用户登录 ──
        with st.form("login_form"):
            username = st.text_input("账号", placeholder="请输入用户名")
            password = st.text_input(
                "密码", type="password", placeholder="请输入密码",
            )
            submitted = st.form_submit_button(
                "  登录", use_container_width=True,
            )

            if submitted:
                if not username or not password:
                    st.warning("请输入账号和密码")
                elif do_login(username, password):
                    st.success("登录成功，正在跳转…")
                    st.rerun()
                else:
                    st.error("账号或密码错误，或账号已被锁定")
