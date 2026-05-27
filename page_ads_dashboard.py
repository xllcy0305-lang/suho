# -*- coding: utf-8 -*-
"""广告数据看板页面"""

import streamlit as st
import pandas as pd

from config import BRAND_NAME
from auth_mod import can_access


def render():
    st.markdown(f"###   广告数据看板")
    st.caption(f"{BRAND_NAME} — 上传广告投放数据，查看 ROI 趋势与优化建议")

    uploaded = st.file_uploader(
        "上传广告投放数据 Excel 文件",
        type=["xlsx", "xls", "csv"],
        key="ads_upload",
    )

    if not uploaded:
        with st.expander("  支持的数据格式"):
            st.markdown("""
            Excel 或 CSV 文件，列名支持自动识别：

            | 列名示例 | 说明 |
            |---------|------|
            | 日期 / date | 投放日期 |
            | 广告组 / campaign | 广告计划名称 |
            | 关键词 / keyword | 投放关键词 |
            | 展现 / impressions | 广告展示次数 |
            | 点击 / clicks | 点击次数 |
            | 花费 / cost | 广告花费 |
            | 订单 / orders | 成交订单数 |
            | 销售额 / sales | 广告带来的销售额 |

            支持 Shopee / Lazada / TikTok 等平台的广告报表。
            """)
        return

    try:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"文件读取失败: {e}")
        return

    if len(df) == 0:
        st.warning("文件为空")
        return

    st.success(f"成功读取 {len(df)} 条广告数据")

    with st.expander("  预览数据", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

    with st.spinner("正在分析广告数据…"):
        from ads_dashboard_engine import analyze, to_excel
        result = analyze(df.copy())

    # 核心指标
    if "summary" in result:
        st.markdown("####   核心指标")
        metrics = result["summary"]
        cols = st.columns(min(len(metrics), 4))
        for i, (k, v) in enumerate(metrics.items()):
            cols[i % 4].metric(k, v)

    # ROI 趋势
    if "roi_trend" in result:
        st.markdown("####   ROI 趋势")
        trend = result["roi_trend"].set_index("日期")
        col1, col2 = st.columns(2)
        with col1:
            st.line_chart(trend[["花费", "销售额"]])
        with col2:
            st.line_chart(trend[["ROI"]])

    # 广告组排行
    if "camp_top_roi" in result or "camp_low_roi" in result:
        st.markdown("####   广告组分析")
        tab1, tab2, tab3 = st.tabs(["  高效广告组", "⚠️ 低效广告组", "  全部广告组"])
        with tab1:
            if "camp_top_roi" in result:
                st.dataframe(result["camp_top_roi"], use_container_width=True)
        with tab2:
            if "camp_low_roi" in result:
                st.dataframe(result["camp_low_roi"], use_container_width=True)
        with tab3:
            if "camp_all" in result:
                st.dataframe(result["camp_all"], use_container_width=True)

    # 关键词效果
    if "kw_effect" in result:
        st.markdown("####   关键词效果")
        st.dataframe(result["kw_effect"], use_container_width=True)

    # 预算建议
    if "suggestions" in result:
        st.markdown("####   预算优化建议")
        sug = result["suggestions"]
        for _, row in sug.iterrows():
            emoji = " " if row["建议"] == "加大预算" else " " if "暂停" in row["建议"] else "⚡"
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.04);border-left:4px solid
                {'#10b981' if '加大' in row['建议'] else '#ef4444' if '暂停' in row['建议'] else '#f59e0b'};
                padding:.8rem 1rem;margin:.4rem 0;border-radius:0 8px 8px 0;">
                <b>{emoji} {row['广告组']}</b> — {row['建议']}
                <br><span style="color:#999;font-size:.85rem">{row['理由']}</span>
            </div>
            """, unsafe_allow_html=True)

    # 下载
    if can_access("export"):
        st.divider()
        buf = to_excel(result)
        st.download_button(
            "  下载广告看板报告",
            data=buf,
            file_name="广告看板报告.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
