# -*- coding: utf-8 -*-
#
import os

from dotenv import load_dotenv

from .conf import ConfigManager
from .env import get_env, has_env

__all__ = ['BASE_DIR', 'PROJECT_DIR', 'VERSION', 'CONFIG']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = get_env('MAXKB_LOG_DIR', os.path.join('/', 'opt', 'jb-agent', 'logs'))
PROJECT_DIR = os.path.dirname(BASE_DIR)
VERSION = '2.0.0'

# load environment variables from .env file
load_dotenv()
# print(get_env('MAXKB_CONFIG'))
if has_env('MAXKB_CONFIG'):
    CONFIG = ConfigManager.load_user_config(root_path=PROJECT_DIR)
else:
    CONFIG = ConfigManager.load_user_config(
        root_path=get_env('MAXKB_CONFIG_DIR', os.path.abspath('/opt/jb-agent/conf'))
    )
