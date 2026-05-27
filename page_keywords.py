# -*- coding: utf-8 -*-
"""热词同步页面"""

import streamlit as st

from trend_scraper import scrape_google_trends_th
from db import log_action
from auth_mod import get_current_user
from config import LEXICON_PATH, BACKUP_DIR
from lexicon_manager import load_lexicon, save_lexicon, backup_lexicon, inject_keywords


def render(sel_cat_name: str, sel_cat_key: str):
    st.markdown(f"####  一键同步泰国热搜词 → `{sel_cat_name}`")
    st.info("点击按钮，联网抓取 Google Trends 泰国区飙升词，自动追加到当前类目长尾词库。")

    try:
        if st.button("  联网同步最新泰国热搜词", key="kw_btn", use_container_width=True):
            with st.spinner("正在抓取 Google Trends 泰国区…"):
                kws, msg = scrape_google_trends_th()
            st.info(msg)
            if kws:
                st.markdown("**抓取到的热词:**")
                for kw in kws:
                    st.markdown(f"- `{kw}`")

                lex = load_lexicon(LEXICON_PATH)
                backup_lexicon(BACKUP_DIR, lex)
                n, imsg = inject_keywords(sel_cat_key, kws, lex)
                st.success(imsg)
                save_lexicon(LEXICON_PATH, lex)
                try:
                    from app import _cached_lexicon
                    _cached_lexicon.clear()
                except Exception:
                    pass
                log_action(get_current_user(), "热词同步",
                           f"类目: {sel_cat_name}, 新增: {n}条")
                st.rerun()
    except Exception as e:
        st.error(f"热词同步异常: {e}")
