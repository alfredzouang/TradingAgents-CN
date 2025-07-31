"""
Celery 任务：单条股票监控分析与邮件发送
"""

from celery import Celery
import os
from pathlib import Path
from datetime import datetime

import yaml

from web.utils.analysis_runner import run_stock_analysis, format_analysis_results
from web.utils.send_email import send_email
from web.utils.report_exporter import render_analysis_report_html, render_analysis_report_markdown
import tempfile

import tushare as ts
import pytz

# Celery app（由 celery_worker.py 导入时初始化）
celery_app = Celery("monitor_tasks")
celery_app.config_from_object("web.celeryconfig")

def format_report(result):
    """生成简明HTML分析报告"""
    if not result.get("success"):
        return f"<h3>股票分析失败</h3><p>{result.get('error')}</p>"
    d = result.get("decision", {})
    state = result.get("state", {})
    html = f"""
    <h2>股票分析报告 - {result.get('stock_symbol')}</h2>
    <ul>
      <li><b>分析日期:</b> {result.get('analysis_date')}</li>
      <li><b>投资建议:</b> {d.get('action', '无')}</li>
      <li><b>置信度:</b> {d.get('confidence', '')}</li>
      <li><b>目标价:</b> {d.get('target_price', '')}</li>
      <li><b>风险分数:</b> {d.get('risk_score', '')}</li>
    </ul>
    <h3>主要结论</h3>
    <div>{d.get('reasoning', '')}</div>
    <hr>
    <h3>风险评估</h3>
    <div>{state.get('risk_assessment', '')}</div>
    """
    return html

def get_market_local_date(market_type):
    """
    获取指定市场的本地日期（YYYY-MM-DD）
    """
    if market_type == "A股":
        tz = pytz.timezone("Asia/Shanghai")
    elif market_type == "港股":
        tz = pytz.timezone("Asia/Hong_Kong")
    elif market_type == "美股":
        tz = pytz.timezone("America/New_York")
    else:
        tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz).strftime("%Y-%m-%d")

def is_trade_day(market_type, date_str):
    """
    判断指定市场在指定日期是否为交易日
    market_type: "A股"、"港股"、"美股"
    date_str: "YYYY-MM-DD"
    返回: True/False
    """
    tushare_token = os.getenv("TUSHARE_TOKEN")
    if not tushare_token:
        raise RuntimeError("TUSHARE_TOKEN 环境变量未配置，无法判断交易日。")
    pro = ts.pro_api(tushare_token)
    date_fmt = date_str.replace("-", "")
    if market_type == "A股":
        # 默认上交所
        df = pro.trade_cal(exchange='', start_date=date_fmt, end_date=date_fmt)
        if df.empty:
            return False
        return str(df.iloc[0]["is_open"]) == "1"
    elif market_type == "港股":
        df = pro.hk_tradecal(start_date=date_fmt, end_date=date_fmt)
        if df.empty:
            return False
        return str(df.iloc[0]["is_open"]) == "1"
    elif market_type == "美股":
        df = pro.us_tradecal(start_date=date_fmt, end_date=date_fmt)
        if df.empty:
            return False
        return str(df.iloc[0]["is_open"]) == "1"
    else:
        # 其他市场默认视为非交易日
        return False

@celery_app.task(queue="monitor_serial")
def monitor_and_send_task(conf):
    """
    单条监控配置的分析与邮件发送任务
    conf: dict，包含 market_type, stock_symbol, research_depth, selected_analysts, email, 等
    """
    try:
        stock_type = conf.get("market_type", "A股")
        stock_code = conf.get("stock_symbol")
        research_depth = int(conf.get("research_depth", 3))
        analysts = conf.get("selected_analysts", ["市场分析师", "基本面分析师"])
        # 分析师类型映射（与前端保持一致）
        analyst_map = {
            "市场分析师": "market",
            "社交媒体分析师": "social",
            "新闻分析师": "news",
            "基本面分析师": "fundamentals"
        }
        # 若 analysts 为中文，需映射为英文 code
        mapped_analysts = []
        for a in analysts:
            if a in analyst_map:
                mapped_analysts.append(analyst_map[a])
            else:
                mapped_analysts.append(a)  # 兼容已为英文 code 的情况
        analysts = mapped_analysts
        email_addr = conf.get("email")
        # 支持多个邮箱（逗号分隔或列表）
        if isinstance(email_addr, str):
            email_addr = [e.strip() for e in email_addr.split(",") if e.strip()]
        elif not isinstance(email_addr, list):
            email_addr = [str(email_addr)]
        # 获取市场本地日期
        analysis_date = get_market_local_date(stock_type)

        # 新增：仅交易日发送判断
        if conf.get("send_on_trade_day"):
            try:
                if not is_trade_day(stock_type, analysis_date):
                    return f"[SKIP] {stock_code} {stock_type} {analysis_date} 非交易日，未发送。"
            except Exception as e:
                return f"[ERROR] {stock_code} 交易日判断失败: {e}"

        llm_provider = os.getenv("LLM_PROVIDER", "dashscope")
        llm_model = os.getenv("LLM_MODEL", "qwen-plus")

        # 1. 执行分析
        result = run_stock_analysis(
            stock_symbol=stock_code,
            analysis_date=analysis_date,
            analysts=analysts,
            research_depth=research_depth,
            llm_provider=llm_provider,
            llm_model=llm_model,
            market_type=stock_type
        )

        # 2. 格式化为 markdown 和 html
        formatted = format_analysis_results(result)
        html_report = render_analysis_report_html(formatted)
        try:
            import markdown2
            md_html = markdown2.markdown(render_analysis_report_markdown(formatted))
        except Exception:
            md_html = render_analysis_report_markdown(formatted)

        # 3. 邮件发送正文（不再附加 PDF/HTML 附件）
        mail_content = md_html
        subject = f"【股票监控】{stock_type} {stock_code} 分析报告 {analysis_date}"
        send_email(subject, mail_content, email_addr)
        return f"[OK] {stock_code} 分析并发送成功。"
    except Exception as e:
        import traceback
        stock_code = conf.get("stock_symbol", "")
        stock_type = conf.get("market_type", "A股")
        analysis_date = get_market_local_date(stock_type)
        email_addr = conf.get("email")
        # 支持多个邮箱（逗号分隔或列表）
        if isinstance(email_addr, str):
            email_addr = [e.strip() for e in email_addr.split(",") if e.strip()]
        elif not isinstance(email_addr, list):
            email_addr = [str(email_addr)]
        tb = traceback.format_exc()
        subject = f"【股票监控告警】{stock_type} {stock_code} 分析失败 {analysis_date}"
        content = (
            f"<h3>股票监控定时任务执行失败</h3>"
            f"<ul>"
            f"<li><b>市场:</b> {stock_type}</li>"
            f"<li><b>股票代码:</b> {stock_code}</li>"
            f"<li><b>日期:</b> {analysis_date}</li>"
            f"<li><b>错误信息:</b> {e}</li>"
            f"</ul>"
            f"<h4>详细日志：</h4>"
            f"<pre style='color:red'>{tb}</pre>"
        )
        try:
            send_email(subject, content, email_addr)
        except Exception as mail_e:
            # 邮件发送失败也要返回日志
            return f"[ERROR] {stock_code} 处理失败: {e}\n邮件告警发送失败: {mail_e}\n{tb}"
        return f"[ERROR] {stock_code} 处理失败: {e}\n{tb}"
