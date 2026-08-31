# coding=utf-8
"""
    @project: dianxin
    @project: dianxin虎
    @file： model.py
    @date：2025/11/5 15:14
    @desc:
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telecom_ai_agent.settings')

application = get_wsgi_application()
