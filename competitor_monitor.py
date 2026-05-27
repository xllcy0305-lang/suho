# -*- coding: utf-8 -*-
"""竞品监控引擎 — 上传竞品 Excel 数据，多维对比分析"""

import pandas as pd
import numpy as np
from io import BytesIO


def _detect_columns(df):
    col_map = {}
    cols_lower = {c: str(c).lower().strip() for c in df.columns}
    mappings = {
        "sku": ["sku", "商品编码", "商品id", "product_id", "asin", "货号"],
        "name": ["商品名称", "name", "title", "product_name", "品名"],
        "price": ["价格", "price", "售价", "selling_price", "单价"],
        "original_price": ["原价", "original_price", "划线价", "market_price"],
        "sales": ["月销量", "销量", "sales", "monthly_sales", "sold", "sale_count"],
        "rating": ["评分", "rating", "score", "rate", "评价分"],
        "reviews": ["评价数", "reviews", "review_count", "评论数", "ratings_count"],
        "shop": ["店铺", "shop", "seller", "店铺名", "卖家"],
        "date": ["日期", "date", "时间", "采集时间"],
        "type": ["类型", "type", "是否自有", "is_self"],
    }
    for key, keywords in mappings.items():
        for col, low in cols_lower.items():
            if any(kw in low for kw in keywords):
                col_map[key] = col
                break
    return col_map


def analyze(df):
    col_map = _detect_columns(df)
    result = {"col_map": col_map, "warnings": []}

    # 数值列
    for key in ("price", "original_price", "sales", "rating", "reviews"):
        if key in col_map:
            df[f"_{key}"] = pd.to_numeric(df[col_map[key]], errors="coerce")

    type_col = col_map.get("type")
    shop_col = col_map.get("shop")
    name_col = col_map.get("name")

    # 区分自有 vs 竞品
    if type_col:
        df["_is_self"] = df[col_map[type_col]].astype(str).str.lower().isin(
            ["自有", "self", "yes", "y", "1", "true"]
        )
    elif shop_col:
        df["_is_self"] = False
    else:
        df["_is_self"] = False

    # ── 1. 价格对比 ──
    if "_price" in df.columns:
        comp_prices = df[~df["_is_self"]]["_price"].dropna()
        self_prices = df[df["_is_self"]]["_price"].dropna()

        price_summary = {}
        if len(self_prices) > 0:
            price_summary["自有均价"] = f"{self_prices.mean():.2f}"
        if len(comp_prices) > 0:
            price_summary["竞品均价"] = f"{comp_prices.mean():.2f}"
            price_summary["竞品最低价"] = f"{comp_prices.min():.2f}"
            price_summary["竞品最高价"] = f"{comp_prices.max():.2f}"
            price_summary["竞品中位价"] = f"{comp_prices.median():.2f}"
        result["price_summary"] = price_summary

        # 价格区间分布
        if len(comp_prices) > 0:
            bins = [0, 50, 100, 200, 500, float("inf")]
            labels = ["<50", "50-100", "100-200", "200-500", ">500"]
            comp_dist = pd.cut(comp_prices, bins=bins, labels=labels).value_counts().reset_index()
            comp_dist.columns = ["价格区间", "商品数"]
            result["price_dist"] = comp_dist

    # ── 2. 销量对比 ──
    if "_sales" in df.columns:
        all_sales = df[["_sales"] + [c for c in (name_col, shop_col, col_map.get("sku")) if c]].copy()
        rename_s = {"_sales": "月销量"}
        if name_col:
            rename_s[name_col] = "商品名称"
        if shop_col:
            rename_s[shop_col] = "店铺"
        sku_c = col_map.get("sku")
        if sku_c:
            rename_s[sku_c] = "SKU"
        all_sales = all_sales.rename(columns=rename_s).sort_values("月销量", ascending=False)
        result["sales_rank"] = all_sales.head(30).reset_index(drop=True)

    # ── 3. 评价分析 ──
    if "_rating" in df.columns:
        ratings = df[["_rating"] + [c for c in (name_col, shop_col) if c]].dropna(subset=["_rating"])
        rename_r = {"_rating": "评分"}
        if name_col:
            rename_r[name_col] = "商品名称"
        if shop_col:
            rename_r[shop_col] = "店铺"
        ratings = ratings.rename(columns=rename_r).sort_values("评分")
        result["rating_rank"] = ratings.reset_index(drop=True)

        rating_summary = {
            "平均评分": f"{df['_rating'].mean():.2f}",
            "最高评分": f"{df['_rating'].max():.2f}",
            "最低评分": f"{df['_rating'].min():.2f}",
            "低于4分商品数": str(len(df[df['_rating'] < 4])),
        }
        result["rating_summary"] = rating_summary

    if "_reviews" in df.columns:
        reviews = df[["_reviews"] + [c for c in (name_col, shop_col) if c]].dropna(subset=["_reviews"])
        rename_rv = {"_reviews": "评价数"}
        if name_col:
            rename_rv[name_col] = "商品名称"
        if shop_col:
            rename_rv[shop_col] = "店铺"
        reviews = reviews.rename(columns=rename_rv).sort_values("评价数", ascending=False)
        result["review_rank"] = reviews.head(30).reset_index(drop=True)

    # ── 4. 变化趋势（需要有日期列且多次采集）──
    if "_sales" in df.columns and "_date" in df.columns:
        df["_date"] = pd.to_datetime(df[col_map["date"]], errors="coerce")
        sku_col = col_map.get("sku")
        if sku_col and df["_date"].notna().sum() > 0:
            dates = df["_date"].dropna().unique()
            if len(dates) > 1:
                trend = df.groupby([sku_col, df["_date"].dt.date])["_sales"].mean().reset_index()
                trend.columns = ["SKU", "日期", "平均销量"]
                result["sales_trend"] = trend

    # ── 5. 汇总 ──
    summary = {"总商品数": str(len(df))}
    if shop_col:
        summary["店铺数量"] = str(df[shop_col].nunique())
    summary["自有商品数"] = str(int(df["_is_self"].sum()))
    summary["竞品数"] = str(int((~df["_is_self"]).sum()))
    result["summary"] = summary

    return result


def to_excel(result):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if "summary" in result:
            pd.DataFrame([result["summary"]]).to_excel(writer, sheet_name="汇总", index=False)
        if "price_summary" in result:
            pd.DataFrame([result["price_summary"]]).to_excel(writer, sheet_name="价格对比", index=False)
        if "price_dist" in result:
            result["price_dist"].to_excel(writer, sheet_name="价格区间分布", index=False)
        if "sales_rank" in result:
            result["sales_rank"].to_excel(writer, sheet_name="销量排名", index=False)
        if "rating_rank" in result:
            result["rating_rank"].to_excel(writer, sheet_name="评分排名", index=False)
        if "review_rank" in result:
            result["review_rank"].to_excel(writer, sheet_name="评价数排名", index=False)
        if "sales_trend" in result:
            result["sales_trend"].to_excel(writer, sheet_name="销量趋势", index=False)
    buf.seek(0)
    return buf
