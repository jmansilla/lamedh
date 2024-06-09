from enum import Enum
from lamedh.expr import Expr


ConstType = Enum('ConstType', ['Natural', 'Boolean'])


class Error(Expr):
    pass


class TypeError(Expr):
    pass


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
        self.parent = None
        assert isinstance(operator, Expr)
        assert isinstance(operand, Expr)
        self.operator = operator
        self.operand = operand
        operator.parent = self
        operand.parent = self

    def children(self):
        return [self.operator, self.operand]

    def __repr__(self):
        return f'UnaryOp({repr(self.operator)} {repr(self.operand)})'

    def __str__(self):
        return f'({self.operator} {self.operand})'


class BinaryOp(Expr):
    pass


class IfThenElse(Expr):
    pass