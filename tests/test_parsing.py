import unittest

from lamedh.expr import Var, Lam, App
from lamedh.expr.applicative import BooleanConstant, NaturalConstant, UnaryOp, BinaryOp, IfThenElse, Error, TypeError, Tuple
from lamedh.parsing.simple import parser  # type: ignore

class Parsing(unittest.TestCase):
    def parse(self, expr_str):
        return parser.parse(expr_str)


class TestParsing(Parsing):

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


class TestApplicativeParsing(Parsing):
    def test_parse_boolean(self):
        for bool_str in ['false', 'true']:
            bool_expr = self.parse(bool_str)
            self.assertTrue(isinstance(bool_expr, BooleanConstant))
            self.assertEqual(bool_expr.value, bool_str)

    def test_parse_errors(self):
        for e_str in ['error', 'typeerror']:
            e_expr = self.parse(e_str)
            if e_str == 'error':
                self.assertTrue(isinstance(e_expr, Error))
            else:
                self.assertTrue(isinstance(e_expr, TypeError))
            self.assertEqual(str(e_expr), e_str)

    def test_paser_number(self):
        for natural_str in [str(n) for n in range(20)]:
            natural_expr = self.parse(natural_str)
            self.assertTrue(isinstance(natural_expr, NaturalConstant))
            self.assertEqual(natural_expr.value, natural_str)

    def test_negative_numbers(self):
        for txt in ['-6', '- 6', '-   6']:
            negative_number = self.parse(txt)
            self.assertTrue(isinstance(negative_number, UnaryOp))
            self.assertTrue(isinstance(negative_number.operand, NaturalConstant))
            self.assertEqual(str(negative_number), '(- 6)')

    def test_not_boolean(self):
        for txt in ['not true', 'not   true', 'not     false']:
            not_expr = self.parse(txt)
            self.assertTrue(isinstance(not_expr, UnaryOp))
            self.assertTrue(isinstance(not_expr.operand, BooleanConstant))
            expected = txt.replace('not', '').strip()
            self.assertEqual(str(not_expr), f'(not {expected})')

    def test_binary_operation(self):
        sub_a = 'a'
        sub_b = 'b'
        for operation in ['+', '-', '*', '/', '%', '<', '<=', '>', '>=', '==', '!=', 'and', 'or', 'implies', '<==>']:
            a_op_b_txt = f'{sub_a} {operation} {sub_b}'
            expr = self.parse(a_op_b_txt)
            self.assertTrue(isinstance(expr, BinaryOp))
            self.assertEqual(str(expr), f'({sub_a} {operation} {sub_b})')

    def test_if_then_else(self):
        sub_a = 'a'
        sub_b = 'b'
        sub_c = 'c'
        if_txt = f'if {sub_a} then {sub_b} else {sub_c}'
        expr = self.parse(if_txt)
        self.assertTrue(isinstance(expr, IfThenElse))
        self.assertEqual(str(expr), f'(If {sub_a} Then {sub_b} Else {sub_c})')

    def test_parse_tuple(self):
        basic_tuple = '<x, y, z>'
        expr = self.parse(basic_tuple)
        self.assertTrue(isinstance(expr, Tuple))
        self.assertEqual(str(expr), basic_tuple)

    def test_singleton_tuple(self):
        basic_tuple = '<x>'
        expr = self.parse(basic_tuple)
        self.assertTrue(isinstance(expr, Tuple))
        self.assertEqual(str(expr), basic_tuple)

    def test_parse_tuple_inside_tuple(self):
        basic_tuple = '<x, y, <a, b, c>, d>'
        expr = self.parse(basic_tuple)
        self.assertTrue(isinstance(expr, Tuple))
        self.assertEqual(str(expr), basic_tuple)
        self.assertEqual(len(expr.children()), 4)
        third = expr.children()[2]
        self.assertIsInstance(third, Tuple)
        self.assertEqual(len(third.children()), 3)

    def test_parse_tuple_with_comparisons(self):
        comparison_easy = '<x, y <= z>'
        expr = self.parse(comparison_easy)
        self.assertTrue(isinstance(expr, Tuple))
        self.assertEqual(str(expr), '<x, (y <= z)>')
        comparison_hard = '<x, y >= z>'
        expr = self.parse(comparison_hard)
        self.assertTrue(isinstance(expr, Tuple))
        self.assertEqual(str(expr), '<x, (y >= z)>')


if __name__ == '__main__':
    unittest.main()
