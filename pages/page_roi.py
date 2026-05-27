# -*- coding: utf-8 -*-
"""ROI 分析页面"""

import streamlit as st
from utils.roi_analyzer import analyze_roi
from database.db import log_action
from auth.auth import get_current_user


def render():
    st.markdown("####  广告保本 ROI 测算工具箱")
    st.info(
        "上传 Excel 利润表，系统自动追加 **单品保本 ROI** "
        "和 **全店通投保本 ROI** 两列，风险款（>2.5）自动标红，安全款（≤1.5）标绿。"
    )

    try:
        up = st.file_uploader(
            "拖拽或点击上传 Excel 利润表（.xlsx）",
            type=["xlsx"],
            key="roi_up",
        )
        if up:
            st.success(f"已上传: `{up.name}`")
            if st.button("  一键分析并生成保本 ROI 版", key="roi_btn", use_container_width=True):
                with st.spinner("正在分析利润率…"):
                    buf, name = analyze_roi(up)
                if buf:
                    st.success("✅ 分析完成！已追加保本 ROI 列")
                    st.download_button(
                        "  下载保本 ROI 分析版 Excel",
                        data=buf, file_name=name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                    log_action(get_current_user(), "ROI分析", f"文件: {up.name}")
                else:
                    st.error(f"分析失败: {name}")
    except Exception as e:
        st.error(f"ROI 模块异常: {e}")
