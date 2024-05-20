import unittest
from lamedh.expr import Var, Lam, App, CanNotEvalException, NotVarException


# class TestExpr(unittest.TestCase):
#     def test_var(self):
#         e = Expr(ExpKind.Var, 'x')
#         self.assertEqual(e.evalN(), e)
#         self.assertEqual(e.evalE(), e)


class TestFreeVars(unittest.TestCase):
    def test_var(self):
        e = Var('x')
        self.assertEqual(e.get_free_variables(), ['x'])

    def test_lambda_identity_is_closed(self):
        e = Lam('x', Var('x'))
        self.assertEqual(e.get_free_variables(), [])

    def test_lambda_simple(self):
        e = Lam('x', Var('y'))
        self.assertEqual(e.get_free_variables(), ['y'])

    def test_application_of_vars(self):
        e1 = App(Var('x'), Var('z'))
        self.assertEqual(e1.get_free_variables(), ['x', 'z'])
        e2 = App(Var('x'), Var('x'))
        self.assertEqual(e2.get_free_variables(), ['x'])


class TestInstrospectFreedom(unittest.TestCase):

    def test_var(self):
        e = Var('x')
        self.assertTrue(e.iam_free())

    def test_lambda_identity_is_closed(self):
        e = Var('x')
        self.assertTrue(e.iam_free())
        lam = Lam('x', e)
        # Not free anymore
        self.assertFalse(e.iam_free())

    def test_lambda_diff_var_is_free(self):
        e = Var('x')
        lam = Lam('Z', e)
        # Still free
        self.assertTrue(e.iam_free())

    def test_nested_var_in_lambda(self):
        e0 = Var('x')
        e1 = Lam('A', e0)
        e2 = Lam('B', e1)
        # neither e1 nor e2 bound "x" from e0
        self.assertTrue(e0.iam_free())
        e3 = Lam('x', e2)
        # e3 bound "x" from e0
        self.assertFalse(e0.iam_free())

    def test_nested_var_in_app(self):
        e0 = Var('x')
        e1 = App(Var('A'), e0)
        e4 = Lam('x', e1)
        self.assertFalse(e0.iam_free())

    def test_nested_var_in_app_deep(self):
        e0 = Var('x')
        e1 = App(Var('A'), e0)
        e2 = App(Var('B'), e1)
        # neither e1 nor e2 bound "x" from e0
        self.assertTrue(e0.iam_free())
        e3 = App(Var('x'), e2)
        # still free
        self.assertTrue(e0.iam_free())
        e4 = Lam('x', e3)
        # e4 bound "x" from e0
        self.assertFalse(e0.iam_free())


if __name__ == '__main__':
    unittest.main()