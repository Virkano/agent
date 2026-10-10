# coding=utf-8
"""
    @project: dianxin
    @project: dianxin
    @file： __init__.py
    @date：2024/3/14 11:54
    @desc:
"""
from . import clean_chat_job, clean_debug_file_job, client_access_num_job
from marketing import jobs as marketing_alert_jobs
from models_provider import pipeline_jobs as model_pipeline_jobs
from platform_monitoring import jobs as platform_monitoring_jobs


def run():
    # client_access_num_job.run()
    clean_chat_job.run()
    clean_debug_file_job.run()
    client_access_num_job.run()
    marketing_alert_jobs.run()
    model_pipeline_jobs.run()
    platform_monitoring_jobs.run()
