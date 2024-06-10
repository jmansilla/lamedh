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
        self.value = value

    def __repr__(self):
        name = self.__class__.__name__
        return f'<{name}:{self.value}>'

    def __str__(self):
        return str(self.value)


class NaturalConstant(BooleanConstant):
    kind = ConstType.Natural


class UnaryOp(Expr):
    def __init__(self, operator, operand):
        assert operator in UnaryOpTable.names()
        self.operator = operator
        self.operand = operand

    def children(self):
        return [self.operand]

    @property
    def operator_symbol(self):
        return UnaryOpTable.symbol_of(self.operator)

    def to_string(self, func, name=''):
        return f'{name}({func(self.operator_symbol)} {func(self.operand)})'


class BinaryOp(Expr):
    def __init__(self, operator, left, right):
        assert operator in BinaryOpTable.names()
        self.operator = operator
        self.left = left
        self.right = right

    def children(self):
        return [self.left, self.right]

    @property
    def operator_symbol(self):
        return BinaryOpTable.symbol_of(self.operator)

    def to_string(self, func, name=''):
        return f'{name}({func(self.left)} {func(self.operator_symbol)} {func(self.right)})'


class IfThenElse(Expr):
    def __init__(self, guard, then_body, else_body):
        self.guard = guard
        self.then_body = then_body
        self.else_body = else_body

    def children(self):
        return [self.guard, self.then_body, self.else_body]

    def to_string(self, func, name=''):
        return f'(If {func(self.guard)} Then {func(self.then_body)} Else {func(self.else_body)})'


class Tuple(Expr):
    def __init__(self, elems):
        self.elems = elems[:]

    def children(self):
        return self.elems[:]

    def to_string(self, func, name=''):
        args = ', '.join(map(func, self.elems))
        if name: name += ':'
        return f'<{name}{args}>'


class Indexing(Expr):
    def __init__(self, container, index):
        self.container = container
        self.index = index

    def children(self):
        return [self.container, self.index]

    def to_string(self, func, name=''):
        if name: name+=':'
        return f'({name}{func(self.container)}.{func(self.index)})'


class Pattern:
    # a pattern may be a Var or a sequence of Patterns
    var = None
    sub_patterns = None
    def __init__(self, var_or_pattern):
        from lamedh.expr import Var
        if isinstance(var_or_pattern, Var):
            self.var = var_or_pattern
        else:
            self.sub_patterns = [Pattern(p) for p in var_or_pattern]

    def to_string(self, func, name=''):
        if self.var:
            return func(self.var)
        else:
            args = ', '.join(func(x) for x in self.sub_patterns)
            return f'<{args}>'

    def __repr__(self):
        name = self.__class__.__name__
        return self.to_string(repr, name)

    def __str__(self):
        return self.to_string(str)


class LetIn(Expr):
    def __init__(self, definitions, in_expr):
        patterns, sub_exprs = zip(*definitions)
        assert isinstance(patterns, tuple)
        assert isinstance(sub_exprs, tuple)
        self.in_expr = in_expr
        self.patterns = [Pattern(p) for p in patterns]
        self.sub_exprs = sub_exprs

    def children(self):
        yield self.in_expr
        for child in self.sub_exprs:
            yield child

    def to_string(self, func, name=''):
        args = ', '.join(
            f'{func(pattern)}:={func(sub_expr)}' for pattern, sub_expr in zip(self.patterns, self.sub_exprs))
        return f'({name}{args} in {func(self.in_expr)})'

    def __str__(self):
        return self.to_string(str, 'let ')


