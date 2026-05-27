# -*- coding: utf-8 -*-
"""SUHO 工具中心 — 卡片式导航"""

import streamlit as st

from config import BRAND_NAME, BRAND_SLOGAN
from auth_mod import can_access, get_current_user, get_current_role, get_role_name

# 工具定义: (key, icon, name, desc)
TOOL_CARDS = [
    ("seo",            "  ", "SEO 标题生成",   "8 平台一键生成爆款标题"),
    ("roi",            "  ", "ROI 保本分析",   "上传利润表自动计算保本 ROI"),
    ("sales",          "  ", "销售数据分析",   "趋势/爆款/滞销/利润分析"),
    ("competitor",     "  ", "竞品监控",       "价格/销量/评价多维对比"),
    ("ads_dashboard",  "  ", "广告数据看板",   "投放数据汇总与 ROI 趋势"),
    ("product_report", "  ", "选品智能报告",   "市场分析与选品建议报告"),
]


def render():
    st.markdown(f"###   {BRAND_NAME} 工具中心")
    st.caption(f"{BRAND_SLOGAN} — 选择工具开始工作")

    st.divider()

    # 工具卡片网格
    cols = st.columns(3)
    shown = 0
    for key, icon, name, desc in TOOL_CARDS:
        if not can_access(key):
            continue
        with cols[shown % 3]:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.04);border:1px solid rgba(79,109,245,.15);
                        border-radius:12px;padding:1.5rem;margin-bottom:1rem;
                        min-height:140px;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">{icon}</div>
                <div style="font-size:1.1rem;font-weight:600;color:#e8e8e8;margin-bottom:0.3rem;">{name}</div>
                <div style="font-size:0.85rem;color:#999;margin-bottom:1rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("打开", key=f"open_{key}", use_container_width=True):
                st.session_state["active_tool"] = key
                st.rerun()
        shown += 1

    if shown == 0:
        st.info("暂无可访问的工具，请联系管理员开通权限。")

    st.divider()

    # 管理员额外入口
    if can_access("admin"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚙️ 企业管理", use_container_width=True):
                st.session_state["active_tool"] = "admin"
                st.rerun()
        with col2:
            if can_access("lexicon"):
                if st.button("  词库管理", use_container_width=True):
                    st.session_state["active_tool"] = "lexicon"
                    st.rerun()
