# -*- coding: utf-8 -*-
"""企业管理后台"""

import streamlit as st
import pandas as pd

from db import (
    get_all_users, create_user, update_user_status, reset_password,
    get_logs, get_all_codes, generate_activation_code, revoke_code,
    get_online_users, get_user_permissions, set_user_permissions,
    delete_user_permissions,
)
from config import ROLES, ALL_FEATURE_KEYS
from auth_mod import get_current_user, get_role_name, has_permission, get_user_all_permissions, ROLE_DEFAULTS


def render():
    if not has_permission("admin"):
        st.error("权限不足，需要管理员权限")
        return

    is_super = has_permission("super_admin")
    tab_labels = ["  用户管理", "  激活码管理", "  操作日志", "  在线用户"]
    if is_super:
        tab_labels.append("  权限管理")
    tabs = st.tabs(tab_labels)
    tab_users, tab_codes, tab_logs, tab_online = tabs[:4]
    tab_perms = tabs[4] if is_super else None

    # ═══════════ 用户管理 ═══════════
    with tab_users:
        st.markdown("#### 用户列表")
        users = get_all_users()
        if users:
            df = pd.DataFrame(users)
            df["角色"] = df["role"].map(ROLES)
            df["状态"] = df["is_active"].apply(lambda x: "✅ 正常" if x else "🔒 禁用")
            st.dataframe(
                df[["username", "display_name", "角色", "状态", "last_login", "created_at"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "username": "用户名",
                    "display_name": "昵称",
                    "last_login": "最后登录",
                    "created_at": "注册时间",
                },
            )

        if has_permission("super_admin"):
            with st.expander("➕ 创建新用户"):
                with st.form("create_user_form"):
                    cu_user = st.text_input("用户名")
                    cu_pass = st.text_input("密码", type="password")
                    cu_role = st.selectbox("角色", list(ROLES.keys()),
                                           format_func=lambda x: ROLES[x])
                    cu_name = st.text_input("显示名称")
                    if st.form_submit_button("创建用户"):
                        ok, msg = create_user(cu_user, cu_pass, cu_role, cu_name)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with st.expander("  重置密码 / 启用禁用"):
                for u in users:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    col1.write(f"**{u['username']}** ({ROLES.get(u['role'], u['role'])})")
                    if col2.button("重置密码", key=f"rp_{u['username']}"):
                        reset_password(u["username"], "123456")
                        st.success(f"密码已重置为 123456")
                        st.rerun()
                    if u["username"] != "admin":
                        status_label = "禁用" if u["is_active"] else "启用"
                        if col3.button(status_label, key=f"st_{u['username']}"):
                            update_user_status(u["username"], 0 if u["is_active"] else 1)
                            st.rerun()

    # ═══════════ 激活码管理 ═══════════
    with tab_codes:
        st.markdown("#### 激活码管理")

        col_gen, _ = st.columns([1, 2])
        with col_gen:
            if st.button("  生成本周激活码", use_container_width=True):
                code_info = generate_activation_code(0, get_current_user())
                st.success(f"已生成: `{code_info['code']}` (周: {code_info['week']})")
                st.rerun()

        codes = get_all_codes()
        if codes:
            df = pd.DataFrame(codes)
            st.dataframe(
                df[["code", "week_label", "used_count", "max_uses", "is_active", "expires_at"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "code": "激活码",
                    "week_label": "周次",
                    "used_count": "已用次数",
                    "max_uses": "最大次数",
                    "is_active": st.column_config.NumberColumn("状态", format="%d"),
                    "expires_at": "过期时间",
                },
            )
            # 撤销按钮
            for c in codes:
                if c["is_active"]:
                    if st.button(f"撤销 {c['code']}", key=f"rev_{c['id']}"):
                        revoke_code(c["id"])
                        st.rerun()

    # ═══════════ 操作日志 ═══════════
    with tab_logs:
        st.markdown("#### 操作日志")
        logs = get_logs(200)
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(
                df[["created_at", "username", "action", "detail"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "created_at": "时间",
                    "username": "用户",
                    "action": "操作",
                    "detail": "详情",
                },
            )
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("  导出日志 CSV", csv, "operation_logs.csv",
                               "text/csv", use_container_width=True)
        else:
            st.info("暂无日志")

    # ═══════════ 在线用户 ═══════════
    with tab_online:
        st.markdown("#### 在线用户")
        online = get_online_users()
        if online:
            df = pd.DataFrame(online)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={"username": "用户名", "last_active": "最后活跃", "page": "当前页面"})
            st.metric("在线人数", len(online))
        else:
            st.info("当前无在线用户")

    # ═══════════ 权限管理（仅 super_admin） ═══════════
    if tab_perms is not None:
        with tab_perms:
            st.markdown("####  用户权限管理")
            st.caption("覆盖角色默认权限，仅需设置与角色默认不同的项。恢复默认请清除覆盖。")

            users = get_all_users()
            user_names = [u["username"] for u in users if u["username"] != "admin"]

            if not user_names:
                st.info("暂无其他用户")
            else:
                sel_user = st.selectbox("选择用户", user_names, key="perm_user")
                sel_role = next((u["role"] for u in users if u["username"] == sel_user), "operator")

                st.caption(f"角色: {ROLES.get(sel_role, sel_role)}")

                # 获取合并后的权限
                merged = get_user_all_permissions(sel_user, sel_role)
                overrides = get_user_permissions(sel_user)

                # 功能分类显示
                func_keys = [k for k in ALL_FEATURE_KEYS if not k.startswith("platform_")]
                plat_keys = [k for k in ALL_FEATURE_KEYS if k.startswith("platform_")]

                func_labels = {
                    "seo": "  生成标题", "roi": "  ROI 分析", "export": "  导出下载",
                    "keywords": "  热词同步", "lexicon": "  词库管理", "admin": "⚙️ 管理后台",
                }
                plat_labels = {
                    "platform_shopee": " Shopee", "platform_lazada": " Lazada",
                    "platform_tiktok": " TikTok", "platform_temu": " Temu",
                    "platform_amazon": " Amazon", "platform_taobao": " 淘宝",
                    "platform_pdd": " 拼多多", "platform_douyin": " 抖音",
                }

                st.markdown("##### 功能权限")
                new_perms = {}
                cols = st.columns(3)
                for i, key in enumerate(func_keys):
                    label = func_labels.get(key, key)
                    default_val = merged.get(key, False)
                    is_override = key in overrides
                    display = f"{label} {'*' if is_override else ''}"
                    val = cols[i % 3].checkbox(display, value=default_val, key=f"fp_{key}")
                    if val != ROLE_DEFAULTS.get(sel_role, {}).get(key, False):
                        new_perms[key] = val

                st.markdown("##### 平台权限")
                cols = st.columns(4)
                for i, key in enumerate(plat_keys):
                    label = plat_labels.get(key, key)
                    default_val = merged.get(key, False)
                    is_override = key in overrides
                    display = f"{label} {'*' if is_override else ''}"
                    val = cols[i % 4].checkbox(display, value=default_val, key=f"pp_{key}")
                    if val != ROLE_DEFAULTS.get(sel_role, {}).get(key, False):
                        new_perms[key] = val

                st.caption("* = 已覆盖角色默认值")

                col_save, col_reset, _ = st.columns([1, 1, 2])
                with col_save:
                    if st.button("  保存权限", use_container_width=True):
                        if new_perms:
                            set_user_permissions(sel_user, new_perms, get_current_user())
                            st.success(f"已更新 {sel_user} 的 {len(new_perms)} 项权限")
                            st.rerun()
                        else:
                            st.info("无变更")
                with col_reset:
                    if st.button("  恢复角色默认", use_container_width=True):
                        delete_user_permissions(sel_user)
                        st.success(f"已恢复 {sel_user} 的角色默认权限")
                        st.rerun()
