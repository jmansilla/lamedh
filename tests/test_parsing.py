import unittest

from lamedh.expr import Var, Lam, App
from lamedh.parsing.simple import parser  # type: ignore


class TestParsing(unittest.TestCase):

    def parse(self, expr_str):
        return parser.parse(expr_str)

    def test_var(self):
        x = self.parse('x')
        self.assertTrue(isinstance(x, Var))
        self.assertEqual(x.var_name, 'x')

    def test_lambda_identity(self):
        lam = self.parse('(λx.x)')
        self.assertTrue(isinstance(lam, Lam))
        self.assertEqual(lam.var_name, 'x')
        self.assertTrue(isinstance(lam.body, Var))
        self.assertEqual(lam.body.var_name, 'x')

    def test_app_simple(self):
        app = self.parse('(A B)')
        self.assertTrue(isinstance(app, App))
        self.assertTrue(isinstance(app.operator, Var))
        self.assertEqual(app.operator.var_name, 'A')
        self.assertTrue(isinstance(app.operand, Var))
        self.assertEqual(app.operand.var_name, 'B')

    def test_app_simple_parenteses_less(self):
        app = self.parse('A B')
        self.assertEqual(repr(app), 'App(<Var:A> <Var:B>)')

    def test_app_is_left_associative(self):
        app = self.parse('A B C')
        self.assertEqual(repr(app), 'App(App(<Var:A> <Var:B>) <Var:C>)')

    def test_app_nested(self):
        app = self.parse('(A (B C))')
        self.assertTrue(isinstance(app, App))
        self.assertTrue(isinstance(app.operator, Var))
        self.assertEqual(app.operator.var_name, 'A')
        self.assertTrue(isinstance(app.operand, App))
        self.assertTrue(isinstance(app.operand.operator, Var))
        self.assertEqual(app.operand.operator.var_name, 'B')
        self.assertTrue(isinstance(app.operand.operand, Var))
        self.assertEqual(app.operand.operand.var_name, 'C')

    def test_lambda_nested(self):
        lam = self.parse('(λx.λy.(w z))')
        self.assertTrue(isinstance(lam, Lam))
        self.assertEqual(lam.var_name, 'x')
        self.assertTrue(isinstance(lam.body, Lam))
        self.assertEqual(lam.body.var_name, 'y')
        self.assertTrue(isinstance(lam.body.body, App))
        self.assertTrue(isinstance(lam.body.body.operator, Var))
        self.assertEqual(lam.body.body.operator.var_name, 'w')
        self.assertTrue(isinstance(lam.body.body.operand, Var))
        self.assertEqual(lam.body.body.operand.var_name, 'z')

    def test_lambda_multiple_variables(self):
        lam = self.parse('(λx y.(w z))')
        self.assertTrue(isinstance(lam, Lam))
        self.assertEqual(lam.var_name, 'x')
        self.assertTrue(isinstance(lam.body, Lam))
        self.assertEqual(lam.body.var_name, 'y')
        self.assertTrue(isinstance(lam.body.body, App))
        self.assertTrue(isinstance(lam.body.body.operator, Var))
        self.assertEqual(lam.body.body.operator.var_name, 'w')
        self.assertTrue(isinstance(lam.body.body.operand, Var))
        self.assertEqual(lam.body.body.operand.var_name, 'z')

    def test_lamda_extends_to_the_end(self):
        # meaning that binds stronger than App
        lam = self.parse('λx.a b')
        self.assertEqual(repr(lam), 'Lam(λx.App(<Var:a> <Var:b>))')

    def test_lambda_extends_to_the_end_when_nested(self):
        lam = self.parse('λx.x λz.z x')
        self.assertEqual(str(lam), '(λx.(x (λz.(z x))))')

    def test_parse_and_print_idempotent(self):
        complex_str = '(x (λx.(λy.(w z))))'
        complex = self.parse(complex_str)
        self.assertEqual(complex_str, str(complex))


if __name__ == '__main__':
    unittest.main()
