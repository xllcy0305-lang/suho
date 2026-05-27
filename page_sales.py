# -*- coding: utf-8 -*-
"""销售数据分析页面"""

import streamlit as st
import pandas as pd

from config import BRAND_NAME
from auth_mod import can_access


def render():
    st.markdown(f"###   销售数据分析")
    st.caption(f"{BRAND_NAME} — 上传销售数据 Excel，自动分析趋势/爆款/滞销/利润")

    uploaded = st.file_uploader(
        "上传销售数据 Excel 文件",
        type=["xlsx", "xls", "csv"],
        key="sales_upload",
    )

    if not uploaded:
        with st.expander("  支持的数据格式"):
            st.markdown("""
            Excel 或 CSV 文件，需包含以下列（列名支持中英文自动识别）：

            | 列名示例 | 说明 |
            |---------|------|
            | 日期 / date | 订单日期 |
            | SKU / 商品编码 | 商品唯一标识 |
            | 商品名称 / product_name | 商品标题 |
            | 销量 / quantity | 销售数量 |
            | 销售额 / amount | 销售金额 |
            | 成本 / cost | 成本价（可选） |

            列名会自动模糊匹配，顺序不限。
            """)
        return

    # 读取文件
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

    st.success(f"成功读取 {len(df)} 条数据，{len(df.columns)} 列")

    with st.expander("  预览数据", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

    # 分析
    with st.spinner("正在分析数据…"):
        from sales_analyzer import analyze, to_excel
        result = analyze(df.copy())

    if result.get("warnings"):
        for w in result["warnings"]:
            st.warning(w)

    # 汇总卡片
    if "summary" in result:
        st.markdown("####   汇总统计")
        metrics = result["summary"]
        cols = st.columns(min(len(metrics), 4))
        for i, (k, v) in enumerate(metrics.items()):
            cols[i % 4].metric(k, v)

    # 趋势图
    if "trend_daily" in result:
        st.markdown("####   销售趋势")
        st.line_chart(result["trend_daily"].set_index("日期")["销售额"])

    if "trend_weekly" in result:
        with st.expander("每周趋势"):
            st.bar_chart(result["trend_weekly"].set_index("周")["销售额"])

    # 爆款排行
    tab1, tab2 = st.tabs(["  销量 TOP20", "  销售额 TOP20"])
    with tab1:
        if "top_by_qty" in result:
            st.dataframe(result["top_by_qty"], use_container_width=True)
        else:
            st.info("无销量数据")
    with tab2:
        if "top_by_amount" in result:
            st.dataframe(result["top_by_amount"], use_container_width=True)
        else:
            st.info("无销售额数据")

    # 滞销预警
    if "slow_moving" in result and len(result["slow_moving"]) > 0:
        st.markdown("####   滞销预警")
        st.warning(f"以下 {len(result['slow_moving'])} 个 SKU 近 30 天销量极低：")
        st.dataframe(result["slow_moving"], use_container_width=True)

    # 利润分析
    if "profit" in result:
        st.markdown("####   利润分析")
        profit = result["profit"]
        if "毛利率" in profit.columns:
            st.bar_chart(profit.set_index("SKU")["毛利率"])
        st.dataframe(profit.head(30), use_container_width=True)

    if "loss_skus" in result and len(result["loss_skus"]) > 0:
        st.error(f"发现 {len(result['loss_skus'])} 个亏损 SKU！")
        st.dataframe(result["loss_skus"], use_container_width=True)

    # 下载
    if can_access("export"):
        st.divider()
        buf = to_excel(result)
        st.download_button(
            "  下载分析报告 Excel",
            data=buf,
            file_name="销售分析报告.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
