"""
Implements an abstraction layer for search terms.

Kevin Ni, kevin.ni@nyu.edu.
"""


class WokSearchConditionBlock:
    def __init__(self, translator_name: str):
        self.translator_name = translator_name


class WokSearchCondition:
    def __init__(self, name: str, condition_block: WokSearchConditionBlock):
        self.name: str = name
        self.condition_block = condition_block


class WokSearchTerm:
    def __init__(self):
        self.conditions = []
