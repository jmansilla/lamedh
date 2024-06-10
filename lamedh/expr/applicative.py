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

    def children(self):
        return []

    def __repr__(self):
        return '<Error>'

    def __str__(self):
        return 'error'


class TypeError(Expr):
    def __repr__(self):
        return '<TypeError>'

    def __str__(self):
        return 'typeerror'

    def children(self):
        return []


class BooleanConstant(Expr):
    kind = ConstType.Boolean

    def __init__(self, value):
        self.parent = None
        self.value = value

    def children(self):
        return []

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


class Tuple(Expr):
    def __init__(self, elems):
        self.elems = []
        self.parent = None
        for elem in elems:
            assert isinstance(elem, Expr)
            elem.parent = self
            self.elems.append(elem)

    def children(self):
        return self.elems[:]

    def __repr__(self):
        args = ', '.join(map(repr, self.elems))
        return f'<Tuple:{args}>'

    def __str__(self):
        args = ', '.join(map(str, self.elems))
        return f'<{args}>'


class Indexing(Expr):
    def __init__(self, container, index):
        assert isinstance(container, Expr)
        assert isinstance(index, Expr)
        container.parent = self
        index.parent = self
        self.container = container
        self.index = index

    def children(self):
        return [self.container, self.index]

    def __repr__(self):
        return f'(Indexing:{repr(self.container)}.{repr(self.index)})'

    def __str__(self):
        return f'({self.container}.{self.index})'



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

    def __repr__(self):
        if self.var:
            return repr(self.var)
        else:
            args = ', '.join(repr(x) for x in self.sub_patterns)
            return f'<{args}>'


    def __str__(self):
        if self.var:
            return str(self.var)
        else:
            args = ', '.join(str(x) for x in self.sub_patterns)
            return f'<{args}>'

class LetIn(Expr):
    def __init__(self, definitions, in_expr):
        patterns, sub_exprs = zip(*definitions)
        assert isinstance(patterns, tuple), type(patterns)
        assert isinstance(sub_exprs, tuple)
        assert isinstance(in_expr, Expr)
        self.parent = None
        self.in_expr = in_expr
        self.in_expr.parent = self
        self.patterns = []
        for _pattern, sub_expr in zip(patterns, sub_exprs):
            assert isinstance(sub_expr, Expr)
            pattern = Pattern(_pattern)
            pattern.parent = self
            self.patterns.append(pattern)
            sub_expr.parent = self
        self.sub_exprs = sub_exprs

    def children(self):
        return [self.in_expr] + [self.values][:]

    def to_string(self, func=str, verbose=False):
        args = ', '.join(
            f'{func(pattern)}:={func(sub_expr)}' for pattern, sub_expr in zip(self.patterns, self.sub_exprs))
        if verbose:
            name = f'{self.__class__.__name__}: '
        else:
            name = 'let '
        return f'({name}{args} in {func(self.in_expr)})'

    def __repr__(self):
        return self.to_string(repr)

    def __str__(self):
        return self.to_string(str)


