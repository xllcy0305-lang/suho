# -*- coding: utf-8 -*-
"""广告数据看板引擎 — 上传广告投放 Excel 自动生成看板"""

import pandas as pd
import numpy as np
from io import BytesIO


def _detect_columns(df):
    col_map = {}
    cols_lower = {c: str(c).lower().strip() for c in df.columns}
    mappings = {
        "date": ["日期", "date", "时间", "report_date", "投放日期"],
        "campaign": ["广告组", "campaign", "ad_group", "计划", "推广计划", "广告计划", "活动"],
        "keyword": ["关键词", "keyword", "搜索词", "search_term"],
        "impressions": ["展现", "impressions", "曝光", "展示次数", "views"],
        "clicks": ["点击", "clicks", "点击次数"],
        "cost": ["花费", "cost", "spend", "ad_cost", "消耗", "投放费用"],
        "orders": ["订单", "orders", "conversions", "成交", "成交笔数"],
        "sales": ["销售额", "sales", "gmv", "revenue", "成交额", "销售金额"],
        "cpc": ["cpc", "单次点击", "点击成本"],
        "ctr": ["ctr", "点击率"],
        "platform": ["平台", "platform", "渠道", "channel"],
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
    for key in ("impressions", "clicks", "cost", "orders", "sales", "cpc", "ctr"):
        if key in col_map:
            df[f"_{key}"] = pd.to_numeric(df[col_map[key]], errors="coerce").fillna(0)

    # 计算派生指标
    if "_impressions" in df.columns and "_clicks" in df.columns:
        df["_ctr"] = np.where(df["_impressions"] > 0, df["_clicks"] / df["_impressions"] * 100, 0)
    if "_clicks" in df.columns and "_cost" in df.columns:
        df["_cpc"] = np.where(df["_clicks"] > 0, df["_cost"] / df["_clicks"], 0)
    if "_cost" in df.columns and "_sales" in df.columns:
        df["_roi"] = np.where(df["_cost"] > 0, df["_sales"] / df["_cost"], 0)
    if "_clicks" in df.columns and "_impressions" in df.columns:
        df["_cvr"] = np.where(df["_clicks"] > 0, df.get("_orders", pd.Series(0, index=df.index)) / df["_clicks"] * 100, 0)

    # ── 1. 核心指标 ──
    summary = {}
    if "_cost" in df.columns:
        summary["总花费"] = f"{df['_cost'].sum():,.2f}"
    if "_sales" in df.columns:
        summary["总销售额"] = f"{df['_sales'].sum():,.2f}"
    if "_cost" in df.columns and "_sales" in df.columns:
        total_cost = df["_cost"].sum()
        total_sales = df["_sales"].sum()
        summary["整体 ROI"] = f"{total_sales / total_cost:.2f}" if total_cost > 0 else "N/A"
    if "_impressions" in df.columns:
        summary["总展现"] = f"{df['_impressions'].sum():,.0f}"
    if "_clicks" in df.columns:
        summary["总点击"] = f"{df["_clicks"].sum():,.0f}"
    if "_orders" in df.columns:
        summary["总订单"] = f"{df['_orders'].sum():,.0f}"
    if "_ctr" in df.columns and "_impressions" in df.columns:
        imp = df["_impressions"].sum()
        clk = df["_clicks"].sum()
        summary["平均CTR"] = f"{clk / imp * 100:.2f}%" if imp > 0 else "N/A"
    if "_cpc" in df.columns and "_cost" in df.columns:
        c = df["_cost"].sum()
        k = df["_clicks"].sum()
        summary["平均CPC"] = f"{c / k:.2f}" if k > 0 else "N/A"
    result["summary"] = summary

    # ── 2. ROI 趋势 ──
    if "_date" in df.columns and "_cost" in df.columns and "_sales" in df.columns:
        df["_date"] = pd.to_datetime(df[col_map["date"]], errors="coerce")
        if df["_date"].notna().sum() > 0:
            daily = df.groupby(df["_date"].dt.date).agg({"_cost": "sum", "_sales": "sum"}).reset_index()
            daily["ROI"] = np.where(daily["_cost"] > 0, (daily["_sales"] / daily["_cost"]).round(2), 0)
            daily.columns = ["日期", "花费", "销售额", "ROI"]
            result["roi_trend"] = daily.sort_values("日期")

    # ── 3. 广告组排行 ──
    campaign_col = col_map.get("campaign")
    if campaign_col:
        agg_dict = {}
        for k in ("_cost", "_sales", "_clicks", "_impressions", "_orders"):
            if k in df.columns:
                agg_dict[k] = "sum"

        if agg_dict:
            camp = df.groupby(campaign_col).agg(agg_dict).reset_index()
            camp = camp.rename(columns={campaign_col: "广告组"})
            rename_c = {}
            for k in agg_dict:
                rename_c[k] = {"_cost": "花费", "_sales": "销售额", "_clicks": "点击",
                               "_impressions": "展现", "_orders": "订单"}.get(k, k)
            camp = camp.rename(columns=rename_c)

            if "花费" in camp.columns and "销售额" in camp.columns:
                camp["ROI"] = np.where(camp["花费"] > 0, (camp["销售额"] / camp["花费"]).round(2), 0)
            if "点击" in camp.columns and "展现" in camp.columns:
                camp["CTR"] = np.where(camp["展现"] > 0, (camp["点击"] / camp["展现"] * 100).round(2), 0)
            if "花费" in camp.columns and "点击" in camp.columns:
                camp["CPC"] = np.where(camp["点击"] > 0, (camp["花费"] / camp["点击"]).round(2), 0)

            if "ROI" in camp.columns:
                result["camp_top_roi"] = camp.nlargest(20, "ROI").reset_index(drop=True)
                result["camp_low_roi"] = camp.nsmallest(20, "ROI").reset_index(drop=True)
            result["camp_all"] = camp.sort_values("花费", ascending=False).reset_index(drop=True)

    # ── 4. 关键词效果 ──
    kw_col = col_map.get("keyword")
    if kw_col:
        agg_kw = {}
        for k in ("_cost", "_sales", "_clicks", "_impressions", "_orders"):
            if k in df.columns:
                agg_kw[k] = "sum"
        if agg_kw:
            kw = df.groupby(kw_col).agg(agg_kw).reset_index()
            kw = kw.rename(columns={kw_col: "关键词"})
            rename_kw = {}
            for k in agg_kw:
                rename_kw[k] = {"_cost": "花费", "_sales": "销售额", "_clicks": "点击",
                                "_impressions": "展现", "_orders": "订单"}.get(k, k)
            kw = kw.rename(columns=rename_kw)
            if "点击" in kw.columns and "展现" in kw.columns:
                kw["CTR"] = np.where(kw["展现"] > 0, (kw["点击"] / kw["展现"] * 100).round(2), 0)
            if "花费" in kw.columns and "销售额" in kw.columns:
                kw["ROI"] = np.where(kw["花费"] > 0, (kw["销售额"] / kw["花费"]).round(2), 0)
            if "点击" in kw.columns and "订单" in kw.columns:
                kw["转化率"] = np.where(kw["点击"] > 0, (kw["订单"] / kw["点击"] * 100).round(2), 0)
            result["kw_effect"] = kw.sort_values("花费", ascending=False).head(50).reset_index(drop=True)

    # ── 5. 预算建议 ──
    if campaign_col and "camp_all" in result:
        camp = result["camp_all"]
        suggestions = []
        for _, row in camp.iterrows():
            name = row["广告组"]
            roi = row.get("ROI", 0)
            cost = row.get("花费", 0)
            if roi >= 3 and cost > 0:
                suggestions.append({"广告组": name, "建议": "加大预算", "ROI": roi, "当前花费": cost,
                                    "理由": f"ROI {roi:.1f} 高效，建议增加 30-50% 预算"})
            elif roi < 1 and cost > 0:
                suggestions.append({"广告组": name, "建议": "降低预算或暂停", "ROI": roi, "当前花费": cost,
                                    "理由": f"ROI {roi:.1f} 低于保本线，建议优化或暂停"})
            elif 1 <= roi < 2:
                suggestions.append({"广告组": name, "建议": "优化素材", "ROI": roi, "当前花费": cost,
                                    "理由": f"ROI {roi:.1f} 偏低，建议优化创意和关键词"})
        if suggestions:
            result["suggestions"] = pd.DataFrame(suggestions)

    return result


def to_excel(result):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        if "summary" in result:
            pd.DataFrame([result["summary"]]).to_excel(writer, sheet_name="核心指标", index=False)
        if "roi_trend" in result:
            result["roi_trend"].to_excel(writer, sheet_name="ROI趋势", index=False)
        if "camp_all" in result:
            result["camp_all"].to_excel(writer, sheet_name="广告组排行", index=False)
        if "kw_effect" in result:
            result["kw_effect"].to_excel(writer, sheet_name="关键词效果", index=False)
        if "suggestions" in result:
            result["suggestions"].to_excel(writer, sheet_name="预算建议", index=False)
    buf.seek(0)
    return buf
