import unittest

from lamedh.expr import Var, Lam, App
from lamedh.parsing.parsing import lambda_parser

class TestParsing(unittest.TestCase):

    def test_var(self):
        x = lambda_parser.parse('x')
        self.assertTrue(isinstance(x, Var))
        self.assertEqual(x.var_name, 'x')

    def test_lambda_identity(self):
        lam = lambda_parser.parse('(λx.x)')
        self.assertTrue(isinstance(lam, Lam))
        self.assertEqual(lam.var_name, 'x')
        self.assertTrue(isinstance(lam.body, Var))
        self.assertEqual(lam.body.var_name, 'x')

    def test_app_simple(self):
        app = lambda_parser.parse('(A B)')
        self.assertTrue(isinstance(app, App))
        self.assertTrue(isinstance(app.operator, Var))
        self.assertEqual(app.operator.var_name, 'A')
        self.assertTrue(isinstance(app.operand, Var))
        self.assertEqual(app.operand.var_name, 'B')

    def test_app_nested(self):
        app = lambda_parser.parse('(A (B C))')
        self.assertTrue(isinstance(app, App))
        self.assertTrue(isinstance(app.operator, Var))
        self.assertEqual(app.operator.var_name, 'A')
        self.assertTrue(isinstance(app.operand, App))
        self.assertTrue(isinstance(app.operand.operator, Var))
        self.assertEqual(app.operand.operator.var_name, 'B')
        self.assertTrue(isinstance(app.operand.operand, Var))
        self.assertEqual(app.operand.operand.var_name, 'C')

    def test_lambda_nested(self):
        lam = lambda_parser.parse('(λx.λy.(w z))')
        self.assertTrue(isinstance(lam, Lam))
        self.assertEqual(lam.var_name, 'x')
        self.assertTrue(isinstance(lam.body, Lam))
        self.assertEqual(lam.body.var_name, 'y')
        self.assertTrue(isinstance(lam.body.body, App))
        self.assertTrue(isinstance(lam.body.body.operator, Var))
        self.assertEqual(lam.body.body.operator.var_name, 'w')
        self.assertTrue(isinstance(lam.body.body.operand, Var))
        self.assertEqual(lam.body.body.operand.var_name, 'z')

    def test_parse_and_print_idempotent(self):
        complex_str = '(x (λx.(λy.(w z))))'
        complex = lambda_parser.parse(complex_str)
        self.assertEqual(complex_str, str(complex))


if __name__ == '__main__':
    unittest.main()