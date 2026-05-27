# -*- coding: utf-8 -*-
"""选品智能报告页面 — 市场分析与选品建议"""

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

from config import BRAND_NAME
from auth_mod import can_access


def _detect_columns(df):
    col_map = {}
    cols_lower = {c: str(c).lower().strip() for c in df.columns}
    mappings = {
        "category": ["类目", "category", "子类目", "sub_category", "品类", "三级类目"],
        "sales": ["销量", "sales", "月销量", "total_sales", "总销量"],
        "amount": ["销售额", "amount", "gmv", "revenue", "总销售额"],
        "search_vol": ["搜索量", "search_volume", "search_vol", "关键词搜索量"],
        "sellers": ["卖家数", "sellers", "seller_count", "商家数", "listing数", "商品数"],
        "avg_price": ["均价", "avg_price", "平均价格", "平均售价"],
        "rating": ["评分", "rating", "平均评分", "avg_rating"],
        "reviews": ["评价数", "reviews", "平均评价数", "review_count"],
        "keyword": ["关键词", "keyword", "搜索词"],
        "growth": ["增长率", "growth", "环比", "同比"],
    }
    for key, keywords in mappings.items():
        for col, low in cols_lower.items():
            if any(kw in low for kw in keywords):
                col_map[key] = col
                break
    return col_map


def _calc_opportunity(df, col_map):
    """计算机会评分"""
    scores = pd.DataFrame()
    cat_col = col_map.get("category")
    if cat_col:
        scores["类目"] = df[cat_col]

    # 市场容量分（销量越高越好）
    if "sales" in col_map:
        s = pd.to_numeric(df[col_map["sales"]], errors="coerce").fillna(0)
        max_s = s.max()
        scores["市场容量分"] = ((s / max_s * 40) if max_s > 0 else 0).round(1)

    # 竞争度分（卖家越少越好）
    if "sellers" in col_map:
        sel = pd.to_numeric(df[col_map["sellers"]], errors="coerce").fillna(9999)
        max_sel = sel.max()
        scores["竞争度分"] = ((1 - sel / max_sel * 0.8) * 30 if max_sel > 0 else 15).round(1)

    # 搜索热度分
    if "search_vol" in col_map:
        sv = pd.to_numeric(df[col_map["search_vol"]], errors="coerce").fillna(0)
        max_sv = sv.max()
        scores["搜索热度分"] = ((sv / max_sv * 30) if max_sv > 0 else 0).round(1)

    # 总分
    score_cols = [c for c in scores.columns if c.endswith("分")]
    if score_cols:
        scores["机会评分"] = scores[score_cols].sum(axis=1).round(1)
        scores = scores.sort_values("机会评分", ascending=False)

    return scores.reset_index(drop=True)


def render():
    st.markdown(f"###   选品智能报告")
    st.caption(f"{BRAND_NAME} — 上传市场数据，自动生成选品建议")

    uploaded = st.file_uploader(
        "上传市场数据 Excel 文件",
        type=["xlsx", "xls", "csv"],
        key="pr_upload",
    )

    if not uploaded:
        with st.expander("  支持的数据格式"):
            st.markdown("""
            Excel 或 CSV 文件，包含市场/类目数据：

            | 列名示例 | 说明 |
            |---------|------|
            | 类目 / category | 子类目名称 |
            | 销量 / sales | 类目总销量 |
            | 销售额 / amount | 类目总 GMV |
            | 搜索量 / search_volume | 关键词搜索量 |
            | 卖家数 / sellers | 竞争对手数量 |
            | 均价 / avg_price | 平均售价 |
            | 评分 / rating | 平均评分 |
            | 增长率 / growth | 环比增长率 |

            数据越全面，报告越精准。最少需要类目 + 销量 + 卖家数。
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

    st.success(f"成功读取 {len(df)} 条市场数据")

    with st.expander("  预览数据", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

    col_map = _detect_columns(df)

    # ── 市场容量分析 ──
    st.markdown("####   市场容量分析")
    summary = {}
    if "sales" in col_map:
        total_sales = pd.to_numeric(df[col_map["sales"]], errors="coerce").sum()
        summary["总销量"] = f"{total_sales:,.0f}"
    if "amount" in col_map:
        total_gmv = pd.to_numeric(df[col_map["amount"]], errors="coerce").sum()
        summary["总 GMV"] = f"{total_gmv:,.2f}"
    if "sellers" in col_map:
        total_sellers = pd.to_numeric(df[col_map["sellers"]], errors="coerce").sum()
        summary["总卖家数"] = f"{total_sellers:,.0f}"
    summary["类目数"] = str(len(df))

    if summary:
        cols = st.columns(min(len(summary), 4))
        for i, (k, v) in enumerate(summary.items()):
            cols[i % 4].metric(k, v)

    # ── 竞争度分析 ──
    if "sellers" in col_map and "sales" in col_map:
        st.markdown("####   竞争度分析")
        comp = df.copy()
        sellers_num = pd.to_numeric(comp[col_map["sellers"]], errors="coerce").fillna(1)
        sales_num = pd.to_numeric(comp[col_map["sales"]], errors="coerce").fillna(0)
        comp["单卖家销量"] = (sales_num / sellers_num.replace(0, 1)).round(1)

        cat_col = col_map.get("category")
        if cat_col:
            comp_viz = comp[[cat_col, col_map["sellers"], col_map["sales"], "单卖家销量"]].copy()
            comp_viz.columns = ["类目", "卖家数", "总销量", "单卖家销量"]
            st.dataframe(comp_viz.sort_values("单卖家销量", ascending=False).head(20),
                         use_container_width=True)

    # ── 机会评分 ──
    st.markdown("####   机会评分")
    scores = _calc_opportunity(df, col_map)

    if "机会评分" in scores.columns:
        st.dataframe(scores, use_container_width=True)

        # 推荐选品
        if len(scores) > 0:
            top_n = scores.head(10)
            st.markdown("####   推荐选品清单")
            for _, row in top_n.iterrows():
                name = row.get("类目", "未知类目")
                score = row.get("机会评分", 0)
                color = "#10b981" if score >= 60 else "#f59e0b" if score >= 40 else "#ef4444"
                st.markdown(f"""
                <div style="background:rgba(255,255,255,.04);border-left:4px solid {color};
                            padding:.8rem 1rem;margin:.4rem 0;border-radius:0 8px 8px 0;">
                    <b>{name}</b> — 机会评分: <span style="color:{color};font-weight:700">{score}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── 详细数据 ──
    with st.expander("  完整数据表"):
        st.dataframe(df, use_container_width=True)

    # ── 下载 ──
    if can_access("export"):
        st.divider()
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            if summary:
                pd.DataFrame([summary]).to_excel(writer, sheet_name="市场概况", index=False)
            if len(scores) > 0:
                scores.to_excel(writer, sheet_name="机会评分", index=False)
            df.to_excel(writer, sheet_name="原始数据", index=False)
        buf.seek(0)

        st.download_button(
            "  下载选品报告 Excel",
            data=buf,
            file_name="选品智能报告.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
