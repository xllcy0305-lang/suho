# -*- coding: utf-8 -*-
"""词库管理页面"""

import json
import streamlit as st

from config import LEXICON_PATH, BACKUP_DIR
from utils.lexicon_manager import load_lexicon, save_lexicon, backup_lexicon
from database.db import log_action
from auth.auth import get_current_user, has_permission


def _clear_lexicon_cache():
    """清除 app.py 中的词库缓存"""
    try:
        from app import _cached_lexicon
        _cached_lexicon.clear()
    except Exception:
        pass


def render(lex: dict):
    st.markdown("####  全类目词库管理")
    is_manager = has_permission("supervisor")

    cats_all = {k: v for k, v in lex.get("categories", {}).items() if not k.startswith("_")}

    for ck, cd in cats_all.items():
        with st.expander(f"  {cd.get('display_name', ck)}", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("主词", len(cd.get("base", [])))
            c2.metric("材质/规格", len(cd.get("material_specs", [])))
            c3.metric("场景/人群", len(cd.get("scene_audience", [])))
            c4.metric("长尾词", len(cd.get("longtail", [])))
            st.caption("子类目: " + " | ".join(cd.get("subcategories", [])))

            if is_manager:
                with st.form(f"add_word_{ck}"):
                    col_a, col_b = st.columns([1, 2])
                    dim = col_a.selectbox("维度", ["longtail", "base", "material_specs", "scene_audience"], key=f"dim_{ck}")
                    new_word = col_b.text_input("添加词语", key=f"word_{ck}")
                    if st.form_submit_button("添加"):
                        if new_word.strip():
                            if dim in cd:
                                cd[dim].append(new_word.strip())
                                lex["categories"][ck] = cd
                                save_lexicon(LEXICON_PATH, lex)
                                _clear_lexicon_cache()
                                log_action(get_current_user(), "添加词汇",
                                           f"{cd.get('display_name')}/{dim}: {new_word.strip()}")
                                st.success(f"已添加: {new_word.strip()}")
                                st.rerun()

    # 导出
    lex_json = json.dumps(lex, ensure_ascii=False, indent=4)
    st.download_button("  下载当前词库 JSON", lex_json,
                       "thai_keywords_lexicon.json", "application/json",
                       use_container_width=True)

    # 导入
    if is_manager:
        st.divider()
        st.markdown("####  导入词库 JSON")
        up = st.file_uploader("上传词库 JSON 文件", type=["json"], key="lex_up")
        if up:
            try:
                data = json.load(up)
                if data.get("categories") and data.get("platform_limits"):
                    backup_lexicon(BACKUP_DIR, lex)
                    save_lexicon(LEXICON_PATH, data)
                    _clear_lexicon_cache()
                    log_action(get_current_user(), "导入词库", f"文件: {up.name}")
                    st.success("词库导入成功！")
                    st.rerun()
                else:
                    st.error("词库格式不正确")
            except Exception as e:
                st.error(f"导入失败: {e}")
