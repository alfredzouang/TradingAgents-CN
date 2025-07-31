"""
Celery 配置文件
"""

import os

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
timezone = "Asia/Shanghai"
enable_utc = False

# 推荐在 .env/docker/k8s 环境变量中配置：
# CELERY_BROKER_URL=redis://redis:6379/0
# CELERY_RESULT_BACKEND=redis://redis:6379/1
# 以适配本地、容器、K8S等多环境
