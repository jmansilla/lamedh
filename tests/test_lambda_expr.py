import unittest
from lamedh.expr import Expr, Var, Lam, App

Factory = Expr.from_string


class TestFreeVars(unittest.TestCase):
    def test_var(self):
        e = Var('x')
        self.assertEqual(e.get_free_vars(), {e})

    def test_lambda_identity_is_closed(self):
        e = Lam('x', Var('x'))
        self.assertEqual(e.get_free_vars(), set())

    def test_lambda_simple(self):
        y = Var('y')
        e = Lam('x', y)
        self.assertEqual(e.get_free_vars(), {y})

    def test_nested_var_in_app(self):
        v0 = Var('x')
        v1 = Var('a')
        e2 = App(v1, v0)
        e3 = Lam('x', e2)
        self.assertEqual(e3.get_free_vars(), {v1})
        self.assertEqual(e2.get_free_vars(), {v0, v1})

    def test_application_of_vars(self):
        x, z = Var('x'), Var('z')
        e1 = App(x, z)
        self.assertEqual(e1.get_free_vars(), {x, z})
        m1, m2 = Var('m'), Var('m')
        e2 = App(m1, m2)
        self.assertEqual(e2.get_free_vars(), {m1, m2})

    def test_lambda_of_apps_binds_both_branches(self):
        m1, m2 = Var('m'), Var('m')
        e = App(m1, m2)
        lam = Lam('m', e)
        self.assertEqual(lam.get_free_vars(), set())

    def test_nested_var_in_lambda(self):
        e0 = Var('x')
        e1 = Lam('A', e0)
        e2 = Lam('B', e1)
        # neither e1 nor e2 bound "x" from e0
        self.assertIn(e0, e1.get_free_vars())
        self.assertIn(e0, e2.get_free_vars())
        e3 = Lam('x', e2)
        # e3 bound "x" from e0
        self.assertNotIn(e0, e3.get_free_vars())

    def test_nested_var_in_app_deep(self):
        e0 = Var('x')
        e1 = App(Var('A'), e0)
        e2 = App(Var('B'), e1)
        # neither e1 nor e2 bound "x" from e0
        self.assertIn(e0, e1.get_free_vars())
        self.assertIn(e0, e2.get_free_vars())
        e3 = App(Var('x'), e2)
        # still free
        self.assertIn(e0, e3.get_free_vars())
        e4 = Lam('x', e3)
        # e4 bound "x" from e0
        self.assertNotIn(e0, e4.get_free_vars())


class TestRenames(unittest.TestCase):
    def test_var(self):
        e = Var('x')
        new_name = 'y'
        e.rename(new_name)
        self.assertEqual(e.var_name, new_name)

    def test_lambda_simple(self):
        lam = Factory('λx.z')
        lam.rename('y')
        # shall only rename the binding var_name
        self.assertEqual(lam.var_name, 'y')
        # and keep the body intact
        self.assertEqual(lam.body.var_name, 'z')
        self.assertEqual(str(lam), '(λy.z)')

    def test_lambda_identity_renames_bound(self):
        lam = Factory('λx.x')
        new_name = 'y'
        lam.rename(new_name)
        # shall both rename the binding var_name, and the body var
        self.assertEqual(lam.var_name, new_name)
        self.assertEqual(str(lam), '(λy.y)')

    def test_lambda_app_renames_both_branches(self):
        x, y1, y2, z = Var('x'), Var('y'), Var('y'), Var('z')
        e1 = App(x, y1)
        e2 = App(y2, z)
        lam = Lam('y', App(e1, e2))
        self.assertEqual(str(lam), '(λy.((x y) (y z)))')
        lam.rename('T')
        self.assertEqual(str(lam), '(λT.((x T) (T z)))')

    def test_renames_skips_inner_if_bound_by_inner(self):
        expr = Factory('(λx.(x (y (λx.x))))')
        expr.rename('T')
        self.assertEqual(str(expr), '(λT.(T (y (λx.x))))')


class TestLambdaApply(unittest.TestCase):

    def assertStringsEqual(self, o1, o2):
        self.assertEqual(str(o1), str(o2))

    def test_reduce_identity(self):
        app = Factory('((λx.x) y)')
        reduced = app.reduce()
        self.assertStringsEqual(reduced, Var('y'))
        self.assertStringsEqual(reduced.parent, None)

    def test_reduce_twice(self):
        app = Factory('((λx.x) ((λx.x) y))')
        reduced = app.reduce().reduce()
        self.assertStringsEqual(reduced, Var('y'))
        self.assertStringsEqual(reduced.parent, None)

    def test_reduce_eta_substitution(self):
        app = Factory('((λy.x) z)')
        reduced = app.reduce()
        self.assertStringsEqual(reduced, Var('x'))
        self.assertEqual(reduced.parent, None)

    def test_parent_of_app_is_updated(self):
        app_1 = Factory('((λx.x) y)')
        outer_app = App(app_1, Var('u'))
        reduced = app_1.reduce()
        self.assertEqual(reduced.parent, outer_app)
        self.assertEqual(outer_app.operator, reduced)

    def test_reduce_doing_one_substitution(self):
        zwz = Factory('λz.λw.z')
        identity_a = Factory('λa.a')
        reduced = App(zwz, identity_a).reduce()
        self.assertEqual(str(reduced), '(λw.(λa.a))')

    def test_reduce_doing_several_substitutions(self):
        body_str = "(λw.(z (w (z z))))"
        zwz = Factory('(λz.%s)' % body_str)
        identity_a = Factory('λa.a')
        app = App(zwz, identity_a)
        reduced = app.reduce()
        a = str(identity_a)
        self.assertEqual(str(reduced), "(λw.(%s (w (%s %s))))" % (a, a, a))

    def test_reduce_with_simple_rename(self):
        zwz = Factory('λz.λw.(z w)')
        arg = Factory('(w a)')
        reduced = App(zwz, arg).reduce()
        self.assertStringsEqual(reduced, '(λw1.((w a) w1))')

class TestRedexes(unittest.TestCase):

    def test_goto_normal(self):
        ffx = Expr.from_string('(λf.λx.(f (f x)))')
        zyx = Expr.from_string('λz.λx.λy.((z y) x)')
        zwz = Expr.from_string('(λz.λw.z)')
        expr = App(App(ffx, zyx), zwz)
        normal = expr.goto_normal()
        self.assertTrue(normal.is_normal())
        self.assertEqual(str(normal), '(λx1.(λy.x1))')


if __name__ == '__main__':
    unittest.main()
