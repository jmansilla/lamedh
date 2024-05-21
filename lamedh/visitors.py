from collections import defaultdict
from copy import copy
import string


class VisitError(Exception):
    pass


class BaseVisitor:

    def visit(self, expr, *args, **kwargs):
        if hasattr(expr, 'children'):
            children = [self.visit(c, *args, **kwargs) for c in expr.children()]
        else:
            children = []
        custom_visit_method = 'visit_' + type(expr).__name__.lower()
        method = getattr(self, custom_visit_method, self.generic_visit)
        return method(expr, children, *args, **kwargs)

    def generic_visit(self, expr, visited_children, *args, **kwargs):
        raise VisitError


class FreeVarVisitor(BaseVisitor):

    def visit_var(self, expr, visited_children):
        return {expr}

    def visit_lam(self, expr, visited_children):
        body_free_vars = visited_children[0]
        return set([v for v in body_free_vars if v.var_name != expr.var_name])

    def visit_app(self, expr, visited_children):
        set_a, set_b = visited_children
        return copy(set_a).union(set_b)


class BoundVarVisitor(BaseVisitor):

    def visit(self, expr, *args, **kwargs):
        if not hasattr(self, 'initializer'):
            self.initializer = expr
        kwargs['initializer'] = self.initializer == expr
        return super().visit(expr, *args, **kwargs)

    def visit_var(self, expr, visited_children, name, initializer):
        if expr.var_name == name:
            return {expr}
        else:
            return set()

    def visit_lam(self, expr, visited_children, name, initializer):
        if initializer:
            # The body of thise lambda is where we are checking bindings
            return visited_children[0]
        if expr.var_name == name:
            # inside this expression, the `name` doesn't bind any more the outside Lambda,
            # becuase will start binding with current inner Lambda
            return set()
        else:
            return visited_children[0]

    def visit_app(self, expr, visited_children, name, initializer):
        set_a, set_b = visited_children
        return copy(set_a).union(set_b)


class SubstituteVisitor(BaseVisitor):

    def visit(self, expr, *args, **kwargs):
        visit_method_name = 'visit_' + type(expr).__name__.lower()
        method = getattr(self, visit_method_name)
        return method(expr, *args, **kwargs)

    def visit_var(self, expr, substitution_map):
        if expr.var_name in substitution_map:
            return substitution_map[expr.var_name].clone()
        else:
            return expr

    def visit_app(self, expr, substitution_map):
        visited_optr = self.visit(expr.operator, substitution_map)
        visited_operand = self.visit(expr.operand, substitution_map)
        App_ = expr.__class__
        return App_(visited_optr, visited_operand)

    def visit_lam(self, expr, substitution_map):
        # before propagating substitution, we need to be sure that lam.var_name is safe
        names_not_to_use = set()
        free_vars_in_body = [
            e for e in expr.body.get_free_vars()
            if e.var_name != expr.var_name
        ] # excluding the free-vars bound to this lambda
        for fv in free_vars_in_body:
            subs_expr = substitution_map.get(fv.var_name, fv)
            subs_fv = subs_expr.get_free_vars()
            names_not_to_use = names_not_to_use.union([_.var_name for _ in subs_fv])
        if expr.var_name in names_not_to_use:
            # need renaming
            new_name = expr.var_name
            name_gen = var_name_generator_numerical(expr.var_name)
            while new_name in names_not_to_use:
                new_name = next(name_gen)
            expr.rename(new_name)

        new_body = self.visit(expr.body, substitution_map)
        Lam_ = expr.__class__
        return Lam_(expr.var_name, new_body)

class EvalNormalVisitor(BaseVisitor):

    def __init__(self, max_steps, verbose=False) -> None:
        super().__init__()
        self.steps = 0
        self.max_steps = max_steps
        self.verbose = verbose

    def show(self, expr, breadcrumbs, success=''):
        print(breadcrumbs.ljust(8), 'step', '%s/%s'.ljust(8) % (self.steps, self.max_steps), '->', expr)

    def visit(self, expr, *args, **kwargs):
        visit_method_name = 'visit_' + type(expr).__name__.lower()
        method = getattr(self, visit_method_name)
        return method(expr, *args, **kwargs)

    def visit_var(self, expr, breadcrumbs):
        from lamedh.expr import CantEvalException
        raise CantEvalException()

    def _register_step(self):
        from lamedh.expr import StopEvaluation
        if self.steps >= self.max_steps:
            raise StopEvaluation()
        self.steps += 1

    def visit_lam(self, expr, breadcrumbs):
        self._register_step()
        if self.verbose:
            self.show(expr, breadcrumbs, success=expr)
        return expr

    def visit_app(self, expr, breadcrumbs):
        self._register_step()
        if self.verbose:
            self.show(expr, breadcrumbs)
        e1 = expr.operator.clone()
        e2 = expr.operand.clone()
        e1.parent = None
        e2.parent = None
        e1_canonic_form = self.visit(e1, breadcrumbs + 'a')
        if not e1_canonic_form.is_canonical():
            from lamedh.expr import CantEvalException
            raise CantEvalException()
        mapping = {e1_canonic_form.var_name: e2}
        new_e = e1_canonic_form.body.substitute(mapping)
        return self.visit(new_e, breadcrumbs + 'b')


class RedicesVisitor(BaseVisitor):
    # each Redex will be an instances of App class where it's operator it's a Lam

    def visit_var(self, expr, visited_children):
        return []

    def visit_app(self, expr, visited_children):
        assert len(visited_children) == 2  # only two children, operator and operand
        redices_operator, redices_operand = visited_children
        result = redices_operator + redices_operand
        if expr.is_redex():
            result.insert(0, expr)
        return result

    def visit_lam(self, expr, visited_children):
        assert len(visited_children) == 1  # only one child, the body
        return visited_children[0]


def var_name_generator_numerical(orig_name):
    # split orig_name into chars per se, and number
    pure_name = orig_name
    number_chars = ''
    while not pure_name.isalpha():
        last_char = pure_name[-1]
        pure_name = pure_name[:-1]
        number_chars = number_chars + last_char
    assert pure_name
    if not number_chars:
        next_number = 1
    else:
        next_number = int(number_chars) + 1
    while True:
        next_name = pure_name + str(next_number)
        next_number += 1
        yield next_name


