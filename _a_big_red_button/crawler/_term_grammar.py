"""
Implements a parser and a generator for the search term grammar.
Search term grammar is defined as follow:

    TERM := (TERM and TERM) |
            (TERM or TERM) |
            (not TERM) |
            (FULL_CONDITION) .
    FULL_CONDITION := (NAME = CONDITION_BLOCK) .
    CONDITION_BLOCK := (CONDITION_BLOCK and CONDITION_BLOCK) |
                       (CONDITION_BLOCK or CONDITION_BLOCK) |
                       (not CONDITION_BLOCK) |
                       CONDITION_VALUE .
    CONDITION_VALUE := [A STRING] .

    in which `and`, `or` and `not` are logical operators.

Kevin Ni, kevin.ni@nyu.edu.
"""

from typing import *
from enum import Enum


class _LogicalOperator(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    def __str__(self):
        return self.name


class _TermGrammarElement:
    _unary_operators = (_LogicalOperator.NOT,)
    _binary_operators = (_LogicalOperator.AND, _LogicalOperator.OR)

    def generate(self):
        raise NotImplementedError('this function should be implemented '
                                  'in subclasses')

    @staticmethod
    def wrap(term: str):
        return f'({term})'

    def __repr__(self):
        return self.generate()


__T = TypeVar('__T', bound='_TermSelfOrLogicalCombinationOfSelf')


class _PythonLogicalOperatorMixin:
    constructing_class: \
        Optional[Type['__T']] = None

    @property
    def _clz(self):
        if self.constructing_class is None:
            return type(self)
        return self.constructing_class

    def __or__(self, other):
        return self._clz(self, other, _LogicalOperator.OR)

    def __and__(self, other):
        return self._clz(self, other, _LogicalOperator.AND)

    def __neg__(self):
        return self._clz(self, _LogicalOperator.NOT)


class _TermSelfOrLogicalCombinationOfSelf(_TermGrammarElement):
    def __init__(self, left: '__T',
                 right: Optional['__T'] = None,
                 operator: Optional[_LogicalOperator] = None):
        self.left, self.right = left, right
        self.operator = operator

    def generate(self):
        if self.operator is None:
            return self.wrap(f'{self.left}')
        else:
            if self.operator in self._unary_operators:
                return self.wrap(f'{self.operator} {self.right}')
            else:
                assert self.right is not None
                return self.wrap(f'{self.left} {self.operator} {self.right}')


class _Term(_TermSelfOrLogicalCombinationOfSelf,
            _PythonLogicalOperatorMixin):
    pass


class _FullCondition(_Term):
    constructing_class = _Term

    def __init__(self, name: str, condition_body: '_ConditionBlock'):
        super(_FullCondition, self).__init__(self)
        self.name, self.condition_body = name, condition_body

    def generate(self):
        return self.wrap(f'{self.name}={self.condition_body}')


class _ConditionBlock(_TermSelfOrLogicalCombinationOfSelf,
                      _PythonLogicalOperatorMixin):
    @property
    def constructing_class(self) -> ClassVar['_ConditionBlock']:
        return _ConditionBlock.__class__

    def named(self, name: str):
        return _FullCondition(name, self)


class _ConditionValue(_ConditionBlock,
                      _PythonLogicalOperatorMixin):
    constructing_class = _ConditionBlock

    def __init__(self, value: Any):
        super(_ConditionValue, self).__init__(self)
        self.value = value

    def generate(self):
        return self.value


_CondVal = _ConditionValue

if __name__ == '__main__':
    print("make sure that this prints (TS=(Guangzhou AND (China OR PRC))):")
    f = _CondVal('Guangzhou')
    g = _CondVal('China') | _CondVal('PRC')
    h = f & g
    i = h.named("TS")
    print(i)
