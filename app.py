#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NORVIK SHOP AI OS v3.0 — 企业级跨境电商 AI 运营工具平台"""

import sys
from pathlib import Path
# 确保项目根目录在 sys.path 中（Streamlit Cloud 必须）
_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import copy
import time

import streamlit as st

from config import LEXICON_PATH
from db import init_db, update_online, reset_password, verify_user
from auth_mod import (
    is_logged_in, get_current_user, get_current_role,
    get_role_name, do_logout, has_permission,
)
from lexicon_manager import BUILTIN_LEXICON as _BUILTIN, load_lexicon

import page_login
import page_seo
import page_roi
import page_keywords
import page_lexicon
import page_admin


# ── 页面配置 ──
st.set_page_config(
    page_title="NORVIK SHOP — AI 运营系统",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS（无外部字体依赖） ──
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


# ── 缓存词库（返回深拷贝防止缓存污染） ──
@st.cache_data(ttl=120, show_spinner=False)
def _cached_lexicon():
    return copy.deepcopy(load_lexicon(LEXICON_PATH))


def main():
    # 初始化数据库（幂等，仅首次）
    if not st.session_state.get("_db_ready"):
        init_db()
        st.session_state["_db_ready"] = True

    # ── 未登录 ──
    if not is_logged_in():
        _, col, _ = st.columns([1, 1.2, 1])
        with col:
            st.markdown("##  NORVIK SHOP")
            st.markdown("### AI OPERATING SYSTEM")
            st.caption("企业级跨境电商 AI 运营工具平台")
        page_login.render()
        return

    # ── 节流在线状态更新（每 60 秒一次） ──
    now = time.time()
    last_heartbeat = st.session_state.get("_hb", 0)
    if now - last_heartbeat > 60:
        update_online(get_current_user())
        st.session_state["_hb"] = now

    # ── 加载词库 ──
    lex = _cached_lexicon()

    cats = {}
    for k, v in lex.get("categories", {}).items():
        if not k.startswith("_"):
            cats[v.get("display_name", k)] = k
    if not cats:
        cats = {d["display_name"]: k for k, d in _BUILTIN["categories"].items()}
        lex["categories"] = _BUILTIN["categories"]

    plats = {}
    for k, v in lex.get("platform_limits", {}).items():
        plats[f"{v.get('name_cn', k)}（≤{v.get('max_chars', 120)}字符）"] = k
    if not plats:
        plats = {"Shopee泰国站（≤120字符）": "shopee_th"}
        lex["platform_limits"] = _BUILTIN["platform_limits"]

    # ── 侧边栏 ──
    with st.sidebar:
        st.markdown("##  NORVIK SHOP")
        st.caption("AI OPERATING SYSTEM v3.0")
        st.divider()
        st.markdown(f"**{st.session_state.get('display_name', '')}**")
        st.caption(f"{get_role_name(get_current_role())} | {get_current_user()}")
        st.divider()
        st.markdown("###  生成参数")
        sel_cat_name = st.selectbox("运营类目", list(cats.keys()), key="sb_cat")
        sel_cat_key = cats[sel_cat_name]
        sel_plat_label = st.selectbox("目标平台", list(plats.keys()), key="sb_plat")
        sel_plat_key = plats[sel_plat_label]
        st.divider()
        st.markdown(f"词库更新: {lex.get('_meta', {}).get('last_updated', '—')}")
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
                        st.success("密码修改成功！下次登录请用新密码")
        st.divider()
        if st.button("  退出登录", use_container_width=True):
            do_logout()
            st.rerun()

    # ── 主区域 ──
    st.markdown("#  NORVIK SHOP")
    st.markdown("#### 企业级跨境电商 AI 运营工具平台")
    st.caption("选品类 → 输产品词 → 点按钮 → 下载 Excel")

    tabs = ["  生成标题", "  ROI 分析", "  热词同步", "  词库管理"]
    if has_permission("admin"):
        tabs.append("⚙️ 企业管理")

    tab_objs = st.tabs(tabs)
    cat_data = lex.get("categories", {}).get(sel_cat_key, {})

    with tab_objs[0]:
        page_seo.render(cat_data, sel_cat_name, sel_plat_key, sel_plat_label, lex)
    with tab_objs[1]:
        page_roi.render()
    with tab_objs[2]:
        page_keywords.render(sel_cat_name, sel_cat_key)
    with tab_objs[3]:
        page_lexicon.render(lex)
    if has_permission("admin") and len(tab_objs) > 4:
        with tab_objs[4]:
            page_admin.render()

    st.divider()
    st.caption("NORVIK SHOP AI OS v3.0 | © 2026")


if __name__ == "__main__":
    main()
