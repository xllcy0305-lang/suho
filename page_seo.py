# -*- coding: utf-8 -*-
"""SEO 标题生成页面"""

import streamlit as st
import pandas as pd

from config import PLATFORM_LIMITS
from seo_engine import dispatch
from excel_handler import export_titles_xlsx
from db import log_action
from auth_mod import get_current_user, can_access


def render(cat_data: dict, sel_cat_name: str, sel_plat_key: str,
           sel_plat_label: str, lex: dict):
    # 平台字符范围
    plim = PLATFORM_LIMITS.get(sel_plat_key, {})
    min_c = plim.get("min_chars", 0)
    max_c = plim.get("max_chars", 120)
    lang = plim.get("lang", "")
    lang_label = {"th": "泰语", "zh": "中文", "en": "英语"}.get(lang, lang)

    st.markdown(f"**当前类目:** `{sel_cat_name}` → `{sel_plat_label}`")
    st.caption(f"语言: {lang_label} | 字符范围: {min_c}-{max_c} 字符")
    subcats = cat_data.get("subcategories", [])
    if subcats:
        st.caption("子类目: " + " | ".join(subcats))

    # 显示平台热词标签
    hot_key_map = {
        "shopee_th": "shopee_hot", "lazada_th": "lazada_hot",
        "tiktok_global": "tiktok_hot", "temu": "temu_hot",
        "taobao": "cn_taobao_hot", "pinduoduo": "cn_pdd_hot",
        "douyin": "cn_douyin_hot",
    }
    hot_key = hot_key_map.get(sel_plat_key)
    if hot_key and cat_data.get(hot_key):
        hot_tags = " ".join(f"`{h}`" for h in cat_data[hot_key][:5])
        st.caption(f"平台热词: {hot_tags}")

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
                mc = max_c
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
                    if can_access("export"):
                        st.download_button(
                            "  下载全部标题 Excel",
                            data=buf, file_name=fname,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                    else:
                        st.caption("导出权限未开启，请联系管理员")
                    log_action(get_current_user(), "生成标题",
                               f"{sel_cat_name}/{sel_plat_label}: {len(titles)}条")
            except Exception as e:
                st.error(f"生成异常: {e}")
