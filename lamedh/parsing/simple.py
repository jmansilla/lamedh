from functools import reduce
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree

from lamedh.expr import Expr, Lam, App, Var
from lamedh.expr.applicative import (
    BooleanConstant, NaturalConstant, UnaryOp, BinaryOp, IfThenElse,
    Error, TypeError, Tuple, LetIn, Rec, LetRec,
    UnaryOpTable, BinaryOpTable
)

unary_symbols = ' | '.join(map(lambda s:'"%s"'%s, UnaryOpTable.symbols()))
binary_symbols = ' | '.join(map(lambda s:'"%s"'%s, BinaryOpTable.symbols()))

grammar = f"""
?start: app

?app: error
    | tuple
    | const
    | ifthenelse
    | letin
    | letrec
    | rec
    | unary_op
    | binary_op
    | lam
    | app " "* lam
    | app " "* app
    | "(" app ")"
    | var

lam: LAMBDA _bounds "." app

_bounds : var+
var: NAME

ifthenelse: "if" app "then" app "else" app

tuple: _tuple_def | tuple_indexing
_tuple_def: "<" app tuple_elem* ">"
tuple_elem: "," app
tuple_indexing: app "." NATURAL

pattern: var | "<" pattern pattern_elem* ">"
pattern_elem: "," pattern

letin: "let" local_var local_var_elem* "in" app
local_var: pattern ":=" app
local_var_elem: "," local_var

rec: "rec" app
letrec: "letrec" local_lam local_lam_elem* "in" app
local_lam: pattern ":=" lam
local_lam_elem: "," local_lam

error: ERRORS
ERRORS: "error" | "typeerror"

const: BOOL | NATURAL
BOOL: "true" | "false"
NATURAL: /[0-9]+/

unary_op: UNARY_OP app
binary_op: app BIN_OP app
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

     def visit_tuple(self, node, visited_children):
          assert len(visited_children) >= 1
          return Tuple(visited_children)

     def local_definitions(self, node, visited_children, factory):
          assert len(visited_children) >= 2
          *local_vars, body = visited_children
          assert isinstance(local_vars, list)
          for lv in local_vars: assert len(lv) == 2
          assert isinstance(body, Expr)
          return factory(local_vars, body)

     def visit_letin(self, node, visited_children):
          return self.local_definitions(node, visited_children, LetIn)

     def visit_letrec(self, node, visited_children):
          return self.local_definitions(node, visited_children, LetRec)

     def visit_local_var(self, node, visited_children):
          assert len(visited_children) == 2, visited_children
          pattern, definition = visited_children
          return (pattern, definition)

     def visit_local_lam(self, node, visited_children):
          return self.visit_local_var(node, visited_children)

     def visit_pattern(self, node, visited_children):
          if len(visited_children) == 1:
               return visited_children[0]
          else:
               return visited_children

     def visit_rec(self, node, visited_children):
          assert len(visited_children) == 1
          return Rec(visited_children[0])


parser = ParseLambdaVisitor()
