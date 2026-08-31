# coding=utf-8
"""
    @project: dianxin
    @project: dianxin
    @file： compare.py
    @date：2024/6/7 14:37
    @desc:
"""
from abc import abstractmethod

class Compare:

    @abstractmethod
    def compare(self, source_value, compare, target_value):
        pass
