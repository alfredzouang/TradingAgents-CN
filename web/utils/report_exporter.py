"""
分析报告导出工具：将分析结果渲染为完整HTML，便于邮件正文和PDF导出
"""

from datetime import datetime

import streamlit as st

def render_export_buttons(results):
    """渲染导出按钮，支持导出分析报告为HTML文件"""
    html = render_analysis_report_html(results)
    st.download_button(
        label="导出分析报告为HTML",
        data=html,
        file_name=f"{results.get('stock_symbol', 'report')}_analysis_{results.get('analysis_date', '')}.html",
        mime="text/html"
    )

def render_analysis_report_markdown(results):
    """将分析结果渲染为简洁Markdown（适用于邮件正文/纯文本）"""
    if not results or not results.get("success"):
        return "## 暂无分析结果"

    stock_symbol = results.get('stock_symbol', 'N/A')
    decision = results.get('decision', {})
    state = results.get('state', {})
    is_demo = results.get('is_demo', False)

    # 投资决策摘要
    action = decision.get('action', 'N/A')
    confidence = decision.get('confidence', 0)
    risk_score = decision.get('risk_score', 0)
    target_price = decision.get('target_price', '待分析')
    reasoning = decision.get('reasoning', '')

    # 分析配置信息
    analysis_date = results.get('analysis_date', '')
    analysts = results.get('analysts', [])
    research_depth = results.get('research_depth', '')
    llm_provider = results.get('llm_provider', '')
    llm_model = results.get('llm_model', '')

    md = f"""# {stock_symbol} 分析报告

**分析日期**: {analysis_date}  
**分析师团队**: {', '.join(analysts) if analysts else 'N/A'}  
**研究深度**: {research_depth}  
**LLM**: {llm_provider} / {llm_model}  

## 投资建议
- **操作**: {action}
- **置信度**: {confidence:.1%}
- **风险评分**: {risk_score:.1%}
- **目标价位**: {target_price if target_price else '待分析'}

## AI分析推理
{reasoning}

## 详细分析报告
"""

    def section(title, content):
        if content:
            return f"### {title}\n{content}\n"
        return ""

    md += section('📈 市场技术分析', state.get('market_report'))
    md += section('💰 基本面分析', state.get('fundamentals_report'))
    md += section('💭 市场情绪分析', state.get('sentiment_report'))
    md += section('📰 新闻事件分析', state.get('news_report'))
    md += section('⚠️ 风险评估', state.get('risk_assessment'))
    md += section('📋 投资建议', state.get('investment_plan'))

    md += """
---

> ⚠️ **投资风险提示**  
> 本分析结果仅供参考，不构成投资建议。股票投资有风险，可能导致本金损失。请结合多方信息理性决策，重大投资建议请咨询专业顾问。
"""

    if is_demo:
        md += "\n\n> 🎭 **演示模式**：当前为模拟数据，仅用于演示。\n"

    return md

def render_analysis_report_html(results):
    """将分析结果渲染为完整HTML（适用于邮件和PDF）"""
    if not results or not results.get("success"):
        return "<h2>暂无分析结果</h2>"

    stock_symbol = results.get('stock_symbol', 'N/A')
    decision = results.get('decision', {})
    state = results.get('state', {})
    is_demo = results.get('is_demo', False)

    # 投资决策摘要
    action = decision.get('action', 'N/A')
    confidence = decision.get('confidence', 0)
    risk_score = decision.get('risk_score', 0)
    target_price = decision.get('target_price', '待分析')
    reasoning = decision.get('reasoning', '')

    # 分析配置信息
    analysis_date = results.get('analysis_date', '')
    analysts = results.get('analysts', [])
    research_depth = results.get('research_depth', '')
    llm_provider = results.get('llm_provider', '')
    llm_model = results.get('llm_model', '')

    # 详细分析报告
    def section(title, content):
        if content:
            return f"<h3>{title}</h3><div>{content}</div>"
        return ""

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #fff; color: #222; }}
            h1, h2, h3 {{ color: #1f77b4; }}
            .summary-table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; }}
            .summary-table th, .summary-table td {{ border: 1px solid #ddd; padding: 8px; }}
            .summary-table th {{ background: #f0f2f6; }}
            .section {{ margin-bottom: 1.5em; }}
            .risk-warning {{ color: #b94a48; background: #f2dede; padding: 1em; border-radius: 6px; margin-top: 2em; }}
            .meta-info {{ color: #888; font-size: 0.95em; margin-bottom: 1em; }}
        </style>
    </head>
    <body>
        <h1>📊 {stock_symbol} 分析报告</h1>
        <div class="meta-info">
            <b>分析日期:</b> {analysis_date} &nbsp;|&nbsp;
            <b>分析师团队:</b> {', '.join(analysts) if analysts else 'N/A'} &nbsp;|&nbsp;
            <b>研究深度:</b> {research_depth} &nbsp;|&nbsp;
            <b>LLM:</b> {llm_provider} / {llm_model}
        </div>
        <table class="summary-table">
            <tr>
                <th>投资建议</th>
                <th>置信度</th>
                <th>风险评分</th>
                <th>目标价位</th>
            </tr>
            <tr>
                <td>{action}</td>
                <td>{confidence:.1%}</td>
                <td>{risk_score:.1%}</td>
                <td>{target_price if target_price else '待分析'}</td>
            </tr>
        </table>
        <div class="section">
            <h3>🧠 AI分析推理</h3>
            <div>{reasoning}</div>
        </div>
        <div class="section">
            <h2>📋 详细分析报告</h2>
            {section('📈 市场技术分析', state.get('market_report'))}
            {section('💰 基本面分析', state.get('fundamentals_report'))}
            {section('💭 市场情绪分析', state.get('sentiment_report'))}
            {section('📰 新闻事件分析', state.get('news_report'))}
            {section('⚠️ 风险评估', state.get('risk_assessment'))}
            {section('📋 投资建议', state.get('investment_plan'))}
        </div>
        <div class="risk-warning">
            <b>⚠️ 投资风险提示：</b><br>
            本分析结果仅供参考，不构成投资建议。股票投资有风险，可能导致本金损失。请结合多方信息理性决策，重大投资建议请咨询专业顾问。<br>
            <span style="color:#888;">分析生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
        {"<div class='risk-warning'><b>🎭 演示模式：</b> 当前为模拟数据，仅用于演示。</div>" if is_demo else ""}
    </body>
    </html>
    """
    return html
