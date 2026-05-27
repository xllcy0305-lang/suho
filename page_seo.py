# -*- coding: utf-8 -*-
"""SEO 标题生成页面"""

import streamlit as st
import pandas as pd

from seo_engine import dispatch
from excel_handler import export_titles_xlsx
from db import log_action
from auth_mod import get_current_user


def render(cat_data: dict, sel_cat_name: str, sel_plat_key: str,
           sel_plat_label: str, lex: dict):
    st.markdown(f"**当前类目:** `{sel_cat_name}` → `{sel_plat_label}`")
    subcats = cat_data.get("subcategories", [])
    if subcats:
        st.caption("子类目: " + " | ".join(subcats))

    product_cn = st.text_input(
        "  请输入中文产品词",
        placeholder="例如：智能手表、防晒霜、月亮椅、婴儿推车",
        key="product_input",
    )

    if st.button("  批量生成 50 个爆款标题", key="gen_btn", use_container_width=True):
        if not product_cn.strip():
            st.warning("⚠ 请先输入中文产品词")
        else:
            try:
                mc = lex.get("platform_limits", {}).get(sel_plat_key, {}).get("max_chars", 120)
                with st.spinner("⏳ AI 正在生成标题，请稍候…"):
                    titles = dispatch(product_cn.strip(), sel_plat_key, cat_data, mc)
                if not titles:
                    st.error("生成失败，词库数据不足。请联系管理员更新词库。")
                else:
                    st.success(f"✅ 已生成 **{len(titles)}** 条不重复标题！")

                    # AI评分排序
                    titles_sorted = sorted(titles, key=lambda x: x.get("score", 0), reverse=True)

                    st.markdown("#####  Top 5 爆款预览（按AI评分排序）")
                    for i, item in enumerate(titles_sorted[:5], 1):
                        score = item.get("score", 0)
                        color = "#10b981" if score >= 75 else "#f59e0b" if score >= 60 else "#ef4444"
                        st.markdown(
                            f'<div class="title-card">'
                            f'<span style="color:#a5b4fc;font-weight:600;">{i}.</span> '
                            f'{item["title"]} '
                            f'<span style="color:#666;font-size:0.8rem;">'
                            f'({item.get("chars", len(item["title"]))}字符)</span> '
                            f'<span style="background:{color};color:#fff;padding:2px 8px;'
                            f'border-radius:12px;font-size:0.75rem;font-weight:700;">'
                            f'{score}分</span>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    with st.expander("查看全部标题"):
                        df = pd.DataFrame({
                            "序号": range(1, len(titles_sorted) + 1),
                            "SEO 标题": [t["title"] for t in titles_sorted],
                            "字符数": [t.get("chars", 0) for t in titles_sorted],
                            "AI评分": [t.get("score", 0) for t in titles_sorted],
                        })
                        st.dataframe(df, use_container_width=True, hide_index=True)

                    buf, fname = export_titles_xlsx(
                        titles_sorted, sel_plat_key, product_cn.strip(),
                        lex.get("platform_limits", {}),
                    )
                    st.divider()
                    st.download_button(
                        "  下载全部标题 Excel",
                        data=buf, file_name=fname,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                    log_action(get_current_user(), "生成标题",
                               f"{sel_cat_name}/{sel_plat_label}: {len(titles)}条")
            except Exception as e:
                st.error(f"生成异常: {e}")
