"""
股票监控配置表单组件
"""

import streamlit as st

def render_monitor_config_form():
    """
    渲染股票监控配置表单，支持多只股票配置
    """
    st.subheader("📋 股票监控配置")

    # 读取已保存的监控配置
    monitor_config = st.session_state.get('monitor_config', [])

    # 新增股票配置
    if 'new_stock_configs' not in st.session_state:
        st.session_state['new_stock_configs'] = []

    st.markdown("#### 当前监控列表")
    if monitor_config:
        for idx, item in enumerate(monitor_config):
            st.markdown(
                f"- **{item['market_type']}** | 代码: `{item['stock_symbol']}` | 深度: {item['research_depth']} | 团队: {', '.join(item['selected_analysts'])} | 邮箱: {item['email']}"
            )
    else:
        st.info("暂无监控配置，请在下方添加。")

    st.markdown("---")
    st.markdown("#### 添加新的监控项")

    with st.form("monitor_config_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            market_type = st.selectbox(
                "选择市场 🌍",
                options=["A股", "美股", "港股"],
                index=0,
                help="选择要监控的股票市场"
            )
            stock_symbol = st.text_input(
                "股票代码 📈",
                value="",
                placeholder="如 AAPL, 000001, 0700.HK",
                help="输入要监控的股票代码"
            ).strip().upper()
            frequency = st.selectbox(
                "发送频率 ⏰",
                options=["每日", "每3天", "每5天", "交易日"],
                index=0,
                help="选择分析报告发送频率"
            )
            # 新增：LLM Provider 选择
            provider_options = [
                ("azureopenai", "Azure OpenAI"),
                ("dashscope", "阿里通义"),
                ("deepseek", "DeepSeek"),
                ("google", "Google Gemini"),
                ("openrouter", "OpenRouter")
            ]
            provider_keys = [x[0] for x in provider_options]
            provider_labels = [x[1] for x in provider_options]
            default_provider = "azureopenai"
            llm_provider = st.selectbox(
                "大模型服务商",
                options=provider_keys,
                format_func=lambda x: dict(provider_options)[x],
                index=provider_keys.index(default_provider),
                help="选择用于分析的LLM服务商"
            )
            # 动态模型选项
            model_options_map = {
                "azureopenai": ["o3", "o4-mini", "gpt-35-turbo", "gpt-4"],
                "dashscope": ["qwen-plus", "qwen-max", "qwen-turbo"],
                "deepseek": ["deepseek-chat"],
                "google": ["gemini-pro"],
                "openrouter": ["openrouter-mixtral", "openrouter-qwen", "openrouter-gpt4"]
            }
            default_model_map = {
                "azureopenai": "o3",
                "dashscope": "qwen-plus",
                "deepseek": "deepseek-chat",
                "google": "gemini-pro",
                "openrouter": "openrouter-mixtral"
            }
            llm_model = st.selectbox(
                "大模型名称",
                options=model_options_map[llm_provider],
                index=model_options_map[llm_provider].index(default_model_map[llm_provider]),
                help="选择用于分析的具体大模型"
            )
        with col2:
            research_depth = st.select_slider(
                "分析深度 🔍",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: {
                    1: "1级-快速",
                    2: "2级-基础",
                    3: "3级-标准",
                    4: "4级-深度",
                    5: "5级-全面"
                }[x],
                help="分析深度越高，分析越详细"
            )
            email = st.text_input(
                "接收邮箱 📧",
                value="",
                placeholder="your@email.com",
                help="分析结果将发送到此邮箱"
            ).strip()
            send_time = st.time_input(
                "执行分析时间 🕗",
                value=None,
                help="每天/每周期几点执行分析（如08:00、21:00）"
            )

        st.markdown("##### 选择分析团队")
        col3, col4 = st.columns(2)
        with col3:
            market_analyst = st.checkbox("📈 市场分析师", value=True)
            social_analyst = st.checkbox("💭 社交媒体分析师", value=False)
        with col4:
            news_analyst = st.checkbox("📰 新闻分析师", value=False)
            fundamentals_analyst = st.checkbox("💰 基本面分析师", value=True)

        selected_analysts = []
        if market_analyst:
            selected_analysts.append("市场分析师")
        if social_analyst:
            selected_analysts.append("社交媒体分析师")
        if news_analyst:
            selected_analysts.append("新闻分析师")
        if fundamentals_analyst:
            selected_analysts.append("基本面分析师")

        # 新增：测试发送邮件按钮
        test_email_btn = st.form_submit_button("✉️ 测试发送邮件", type="secondary")
        submitted = st.form_submit_button("➕ 添加到监控列表", type="primary")

        # 校验
        error_msg = None
        if submitted:
            if not stock_symbol:
                error_msg = "请填写股票代码"
            elif not email or "@" not in email:
                error_msg = "请填写有效的邮箱地址"
            elif not selected_analysts:
                error_msg = "请至少选择一个分析团队"

        if submitted and not error_msg:
            # 添加到 session_state
            new_item = {
                "market_type": market_type,
                "stock_symbol": stock_symbol,
                "research_depth": research_depth,
                "selected_analysts": selected_analysts,
                "email": email,
                "frequency": frequency,
                "send_time": send_time.strftime("%H:%M") if send_time else "08:00",
                "llm_provider": llm_provider,
                "llm_model": llm_model
            }
            monitor_config.append(new_item)
            st.session_state['monitor_config'] = monitor_config
            st.success(f"已添加：{market_type} {stock_symbol}，将发送到 {email}，频率：{frequency}，时间：{new_item['send_time']}，模型：{llm_provider}/{llm_model}")
        elif submitted and error_msg:
            st.error(error_msg)

        # 新增：测试发送邮件逻辑
        if test_email_btn:
            if not email or "@" not in email:
                st.error("请先填写有效的邮箱地址")
            else:
                try:
                    from datetime import datetime as dt
                    from utils.send_email import send_email
                    from utils.analysis_runner import run_stock_analysis
                    from utils.report_exporter import render_analysis_report_html
                    import tempfile
                    import os

                    # 1. 组装分析参数
                    today = dt.now().strftime("%Y-%m-%d")
                    # 分析师类型映射
                    analyst_map = {
                        "市场分析师": "market",
                        "社交媒体分析师": "social",
                        "新闻分析师": "news",
                        "基本面分析师": "fundamentals"
                    }
                    analysts = [analyst_map[a] for a in selected_analysts if a in analyst_map]

                    # 2. 执行分析
                    st.info("正在执行股票分析并生成报告，请稍候...")
                    results = run_stock_analysis(
                        stock_symbol=stock_symbol,
                        analysis_date=today,
                        analysts=analysts,
                        research_depth=research_depth,
                        llm_provider=llm_provider,
                        llm_model=llm_model,
                        market_type=market_type
                    )

                    # 3. 生成HTML报告和Markdown报告
                    html = render_analysis_report_html(results)
                    from utils.report_exporter import render_analysis_report_markdown
                    try:
                        import markdown2
                        md_html = markdown2.markdown(render_analysis_report_markdown(results))
                    except Exception:
                        md_html = render_analysis_report_markdown(results)

                    # 4. 生成PDF报告（复用 docker_pdf_adapter 逻辑）
                    pdf_path = None
                    pdf_error = None
                    try:
                        import pypandoc
                        from utils.docker_pdf_adapter import get_docker_pdf_extra_args, setup_xvfb_display
                        setup_xvfb_display()
                        extra_args = get_docker_pdf_extra_args()
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
                            output = pypandoc.convert_text(
                                html,
                                'pdf',
                                format='html',
                                outputfile=pdf_file.name,
                                extra_args=extra_args
                            )
                            pdf_path = pdf_file.name
                    except Exception as e:
                        pdf_error = str(e)
                        # 降级为 HTML 附件
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as html_file:
                            html_file.write(html)
                            pdf_path = html_file.name

                    # 5. 发送邮件（正文+附件）
                    mail_content = md_html
                    if pdf_error:
                        mail_content = (
                            f"<div style='color:red'><b>⚠️ PDF生成失败：{pdf_error}</b><br>已自动附上 HTML 报告，请用浏览器打开附件。</div>"
                            + md_html
                        )
                    send_email(
                        subject=f"【TradingAgents】{market_type}{stock_symbol} 分析报告（测试邮件）",
                        content=mail_content,
                        to_addr=email,
                        attachment_path=pdf_path
                    )
                    if pdf_error:
                        st.warning(f"PDF生成失败，已自动发送 HTML 附件：{pdf_error}")
                    else:
                        st.success(f"测试邮件（含分析报告PDF）已发送到 {email}，请查收（如未收到请检查垃圾箱）")
                    # 清理临时文件
                    if pdf_path and os.path.exists(pdf_path):
                        os.remove(pdf_path)
                except Exception as e:
                    st.error(f"发送失败：{e}")

    # 删除功能
    if monitor_config:
        st.markdown("---")
        st.markdown("#### 管理监控列表")
        for idx, item in enumerate(monitor_config):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"{idx+1}. **{item['market_type']}** | 代码: `{item['stock_symbol']}` | 深度: {item['research_depth']} | 团队: {', '.join(item['selected_analysts'])} | 邮箱: {item['email']} | 频率: {item.get('frequency', '每日')} | 时间: {item.get('send_time', '08:00')}"
                )
            with col2:
                if st.button("删除", key=f"del_{idx}"):
                    monitor_config.pop(idx)
                    st.session_state['monitor_config'] = monitor_config
                    st.success("已删除该监控项")
                    st.rerun()

    # 保存按钮
    if st.button("💾 保存所有监控配置"):
        st.session_state['monitor_config_saved'] = True
        st.success("监控配置已保存（仅本地/会话，后续可持久化到文件）")

    # 🚀 测试 Celery 任务按钮
    st.markdown("---")
    st.markdown("#### Celery 任务测试")
    if st.button("🚀 测试 Celery 任务", help="读取配置文件并异步触发 celery 监控任务"):
        try:
            import yaml
            import os
            # K8s 挂载后路径
            config_path = "/app/web/monitor_config.yaml"
            if not os.path.exists(config_path):
                config_path = "web/monitor_config.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                conf = yaml.safe_load(f)
            if not conf:
                st.error("配置文件为空，无法触发任务")
            else:
                from web.tasks.monitor_tasks import monitor_and_send_task
                # 支持多条配置分别触发 celery 任务
                if isinstance(conf, list):
                    task_ids = []
                    for idx, item in enumerate(conf):
                        result = monitor_and_send_task.delay(item)
                        task_ids.append(result.id)
                        st.success(f"Celery 任务已提交，第{idx+1}条，task_id: {result.id}")
                else:
                    result = monitor_and_send_task.delay(conf)
                    st.success(f"Celery 任务已提交，task_id: {result.id}")
        except Exception as e:
            st.error(f"Celery 任务触发失败：{e}")

    return monitor_config
