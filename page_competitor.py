# -*- coding: utf-8 -*-
"""竞品监控页面"""

import streamlit as st
import pandas as pd

from config import BRAND_NAME
from auth_mod import can_access


def render():
    st.markdown(f"###   竞品监控")
    st.caption(f"{BRAND_NAME} — 上传竞品数据，价格/销量/评价多维对比")

    uploaded = st.file_uploader(
        "上传竞品数据 Excel 文件",
        type=["xlsx", "xls", "csv"],
        key="comp_upload",
    )

    if not uploaded:
        with st.expander("  支持的数据格式"):
            st.markdown("""
            Excel 或 CSV 文件，列名支持自动识别：

            | 列名示例 | 说明 |
            |---------|------|
            | SKU / 商品编码 | 商品标识 |
            | 商品名称 / name | 商品标题 |
            | 价格 / price | 当前售价 |
            | 月销量 / sales | 月销量 |
            | 评分 / rating | 评价分 |
            | 评价数 / reviews | 评价总数 |
            | 店铺 / shop | 店铺名称 |
            | 类型 / type | "自有" 或留空表示竞品 |

            建议将自有商品的"类型"列标为"自有"，以便对比。
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

    st.success(f"成功读取 {len(df)} 条竞品数据")

    with st.expander("  预览数据", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

    with st.spinner("正在分析竞品数据…"):
        from competitor_monitor import analyze, to_excel
        result = analyze(df.copy())

    # 汇总
    if "summary" in result:
        st.markdown("####   数据概览")
        metrics = result["summary"]
        cols = st.columns(min(len(metrics), 4))
        for i, (k, v) in enumerate(metrics.items()):
            cols[i % 4].metric(k, v)

    # 价格对比
    if "price_summary" in result:
        st.markdown("####   价格对比")
        ps = result["price_summary"]
        cols = st.columns(min(len(ps), 4))
        for i, (k, v) in enumerate(ps.items()):
            cols[i % 4].metric(k, v)

    if "price_dist" in result:
        st.bar_chart(result["price_dist"].set_index("价格区间")["商品数"])

    # 销量排名
    if "sales_rank" in result:
        st.markdown("####   销量排名")
        st.dataframe(result["sales_rank"], use_container_width=True)

    # 评价分析
    tab1, tab2 = st.tabs(["  评分排名", "  评价数排名"])
    with tab1:
        if "rating_summary" in result:
            rs = result["rating_summary"]
            cols = st.columns(min(len(rs), 4))
            for i, (k, v) in enumerate(rs.items()):
                cols[i % 4].metric(k, v)
        if "rating_rank" in result:
            st.dataframe(result["rating_rank"], use_container_width=True)
    with tab2:
        if "review_rank" in result:
            st.dataframe(result["review_rank"], use_container_width=True)

    # 销量趋势
    if "sales_trend" in result:
        st.markdown("####   销量变化趋势")
        st.dataframe(result["sales_trend"], use_container_width=True)

    # 下载
    if can_access("export"):
        st.divider()
        buf = to_excel(result)
        st.download_button(
            "  下载竞品分析报告",
            data=buf,
            file_name="竞品分析报告.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
