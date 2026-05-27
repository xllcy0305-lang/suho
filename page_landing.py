# -*- coding: utf-8 -*-
"""SUHO 品牌落地页"""

import streamlit as st

from config import BRAND_NAME, BRAND_NAME_CN, BRAND_SLOGAN, BRAND_VERSION


def render():
    # Hero 区
    st.markdown(f"""
    <div style="text-align:center;padding:3rem 1rem 1rem;">
        <h1 style="font-size:3.5rem;margin-bottom:0.3rem;
                   background:linear-gradient(135deg,#4f6df5,#7c3aed,#a855f7);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            {BRAND_NAME}
        </h1>
        <h2 style="color:#a5b4fc;font-size:1.5rem;margin-top:0;font-weight:400;">
            {BRAND_NAME_CN} — {BRAND_SLOGAN}
        </h2>
        <p style="color:#888;font-size:0.95rem;margin-top:0.5rem;">
            {BRAND_VERSION} | 为跨境电商团队打造的一站式 AI 运营工具
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 功能卡片区
    st.markdown("###   核心功能")

    tools = [
        ("  ", "SEO 标题生成", "8 大平台一键生成爆款标题，支持 Shopee / Lazada / TikTok / TEMU / Amazon / 淘宝 / 拼多多 / 抖音", "seo"),
        ("  ", "ROI 保本分析", "上传利润表自动计算单品保本 ROI 和全店通投保本 ROI，风险款自动标红", "roi"),
        ("  ", "销售数据分析", "上传销售数据 Excel，自动分析销售趋势、爆款排行、滞销预警、利润分布", "sales"),
        ("  ", "竞品监控", "上传竞品数据，价格/销量/评价多维对比，变化趋势一目了然", "competitor"),
        ("  ", "广告数据看板", "广告投放数据汇总，ROI 趋势图、关键词效果分析、预算优化建议", "ads_dashboard"),
        ("  ", "选品智能报告", "市场容量、竞争度、机会评分，自动生成选品建议报告", "product_report"),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc, _) in enumerate(tools):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.04);border:1px solid rgba(79,109,245,.15);
                        border-radius:12px;padding:1.2rem;margin-bottom:1rem;
                        min-height:160px;transition:all .3s;">
                <div style="font-size:1.8rem;margin-bottom:0.5rem;">{icon}</div>
                <div style="font-size:1.05rem;font-weight:600;color:#e8e8e8;margin-bottom:0.4rem;">{title}</div>
                <div style="font-size:0.85rem;color:#999;line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # 团队协作信息
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **  多角色权限管理**
        - 超级管理员 / 管理员 / 主管 / 运营
        - 按功能和平台精细控制访问权限
        - 操作日志全程记录
        """)
    with col2:
        st.markdown("""
        **  数据安全**
        - 密码加密存储，登录失败锁定
        - 激活码验证机制
        - 用户数据隔离
        """)

    st.divider()

    # CTA 按钮
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        if st.button("  登录系统", use_container_width=True, type="primary"):
            st.session_state["show_login"] = True
            st.rerun()

    st.caption("如需账号请联系管理员 | SUHO 速合 © 2026")
