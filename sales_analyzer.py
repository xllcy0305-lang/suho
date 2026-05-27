# -*- coding: utf-8 -*-
"""销售数据分析引擎 — 上传 Excel 自动生成分析报告"""

import pandas as pd
import numpy as np
from io import BytesIO


def _detect_columns(df):
    """自动识别列名映射"""
    col_map = {}
    cols_lower = {c: str(c).lower().strip() for c in df.columns}

    mappings = {
        "date": ["日期", "date", "时间", "order_date", "sale_date", "下单时间", "交易时间"],
        "sku": ["sku", "商品编码", "商品id", "product_id", "item_id", "货号", "asin"],
        "name": ["商品名称", "name", "product_name", "title", "商品标题", "品名"],
        "quantity": ["销量", "数量", "quantity", "qty", "sales_qty", "order_qty", "售出数量"],
        "amount": ["销售额", "金额", "amount", "sales_amount", "revenue", "gmv", "total", "售价"],
        "cost": ["成本", "cost", "cost_price", "采购成本", "进货价"],
        "platform": ["平台", "platform", "渠道", "channel"],
        "category": ["类目", "category", "品类"],
    }

    for key, keywords in mappings.items():
        for col, low in cols_lower.items():
            if any(kw in low for kw in keywords):
                col_map[key] = col
                break

    return col_map


def analyze(df):
    """主分析函数，返回 dict 结果"""
    col_map = _detect_columns(df)

    result = {"col_map": col_map, "warnings": []}

    # 日期列处理
    if "date" in col_map:
        df["_date"] = pd.to_datetime(df[col_map["date"]], errors="coerce")
        if df["_date"].isna().all():
            result["warnings"].append("日期列无法解析为日期格式")
            del df["_date"]

    # 数值列处理
    for key in ("quantity", "amount", "cost"):
        if key in col_map:
            df[f"_{key}"] = pd.to_numeric(df[col_map[key]], errors="coerce").fillna(0)

    # ── 1. 销售趋势 ──
    if "_date" in df.columns and "_amount" in df.columns:
        daily = df.groupby(df["_date"].dt.date)["_amount"].sum().reset_index()
        daily.columns = ["日期", "销售额"]
        daily = daily.sort_values("日期")
        result["trend_daily"] = daily

        if len(daily) >= 7:
            weekly = df.groupby(df["_date"].dt.to_period("W"))["_amount"].sum().reset_index()
            weekly.columns = ["周", "销售额"]
            weekly["周"] = weekly["周"].astype(str)
            result["trend_weekly"] = weekly

    # ── 2. 爆款排行 ──
    sku_col = col_map.get("sku")
    name_col = col_map.get("name")

    if sku_col:
        group_cols = [sku_col]
        if name_col and name_col != sku_col:
            group_cols.append(name_col)

        agg_dict = {}
        if "_quantity" in df.columns:
            agg_dict["_quantity"] = "sum"
        if "_amount" in df.columns:
            agg_dict["_amount"] = "sum"
        if "_cost" in df.columns:
            agg_dict["_cost"] = "sum"

        if agg_dict:
            top = df.groupby(group_cols).agg(agg_dict).reset_index()
            rename = {sku_col: "SKU"}
            if name_col and name_col in top.columns:
                rename[name_col] = "商品名称"
            if "_quantity" in top.columns:
                rename["_quantity"] = "总销量"
            if "_amount" in top.columns:
                rename["_amount"] = "总销售额"
            if "_cost" in top.columns:
                rename["_cost"] = "总成本"
            top = top.rename(columns=rename)

            if "总销量" in top.columns:
                result["top_by_qty"] = top.nlargest(20, "总销量").reset_index(drop=True)
            if "总销售额" in top.columns:
                result["top_by_amount"] = top.nlargest(20, "总销售额").reset_index(drop=True)

            # ── 3. 滞销预警 ──
            if "_date" in df.columns and "_quantity" in df.columns:
                recent = df[df["_date"] >= df["_date"].max() - pd.Timedelta(days=30)]
                if len(recent) > 0:
                    slow = recent.groupby(sku_col)["_quantity"].sum().reset_index()
                    slow.columns = ["SKU", "近30天销量"]
                    slow = slow[slow["近30天销量"] < slow["近30天销量"].quantile(0.1)]
                    if name_col:
                        name_map = df.drop_duplicates(sku_col).set_index(sku_col)[name_col].to_dict()
                        slow["商品名称"] = slow["SKU"].map(name_map).fillna("")
                    slow = slow.sort_values("近30天销量")
                    result["slow_moving"] = slow.reset_index(drop=True)

            # ── 4. 利润分析 ──
            if "_amount" in df.columns and "_cost" in df.columns:
                profit = df.groupby(group_cols).agg({"_amount": "sum", "_cost": "sum"}).reset_index()
                profit["毛利"] = profit["_amount"] - profit["_cost"]
                profit["毛利率"] = np.where(
                    profit["_amount"] > 0,
                    (profit["毛利"] / profit["_amount"] * 100).round(2),
                    0,
                )
                rename_p = {sku_col: "SKU"}
                if name_col and name_col in profit.columns:
                    rename_p[name_col] = "商品名称"
                rename_p["_amount"] = "总销售额"
                rename_p["_cost"] = "总成本"
                profit = profit.rename(columns=rename_p)
                profit = profit.sort_values("毛利率")
                result["profit"] = profit.reset_index(drop=True)
                result["loss_skus"] = profit[profit["毛利率"] < 0].reset_index(drop=True)

    # ── 5. 汇总统计 ──
    summary = {}
    if "_amount" in df.columns:
        summary["总销售额"] = f"{df['_amount'].sum():,.2f}"
    if "_quantity" in df.columns:
        summary["总销量"] = f"{df['_quantity'].sum():,.0f}"
    if "_cost" in df.columns and "_amount" in df.columns:
        total_profit = df["_amount"].sum() - df["_cost"].sum()
        margin = (total_profit / df["_amount"].sum() * 100) if df["_amount"].sum() > 0 else 0
        summary["总毛利"] = f"{total_profit:,.2f}"
        summary["整体毛利率"] = f"{margin:.1f}%"
    summary["SKU 数量"] = str(df[sku_col].nunique()) if sku_col else "N/A"
    summary["数据行数"] = str(len(df))
    if "_date" in df.columns:
        summary["日期范围"] = f"{df['_date'].min().date()} ~ {df['_date'].max().date()}"
    result["summary"] = summary

    return result


def to_excel(result):
    """将分析结果导出为 Excel"""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if "summary" in result:
            pd.DataFrame([result["summary"]]).to_excel(writer, sheet_name="汇总", index=False)
        if "trend_daily" in result:
            result["trend_daily"].to_excel(writer, sheet_name="每日趋势", index=False)
        if "trend_weekly" in result:
            result["trend_weekly"].to_excel(writer, sheet_name="每周趋势", index=False)
        if "top_by_qty" in result:
            result["top_by_qty"].to_excel(writer, sheet_name="销量TOP20", index=False)
        if "top_by_amount" in result:
            result["top_by_amount"].to_excel(writer, sheet_name="销售额TOP20", index=False)
        if "slow_moving" in result:
            result["slow_moving"].to_excel(writer, sheet_name="滞销预警", index=False)
        if "profit" in result:
            result["profit"].to_excel(writer, sheet_name="利润分析", index=False)
        if "loss_skus" in result and len(result["loss_skus"]) > 0:
            result["loss_skus"].to_excel(writer, sheet_name="亏损SKU", index=False)
    buf.seek(0)
    return buf
