from functools import reduce
from lark import Lark
from lark.lexer import Token
from lark.tree import Tree

from lamedh.expr import Lam, App, Var

grammar = """
?start: app

?app: lam
    | app " "* lam
    | app " "* app
    | "(" app ")"
    | var

lam: LAMBDA _bounds "." app

_bounds : var+
var: NAME

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


parser = ParseLambdaVisitor()
