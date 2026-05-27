# -*- coding: utf-8 -*-
"""ROI 分析页面 — 大文件优化版"""

import streamlit as st

from roi_analyzer import analyze_roi, check_file_size, MAX_FILE_SIZE
from db import log_action
from auth_mod import get_current_user


def _fmt_size(nbytes: int) -> str:
    if nbytes < 1024:
        return f"{nbytes} B"
    if nbytes < 1024 * 1024:
        return f"{nbytes/1024:.1f} KB"
    if nbytes < 1024 * 1024 * 1024:
        return f"{nbytes/(1024*1024):.1f} MB"
    return f"{nbytes/(1024*1024*1024):.2f} GB"


def render():
    st.markdown("####  广告保本 ROI 测算工具箱")
    st.info(
        "上传 Excel 利润表，系统自动追加 **单品保本 ROI** "
        "和 **全店通投保本 ROI** 两列，风险款（>2.5）自动标红，安全款（≤1.5）标绿。"
    )
    st.caption(f"最大支持上传: {_fmt_size(MAX_FILE_SIZE)} | 超大文件请拆分后分批上传")

    try:
        up = st.file_uploader(
            "拖拽或点击上传 Excel 利润表（.xlsx）",
            type=["xlsx"],
            key="roi_up",
            help="支持 .xlsx 格式，最大 1GB。超过 500MB 建议拆分。",
        )
        if up is None:
            return

        # ── 文件信息 ──
        file_bytes = up.getvalue()
        file_size = len(file_bytes)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("文件名", up.name)
        with col2:
            st.metric("文件大小", _fmt_size(file_size))

        # ── 文件大小检查 ──
        ok, msg, level = check_file_size(file_bytes)
        if level == "warning":
            st.warning(msg)
        elif level == "error":
            st.error(msg)
            st.stop()
        elif level == "info" and file_size > 50 * 1024 * 1024:
            st.info(msg)

        # ── 分析按钮 ──
        if st.button("  一键分析并生成保本 ROI 版", key="roi_btn", use_container_width=True):
            # 进度条
            progress_bar = st.progress(0)
            status_text = st.empty()

            def on_progress(step, pct):
                progress_bar.progress(pct, text=step)
                status_text.text(step)

            try:
                on_progress("开始处理…", 0)
                buf, name = analyze_roi(up, progress_callback=on_progress)

                progress_bar.progress(100, text="完成！")

                if buf:
                    st.success(f"✅ 分析完成！已追加保本 ROI 列")
                    st.download_button(
                        "  下载保本 ROI 分析版 Excel",
                        data=buf, file_name=name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                    log_action(get_current_user(), "ROI分析",
                               f"文件: {up.name} ({_fmt_size(file_size)})")
                else:
                    st.error(f"分析失败: {name}")
            except MemoryError:
                st.error("内存不足！文件过大，请拆分后重新上传。建议单文件不超过 500MB。")
            except Exception as e:
                st.error(f"处理异常: {e}")
            finally:
                # 清理进度条
                try:
                    progress_bar.empty()
                    status_text.empty()
                except Exception:
                    pass

    except Exception as e:
        st.error(f"ROI 模块异常: {e}")
