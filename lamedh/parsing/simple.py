from functools import reduce
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree

from lamedh.expr import Expr, Lam, App, Var
from lamedh.expr.applicative import (
    BooleanConstant, NaturalConstant, UnaryOp, BinaryOp, IfThenElse, Error, TypeError,
    UnaryOpTable, BinaryOpTable
)

unary_symbols = ' | '.join(map(lambda s:'"%s"'%s, UnaryOpTable.symbols()))
binary_symbols = ' | '.join(map(lambda s:'"%s"'%s, BinaryOpTable.symbols()))

grammar = f"""
?start: app

?app: error
    | const
    | unary_op
    | binary_op
    | ifthenelse
    | lam
    | app " "* lam
    | app " "* app
    | "(" app ")"
    | var

lam: LAMBDA _bounds "." app

_bounds : var+
ifthenelse: "if" app "then" app "else" app
var: NAME
const: BOOL | NATURAL
unary_op: UNARY_OP app
binary_op: app BIN_OP app
error: ERRORS

ERRORS: "error" | "typeerror"
BOOL: "true" | "false"
NATURAL: /[0-9]+/
UNARY_OP: {unary_symbols}
BIN_OP: {binary_symbols}

LAMBDA: "λ" | "lambda" | "/"
%import common.CNAME -> NAME

%ignore /\\s+/
"""


class ParseLambdaVisitor:

     def __init__(self) -> None:
          self.parser = Lark(grammar, start='start', parser='earley')

     def parse(self, text):
          tree = self.parser.parse(text)
          return self.visit(tree)

     def visit(self, node):
          if isinstance(node, Tree):
               visited_children = [self.visit(c) for c in node.children]
               assert isinstance(node.data, Token)
               assert node.data.type == 'RULE'
               custom_visit_method = 'visit_' + node.data.value
               method = getattr(self, custom_visit_method, self.generic_visit)
               return method(node, visited_children)
          else:
               return node

     def generic_visit(self, node, visited_children):
          return visited_children[0]

     def visit_var(self, node, visited_children):
          assert len(visited_children) == 1
          token = visited_children[0]
          assert isinstance(token, Token)
          return Var(token.value)

     def visit_app(self, node, visited_children):
          return App(visited_children[0], visited_children[1])

     def visit_lam(self, node, visited_children):
          _, *vars, body = visited_children
          vars.reverse()
          exp = reduce(lambda body,v : Lam(v.var_name, body), vars, body)
          return exp

     # -- Applicative productions
     def visit_const(self, node, visited_children):
          klass_dict = {'NATURAL': NaturalConstant, 'BOOL': BooleanConstant}
          assert len(visited_children) == 1
          token = visited_children[0]
          assert isinstance(token, Token)
          assert token.type in klass_dict
          return klass_dict[token.type](token.value)

     def visit_unary_op(self, node, visited_children):
          assert len(visited_children) == 2
          op_symbol_token, sub_expr = visited_children
          assert isinstance(op_symbol_token, Token)
          assert isinstance(sub_expr, Expr)
          assert op_symbol_token.value in UnaryOpTable.symbols()
          return UnaryOp(
               UnaryOpTable[op_symbol_token.value],
               sub_expr
          )

     def visit_binary_op(self, node, visited_children):
          assert len(visited_children) == 3
          sub_expr_a, op_symbol_token, sub_expr_b = visited_children
          assert isinstance(op_symbol_token, Token)
          assert isinstance(sub_expr_a, Expr)
          assert isinstance(sub_expr_b, Expr)
          assert op_symbol_token.value in BinaryOpTable.symbols()
          return BinaryOp(
               BinaryOpTable[op_symbol_token.value],
               sub_expr_a,
               sub_expr_b
          )

     def visit_ifthenelse(self, node, visited_children):
          assert len(visited_children) == 3
          guard, then_expr, else_expr = visited_children
          assert isinstance(guard, Expr)
          assert isinstance(then_expr, Expr)
          assert isinstance(else_expr, Expr)
          return IfThenElse(
               guard,
               then_expr,
               else_expr
          )

     def visit_error(self, node, visited_children):
          assert len(visited_children) == 1, visited_children
          token = visited_children[0]
          assert isinstance(token, Token)
          assert token.type == 'ERRORS'
          if token.value == 'error':
               return Error()
          elif token.value == 'typeerror':
               return TypeError()
          else:
               raise ValueError(token.value)


parser = ParseLambdaVisitor()
