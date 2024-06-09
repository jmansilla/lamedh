from enum import Enum
from typing import Any
from lamedh.expr import Expr
from lamedh.bidict import NameSymbolMap

ConstType = Enum('ConstType', ['Natural', 'Boolean'])


UnaryOpTable = NameSymbolMap({'-': 'Negative', 'not': 'Not'})
BinaryOpTable = NameSymbolMap({
    '+': 'Sum',
    '-': 'Minus',
    '*': 'Times',
    '/': 'Div',
    '%': 'Reminder',
    '==': 'Equal',
    '!=': 'NotEqual',
    '<': 'LessThan',
    '<=': 'LessThanEqual',
    '>': 'MoreThan',
    '>=': 'MoreThanEqual',
    'or': 'Or',
    'and': 'And',
    'implies': 'Implies',
    '<==>': 'IfOnlyIf'
})


class Error(Expr):

    def __repr__(self):
        return '<Error>'

    def __str__(self):
        return 'error'


class TypeError(Expr):
    def __repr__(self):
        return '<TypeError>'

    def __str__(self):
        return 'typeerror'


class BooleanConstant(Expr):
    kind = ConstType.Boolean

    def __init__(self, value):
        self.parent = None
        self.value = value

    def __repr__(self):
        type_name = self.kind.name.capitalize()
        return f'<Constant({type_name}):{self.value}>'

    def __str__(self):
        return str(self.value)


class NaturalConstant(BooleanConstant):
    kind = ConstType.Natural


class UnaryOp(Expr):
    def __init__(self, operator, operand):
        assert operator in UnaryOpTable.names()
        assert isinstance(operand, Expr)
        self.parent = None
        self.operator = operator
        self.operand = operand
        operand.parent = self

    def children(self):
        return [self.operand]

    @property
    def operator_symbol(self):
        return UnaryOpTable.symbol_of(self.operator)

    def __repr__(self):
        return f'UnaryOp({repr(self.operator_symbol)} {repr(self.operand)})'

    def __str__(self):
        return f'({self.operator_symbol} {self.operand})'


class BinaryOp(Expr):
    def __init__(self, operator, left, right):
        assert operator in BinaryOpTable.names()
        assert isinstance(left, Expr)
        assert isinstance(right, Expr)
        self.parent = None
        self.operator = operator
        self.left = left
        self.left.parent = self
        self.right = right
        self.right.parent = self

    def children(self):
        return [self.left, self.right]

    @property
    def operator_symbol(self):
        return BinaryOpTable.symbol_of(self.operator)

    def __repr__(self):
        return f'BinaryOp({repr(self.left)} {repr(self.operator_symbol)} {repr(self.right)})'

    def __str__(self):
        return f'({self.left} {self.operator_symbol} {self.right})'


class IfThenElse(Expr):
    def __init__(self, guard, then_body, else_body):
        for name, variable in [('guard', guard), ('then_body', then_body), ('else_body', else_body)]:
            assert isinstance(variable, Expr)
            variable.parent = self
            setattr(self, name, variable)
        self.parent = None

    def children(self):
        return [self.guard, self.then_body, self.else_body]

    def __repr__(self):
        return f'(If {repr(self.guard)} Then {repr(self.then_body)} Else {repr(self.else_body)})'

    def __str__(self):
        return f'(If {self.guard} Then {self.then_body} Else {self.else_body})'
