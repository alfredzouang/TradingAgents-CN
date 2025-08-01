"""
每日股票监控分析并邮件发送任务
用法：python scripts/daily_monitor_task.py
需配置 SMTP 相关环境变量，monitor_config.yaml 由前端页面维护
"""

import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# 项目根目录加入 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml

# 导入分析和邮件工具
from web.utils.analysis_runner import run_stock_analysis
from web.utils.send_email import send_email
from web.tasks.monitor_tasks import monitor_and_send_task

# 监控配置文件路径
CONFIG_FILE = project_root / "monitor_config.yaml"

def load_monitor_config():
    if not CONFIG_FILE.exists():
        print(f"[ERROR] 配置文件不存在: {CONFIG_FILE}")
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []

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

def should_send_today(conf, now):
    """
    判断今天是否应发送分析报告
    支持 frequency: 每日、每3天、每5天、交易日
    支持 send_time: "08:00"、"21:00" 等
    """
    freq = conf.get("frequency", "每日")
    send_time = conf.get("send_time", "08:00")
    # 时间判断
    try:
        send_hour, send_minute = map(int, send_time.split(":"))
    except Exception:
        send_hour, send_minute = 8, 0
    # 只在指定时间点的±10分钟内执行
    if not (now.hour == send_hour and abs(now.minute - send_minute) <= 10):
        return False

    # 频率判断
    if freq == "每日":
        return True
    elif freq == "每3天":
        # 以配置文件创建日为基准，每3天一次
        base_day = conf.get("base_day")
        if not base_day:
            conf["base_day"] = now.strftime("%Y-%m-%d")
            return True
        delta = (now.date() - datetime.strptime(conf["base_day"], "%Y-%m-%d").date()).days
        return delta % 3 == 0
    elif freq == "每5天":
        base_day = conf.get("base_day")
        if not base_day:
            conf["base_day"] = now.strftime("%Y-%m-%d")
            return True
        delta = (now.date() - datetime.strptime(conf["base_day"], "%Y-%m-%d").date()).days
        return delta % 5 == 0
    elif freq == "交易日":
        # 简单判断：周一到周五
        return now.weekday() < 5
    else:
        return True

def main():
    configs = load_monitor_config()
    if not configs:
        print("[INFO] 无监控配置，任务结束。")
        return

    now = datetime.now()
    updated = False

    for idx, conf in enumerate(configs):
        try:
            if not should_send_today(conf, now):
                continue
            # 直接异步分发 celery 任务
            result = monitor_and_send_task.delay(conf)
            print(f"[{idx+1}/{len(configs)}] Celery 任务已提交，task_id: {result.id}")
            updated = True
        except Exception as e:
            print(f"[ERROR] {conf.get('stock_symbol', '')} celery 任务分发失败: {e}")
            traceback.print_exc()

    # 若有 base_day 字段更新，持久化配置
    if updated:
        try:
            import yaml
            project_root = Path(__file__).parent.parent
            CONFIG_FILE = project_root / "monitor_config.yaml"
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(configs, f, allow_unicode=True)
        except Exception as e:
            print(f"[WARN] base_day 持久化失败: {e}")

if __name__ == "__main__":
    main()
