"""
股票监控配置页面模块
"""

import streamlit as st
from components.monitor_config_form import render_monitor_config_form
import yaml
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "monitor_config.yaml"

def save_monitor_config(config_list):
    """保存监控配置到 YAML 文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_list, f, allow_unicode=True)
        st.success("监控配置已持久化到 monitor_config.yaml")
    except Exception as e:
        st.error(f"保存配置失败: {e}")

def load_monitor_config():
    """从 YAML 文件加载监控配置，不存在则自动创建空文件"""
    if not CONFIG_FILE.exists():
        try:
            CONFIG_FILE.touch()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump([], f, allow_unicode=True)
        except Exception as e:
            st.warning(f"自动创建配置文件失败: {e}")
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    except Exception as e:
        st.warning(f"加载配置失败: {e}")
    return []

def render_monitor_config():
    st.header("📋 股票监控配置")
    # 加载已保存配置
    if "monitor_config" not in st.session_state:
        st.session_state["monitor_config"] = load_monitor_config()

    config_list = render_monitor_config_form()

    # 持久化保存
    if st.session_state.get("monitor_config_saved"):
        save_monitor_config(config_list)
        st.session_state["monitor_config_saved"] = False

    # 仅 admin 用户可见的测试邮件发送按钮
    if st.session_state.get("user_role") == "admin":
        st.subheader("🔒 测试邮件发送（仅管理员可见）")
        test_email = st.text_input("测试收件邮箱", key="test_email_input")
        if st.button("发送测试邮件", key="send_test_email_btn"):
            from web.utils.send_email import send_email
            try:
                send_email(
                    subject="【TradingAgents】测试邮件",
                    content="<h3>这是一封测试邮件，说明邮件服务配置正常。</h3>",
                    to_addr=test_email
                )
                st.success(f"测试邮件已发送到 {test_email}")
            except Exception as e:
                st.error(f"测试邮件发送失败: {e}")

    # 显示配置文件路径
    st.info(f"配置文件路径: {CONFIG_FILE}")
