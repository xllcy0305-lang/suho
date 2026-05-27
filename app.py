#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUHO 速合 — 跨境电商 AI 运营平台"""

import sys
from pathlib import Path
_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import copy
import time

import streamlit as st

from config import LEXICON_PATH, BRAND_NAME, BRAND_SLOGAN, BRAND_VERSION
from db import init_db, update_online, reset_password, verify_user
from auth_mod import (
    is_logged_in, get_current_user, get_current_role,
    get_role_name, do_logout, can_access,
    get_accessible_platforms,
)
from lexicon_manager import BUILTIN_LEXICON as _BUILTIN, load_lexicon

import page_landing
import page_login
import page_hub
import page_seo
import page_roi
import page_keywords
import page_lexicon
import page_admin

# 新工具模块（即使文件不存在也不阻塞主程序）
_new_pages = {}
for _name in ("page_sales", "page_competitor", "page_ads_dashboard", "page_product_report"):
    try:
        _new_pages[_name] = __import__(_name)
    except ImportError:
        pass


# ── 页面配置 ──
st.set_page_config(
    page_title=f"{BRAND_NAME} — {BRAND_SLOGAN}",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──
st.markdown("""<style>
.stApp{background:linear-gradient(135deg,#0a0a1a 0%,#0f0f2e 30%,#1a1a3e 60%,#0d0d2b 100%);color:#e8e8e8}
section[data-testid="stSidebar"]{background:rgba(8,8,22,.98);border-right:1px solid rgba(100,120,255,.12)}
.stButton>button{background:linear-gradient(135deg,#4f6df5,#7c3aed);color:#fff;border:none;border-radius:10px;padding:.6rem 2rem;font-size:.95rem;font-weight:600;transition:all .3s;box-shadow:0 2px 12px rgba(79,109,245,.25)}
.stButton>button:hover{box-shadow:0 6px 20px rgba(79,109,245,.4);transform:translateY(-1px)}
div[data-testid="stDownloadButton"]>button{background:linear-gradient(135deg,#059669,#10b981)!important;border-radius:10px!important}
.title-card{background:rgba(255,255,255,.04);border-left:4px solid #4f6df5;padding:.7rem 1rem;margin:.4rem 0;border-radius:0 10px 10px 0;color:#d0d0d0;font-size:.95rem}
.title-card:hover{background:rgba(255,255,255,.08)}
.stTabs [data-baseweb="tab-list"]{gap:6px}
.stTabs [data-baseweb="tab"]{background:rgba(79,109,245,.08);border-radius:8px 8px 0 0;padding:.5rem 1.5rem;border:1px solid rgba(79,109,245,.12)}
.stTabs [aria-selected="true"]{background:rgba(79,109,245,.2)!important;border-bottom:2px solid #4f6df5!important}
[data-testid="stMetric"]{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:1rem}
footer{visibility:hidden}
</style>""", unsafe_allow_html=True)


# ── 侧边栏工具菜单 ──
_TOOL_MENU = [
    ("hub", "  工具中心"),
    ("seo", "  SEO 标题"),
    ("roi", "  ROI 分析"),
    ("sales", "  销售分析"),
    ("competitor", "  竞品监控"),
    ("ads_dashboard", "  广告看板"),
    ("product_report", "  选品报告"),
    ("keywords", "  热词同步"),
    ("lexicon", "  词库管理"),
    ("admin", "⚙️ 企业管理"),
]


# ── 缓存词库 ──
@st.cache_data(ttl=120, show_spinner=False)
def _cached_lexicon():
    return copy.deepcopy(load_lexicon(LEXICON_PATH))


def _render_sidebar():
    """渲染侧边栏导航和用户信息"""
    with st.sidebar:
        st.markdown(f"##  {BRAND_NAME}")
        st.caption(f"{BRAND_SLOGAN} {BRAND_VERSION}")
        st.divider()
        st.markdown(f"**{st.session_state.get('display_name', '')}**")
        st.caption(f"{get_role_name(get_current_role())} | {get_current_user()}")
        st.divider()

        # 工具导航菜单
        active_tool = st.session_state.get("active_tool", "hub")
        for key, label in _TOOL_MENU:
            if key == "hub" or can_access(key):
                is_active = "▶ " if active_tool == key else "　"
                if st.button(f"{is_active}{label}", key=f"nav_{key}",
                             use_container_width=True,
                             type="primary" if active_tool == key else "secondary"):
                    st.session_state["active_tool"] = key
                    st.rerun()

        # 修改密码
        if can_access("admin"):
            st.divider()
            with st.expander("  修改密码"):
                with st.form("change_pwd_form"):
                    old_pwd = st.text_input("当前密码", type="password")
                    new_pwd = st.text_input("新密码", type="password")
                    confirm_pwd = st.text_input("确认新密码", type="password")
                    if st.form_submit_button("确认修改"):
                        if not old_pwd or not new_pwd:
                            st.warning("请填写所有字段")
                        elif new_pwd != confirm_pwd:
                            st.error("两次输入的新密码不一致")
                        elif len(new_pwd) < 4:
                            st.error("密码至少 4 位")
                        elif not verify_user(get_current_user(), old_pwd):
                            st.error("当前密码错误")
                        else:
                            reset_password(get_current_user(), new_pwd)
                            st.success("密码修改成功！")

        st.divider()
        if st.button("  退出登录", use_container_width=True):
            do_logout()
            st.rerun()


def _render_tool(tool_key: str, lex: dict):
    """渲染当前选中的工具页面"""
    # 返回按钮
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("← 返回中心"):
            st.session_state["active_tool"] = "hub"
            st.rerun()

    # SEO 需要类目/平台选择器
    if tool_key in ("seo", "keywords"):
        cats = {}
        for k, v in lex.get("categories", {}).items():
            if not k.startswith("_"):
                cats[v.get("display_name", k)] = k
        if not cats:
            cats = {d["display_name"]: k for k, d in _BUILTIN["categories"].items()}

        plats = {}
        accessible = get_accessible_platforms()
        for k, v in lex.get("platform_limits", {}).items():
            if k in accessible:
                plats[f"{v.get('name_cn', k)}（≤{v.get('max_chars', 120)}字符）"] = k
        if not plats:
            plats = {"Shopee泰国站（≤120字符）": "shopee_th"}

        c1, c2 = st.columns(2)
        sel_cat_name = c1.selectbox("运营类目", list(cats.keys()), key="sb_cat")
        sel_cat_key = cats[sel_cat_name]
        sel_plat_label = c2.selectbox("目标平台", list(plats.keys()), key="sb_plat")
        sel_plat_key = plats[sel_plat_label]

    # 工具分发
    if tool_key == "seo":
        cat_data = lex.get("categories", {}).get(sel_cat_key, {})
        page_seo.render(cat_data, sel_cat_name, sel_plat_key, sel_plat_label, lex)
    elif tool_key == "roi":
        page_roi.render()
    elif tool_key == "keywords":
        page_keywords.render(sel_cat_name, sel_cat_key)
    elif tool_key == "lexicon":
        page_lexicon.render(lex)
    elif tool_key == "admin":
        page_admin.render()
    elif tool_key == "sales" and "page_sales" in _new_pages:
        _new_pages["page_sales"].render()
    elif tool_key == "competitor" and "page_competitor" in _new_pages:
        _new_pages["page_competitor"].render()
    elif tool_key == "ads_dashboard" and "page_ads_dashboard" in _new_pages:
        _new_pages["page_ads_dashboard"].render()
    elif tool_key == "product_report" and "page_product_report" in _new_pages:
        _new_pages["page_product_report"].render()
    else:
        st.info("该工具正在开发中，敬请期待！")


def main():
    # 初始化数据库
    if not st.session_state.get("_db_ready"):
        init_db()
        st.session_state["_db_ready"] = True

    # ── 未登录 ──
    if not is_logged_in():
        if st.session_state.get("show_login"):
            _, col, _ = st.columns([1, 1.2, 1])
            with col:
                st.markdown(f"##  {BRAND_NAME}")
                st.caption(BRAND_SLOGAN)
            page_login.render()
            if st.button("← 返回首页"):
                st.session_state["show_login"] = False
                st.rerun()
        else:
            page_landing.render()
        return

    # ── 在线心跳 ──
    now = time.time()
    if now - st.session_state.get("_hb", 0) > 60:
        update_online(get_current_user())
        st.session_state["_hb"] = now

    # ── 侧边栏 ──
    _render_sidebar()

    # ── 主区域 ──
    active_tool = st.session_state.get("active_tool", "hub")
    lex = _cached_lexicon()

    if active_tool == "hub":
        page_hub.render()
    else:
        _render_tool(active_tool, lex)

    st.divider()
    st.caption(f"{BRAND_NAME} {BRAND_SLOGAN} {BRAND_VERSION} | © 2026")


if __name__ == "__main__":
    main()
