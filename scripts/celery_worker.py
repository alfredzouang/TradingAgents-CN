"""
Celery worker 启动脚本
用法：python scripts/celery_worker.py
或 celery -A web.tasks.monitor_tasks.celery_app worker --loglevel=info
"""

from web.tasks.monitor_tasks import celery_app

if __name__ == "__main__":
    celery_app.worker_main()
