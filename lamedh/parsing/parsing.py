from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

from lamedh.expr import Var, Lam, App, Expr


grammar = Grammar(
    """
    expr        = abstraction / application / var
    open        = "("
    close       = ")"
    white       = " "
    lambda      = "λ"
    dot         = "."
    var         = ~"[_A-Z0-9]+"i
    application = open expr white expr close
    abstraction = abstraction_par / abstraction_clean
    abstraction_par = open lambda var dot expr close
    abstraction_clean = lambda var dot expr
    """)

# Not working as expected.
less_parenthesis_grammar = Grammar(
    """
    expr        = abstraction / application_par / application_clean / var
    open        = "("
    close       = ")"
    white       = " "
    lambda      = "λ"
    dot         = "."
    var         = ~"[A-Z0-9]+"i
    application_par = open expr white expr close
    application_clean = expr white expr
    abstraction = abstraction_par / abstraction_clean
    abstraction_par = open lambda var dot expr close
    abstraction_clean = lambda var dot expr
    """)

class ParseLambdaVisitor(NodeVisitor):

    def filter_skips(self, children):
        return [c for c in children if isinstance(c, Expr)]

    def visit_expr(self, node, visited_children):
        """ Returns the overall output. """
        assert len(visited_children) == 1 # or var, or app or lambda
        return visited_children[0]

    def visit_application(self, node, visited_children):
        """ Gets the left and right hand side of the application. """
        left, right = self.filter_skips(visited_children)
        return App(left, right)
    visit_application_par = visit_application
    visit_application_clean = visit_application

    def visit_var(self, node, visited_children):
        """ Gets the variable name. """
        return Var(node.text)

    def visit_abstraction(self, node, visited_children):
        # it's abstraction_clean or abstraction_par (parenthesis)
        assert len(visited_children) == 1
        return visited_children[0]

    def visit_abstraction_par(self, node, visited_children):
        """ Gets the var and body of the lambda expression. """
        var, body = self.filter_skips(visited_children)
        return Lam(var.var_name, body)
    visit_abstraction_clean = visit_abstraction_par

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        return visited_children or node

lambda_parser = ParseLambdaVisitor()
lambda_parser.grammar = grammar
