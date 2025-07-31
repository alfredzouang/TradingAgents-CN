"""
Celery beat 动态调度脚本
用法：python scripts/celery_beat.py
自动根据 monitor_config.yaml 生成定时任务
"""

import os
import sys
from pathlib import Path
import yaml
from datetime import datetime
from celery import Celery
from celery.schedules import crontab

# 导入 celery_app 和任务
from web.tasks.monitor_tasks import celery_app, monitor_and_send_task

# 配置文件路径
project_root = Path(__file__).parent.parent
CONFIG_FILE = project_root / "monitor_config.yaml"

def parse_cron_from_config(conf):
    """
    根据 frequency 和 send_time 生成 crontab schedule
    """
    freq = conf.get("frequency", "每日")
    send_time = conf.get("send_time", "08:00")
    try:
        hour, minute = map(int, send_time.split(":"))
    except Exception:
        hour, minute = 8, 0

    if freq == "每日":
        return crontab(minute=minute, hour=hour)
    elif freq == "每3天":
        # celery crontab 不支持“每3天”，用每天调度，task 内部判断
        return crontab(minute=minute, hour=hour)
    elif freq == "每5天":
        return crontab(minute=minute, hour=hour)
    elif freq == "交易日":
        # 周一到周五
        return crontab(minute=minute, hour=hour, day_of_week="1-5")
    else:
        return crontab(minute=minute, hour=hour)

def build_beat_schedule():
    """
    动态生成 celery beat_schedule
    """
    if not CONFIG_FILE.exists():
        print(f"[WARN] 配置文件不存在: {CONFIG_FILE}")
        return {}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        configs = yaml.safe_load(f) or []

    schedule = {}
    for idx, conf in enumerate(configs):
        task_name = f"monitor_and_send_{conf.get('stock_symbol', 'unknown')}_{idx}"
        schedule[task_name] = {
            "task": "web.tasks.monitor_tasks.monitor_and_send_task",
            "schedule": parse_cron_from_config(conf),
            "args": (conf,)
        }
    return schedule

def main():
    celery_app.conf.beat_schedule = build_beat_schedule()
    celery_app.conf.timezone = "Asia/Shanghai"
    celery_app.start(argv=["celery", "beat", "-l", "info"])

if __name__ == "__main__":
    main()
