# coding=utf-8
"""
    @project: dianxin-xpack
    @project: dianxin虎
    @file： __init__.py.py
    @date：2025/11/5 14:45
    @desc:
"""
import os

if os.environ.get('SERVER_NAME', 'web') == 'local_model':
    from .model import *
else:
    from .web import *
