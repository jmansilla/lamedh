from copy import deepcopy

from lamedh.visitors import FreeVarVisitor, BoundVarVisitor, SubstituteVisitor, RedicesVisitor
from lamedh.visitors import EvalNormalVisitor, EvalEagerVisitor


class StopEvaluation(Exception):
    pass


class CantEvalException(Exception):
    pass


class CantReduceException(Exception):
    pass


class CantReduceToCanonicalException(Exception):
    pass


class Expr:

    @staticmethod
    def from_string(expr_str):
        # import here to avoid circular import error
        from lamedh.parsing.lambda_lark import parser  # type: ignore
        return parser.parse(expr_str)

    def clone(self):
        return deepcopy(self)

    def get_free_vars(self):
        return FreeVarVisitor().visit(self)

    def is_redex(self):
        return False

    def goto_root(self):
        node = self
        while node.parent:
            node = node.parent
        return node

    def get_redices(self):
        root = self.goto_root()
        return RedicesVisitor().visit(root)

    def is_normal_form(self):
        return len(self.get_redices()) == 0

    def is_canonical(self):
        root = self.goto_root()
        return isinstance(root, Lam)

    def reduce(self):
        raise CantReduceException()

    def substitute(self, substitution_map):
        substituted = SubstituteVisitor().visit(self, substitution_map)
        return substituted

    def goto_canonical(self, max_steps=25, verbose=False):
        root = self.goto_root().clone()
        step = 0
        while not root.is_canonical() and step < max_steps:
            redices = root.get_redices()
            if not redices:
                raise CantReduceToCanonicalException
            redex = redices[0]  # try to reduce outer most first
            root = redex.reduce().goto_root()
            step += 1
            if verbose:
                print(root)
        return root

    def goto_normal_form(self, max_steps=25, verbose=False, **kwargs):
        step = 0
        def show(expr):
            str_expr = kwargs.get('formatter', str)(expr)
            print('step', step, '->', str_expr, '    %s redices' % len(expr.get_redices()))
        root = self.goto_root().clone()
        if verbose:
            show(root)
        while not root.is_normal_form() and step < max_steps:
            redices = root.get_redices()
            if not redices:
                raise CantReduceToCanonicalException
            redex = redices[-1]  # try to reduce inner most first, always
            root = redex.reduce().goto_root()
            step += 1
            if verbose:
                show(root)
        return root

    def evalN(self, max_steps=25, verbose=False, **kwargs):
        visitor = EvalNormalVisitor(max_steps=max_steps, verbose=verbose, **kwargs)
        return visitor.visit(self, '')

    def evalE(self, max_steps=25, verbose=False, **kwargs):
        visitor = EvalEagerVisitor(max_steps=max_steps, verbose=verbose, **kwargs)
        return visitor.visit(self, '')


class Var(Expr):

    def __init__(self, name):
        self.parent = None
        self.var_name = name

    def __repr__(self):
        return f'<Var:{self.var_name}>'

    def __str__(self):
        return self.var_name

    def rename(self, new_name):
        assert isinstance(new_name, str)
        self.var_name = new_name


class Lam(Expr):

    def __init__(self, name, body):
        self.parent = None
        assert isinstance(name, str)
        self.var_name = name
        assert isinstance(body, Expr)
        self.body = body
        self.body.parent = self

    def __repr__(self):
        return f'Lam(λ{self.var_name}.{repr(self.body)})'

    def __str__(self):
        return f'(λ{self.var_name}.{self.body})'

    def children(self):
        return [self.body]

    def replace_child(self, old, new):
        new.parent = self
        self.body = new

    def bound_var_occurrence(self):
        # Returns all occurrences of variables this lambda's is binding
        return BoundVarVisitor().visit(self, self.var_name)

    def rename(self, new_name):
        assert isinstance(new_name, str)
        for occ in self.bound_var_occurrence():
            occ.rename(new_name)
        self.var_name = new_name


class App(Expr):

    def __init__(self, operator, operand):
        self.parent = None
        assert isinstance(operator, Expr)
        assert isinstance(operand, Expr)
        self.operator = operator
        self.operand = operand
        operator.parent = self
        operand.parent = self

    def children(self):
        return [self.operator, self.operand]

    def __repr__(self):
        return f'App({repr(self.operator)} {repr(self.operand)})'

    def __str__(self):
        return f'({self.operator} {self.operand})'

    def is_redex(self):
        return isinstance(self.operator, Lam)

    def replace_child(self, old, new):
        new.parent = self
        if self.operator == old:
            self.operator = new
        if self.operand == old:
            self.operand = new

    def reduce(self):
        # Reducing redices WILL modify objects in-place.
        # If needed to preserve original structure, caller must make a copy
        # before calling reduce
        if not self.is_redex():
            raise CantReduceException()

        lam = self.operator
        arg = self.operand
        mapping = {lam.var_name: arg.clone()}
        substituted = lam.body.substitute(mapping)

        if self.parent:
            self.parent.replace_child(self, substituted)
        substituted.parent = self.parent
        return substituted

