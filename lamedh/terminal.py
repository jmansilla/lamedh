import atexit
import os
import re
import readline

from lamedh.expr import Expr
from lamedh.visitors import SubstituteVisitor


histfile = os.path.join(os.path.expanduser("~"), ".lamedh_history")
try:
    readline.read_history_file(histfile)
    # default history len is -1 (infinite), which may grow unruly
    readline.set_history_length(1000)
except FileNotFoundError:
    pass

atexit.register(readline.write_history_file, histfile)



def clean_split(txt, delimiter):
    return map(lambda s:s.strip(), txt.split(delimiter, 1))


class Terminal:
    PS1 = "λh> "
    OUT = "OUT: "

    def __init__(self):
        self.memory = {}
        self.formatter = PrettyFormatter()

    def main(self):
        self.greetings()
        while True:
            try:
                cmd = input(self.PS1)
            except EOFError:
                break
            cmd = cmd.strip()
            if cmd == "?":
                self.help()
            elif cmd == "exit" or cmd == "quit":
                break
            else:
                if not cmd:
                    continue
                self.process_cmd(cmd)

    def process_cmd(self, cmd):
        if '=' in cmd:
            try:
                new_name, raw_expr = clean_split(cmd, '=')
            except ValueError:
                print("Error: expression can have at most one '=', got '%s' instead" % cmd.count('='))
                return
        else:
            new_name = '_'
            raw_expr = cmd
        if not new_name:
            print("Error: expression name can't be empty")
            return

        raw_expr = raw_expr.strip()
        if '->' in raw_expr:
            self.process_operation(new_name, raw_expr)
        else:
            if raw_expr in self.memory:
                if new_name != '_':
                    self.memory[new_name] = self.memory[raw_expr]
                else:
                    print(self.OUT, self.formatter(self.memory[raw_expr]))
            else:
                self.parse_expr(new_name, raw_expr)

    def parse_expr(self, new_name, raw_expr):
            try:
                parsed = Expr.from_string(raw_expr)
                # FIXME: if new parsed expression has free vars that are in memory, substitute them
                mapping = {k:v.clone() for k, v in self.memory.items() if k != '_'}
                parsed = SubstituteVisitor().visit(parsed, mapping)
            except Exception as e:
                print("Parsing Lambda Expr Error: %s" % e)
                return
            print('new expression parsed:', self.formatter(parsed))
            self.memory[new_name] = parsed

    def process_operation(self, new_name, raw_expr):
        var, operation = clean_split(raw_expr, '->')
        if '->' in operation:
            print("Error: operation can't have more than one '->'")
            return
        var = var.strip()
        if var not in self.memory:
            print("Error: unknown expression: '%s'" % var)
            return
        stored_expr = self.memory[var]

        if operation == 'show()' or operation == 'show':
            print(self.OUT, self.formatter(stored_expr))
        elif operation == 'debug()' or operation == 'debug':
            print(self.OUT, repr(stored_expr))
        else:
            for prefix in ['evalE', 'evalN', 'goto_normal_form']:
                if operation.startswith(prefix):
                    # option a, ends in "()", option b, ends in "(<number>)"
                    func = getattr(stored_expr, prefix)
                    if operation == prefix or operation == prefix+'()':
                        max_steps = 10
                    elif operation.endswith(')'):
                        number_str = operation[len(prefix)+1:-1]
                        try:
                            max_steps = int(number_str)
                        except ValueError:
                            max_steps = None
                    if not max_steps:
                        print("Error: unknown operation: '%s' Type '?' for help" % operation)
                    # Let's execute the operation
                    print(self.OUT)
                    try:
                        new_expr = func(max_steps=max_steps, verbose=1, formatter=self.formatter)
                    except Exception as e:
                        print("Error occured when running operation '%s':" % prefix)
                        print("  %s: %s" % (type(e).__name__, e))
                        return
                    print(self.OUT, self.formatter(new_expr))
                    self.memory[new_name] = new_expr
                    return
            print("Error: unknown operation: '%s' Type '?' for help" % operation)

    def help(self):
        print("Help:")
        print("Define expressions by typing: <name> = <expression>")
        print("Then you can:")
        print("  - show expressions by typing: <name> -> show()")
        print("  - show expressions by typing: <name> -> debug()")
        print("  - reduce to normal form by typing: <name> -> goto_normal_form(<Number>)")
        print("  - evaluate Eagerly an expression by typing: <name> -> evalE(<Number>)")
        print("  - evaluate Normaly an expression by typing: <name> -> evalN(<Number>)")
        print("If max_steps <Number> is not specified, defaults to 10.")
        print("NOTEs:")
        print("   - parsing DOES NOT work with un-parenthesis applications.")
        print("     Instead of λx.λy.xyz you must write λx.λy.((x y) z)")
        print("   - expressions ARE NOT reduced/evaluated inplace, they are cloned, in order to")
        print("     save the result, type: <new_name> = <name> -> <operation>")

    def greetings(self):
        print("Greetings. This is the λ-Lamedh Calculus Terminal.")
        print("Type ? for help.")


class PrettyFormatter:

    PINK = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self):
        self.colors = [self.WHITE, self.PINK, self.BLUE, self.RED, self.CYAN, self.GREEN, self.YELLOW]

    def next_color(self, respect_to):
        assert respect_to in self.colors
        idx = self.colors.index(respect_to)
        return self.colors[(idx + 1) % len(self.colors)]

    def prev_color(self, respect_to):
        assert respect_to in self.colors
        idx = self.colors.index(respect_to)
        return self.colors[(idx - 1) % len(self.colors)]

    def __call__(self, txt):
        if not isinstance(txt, str):
            txt = str(txt)
        current_color = self.colors[0]
        result = '' + current_color
        for i, c in enumerate(txt):
            if c == '(':
                current_color = self.next_color(current_color)
                result += current_color + c
            elif c == ')':
                current_color = self.prev_color(current_color)
                result += c + current_color
            else:
                result += c
        return result

    def ljust(self, msg, gap):
        columns, _ = os.get_terminal_size()
        length = len(re.subn('\\x1b.*?m', '', msg)[0])
        if length < (columns - gap):
            msg += ' ' * (columns - gap - length)
        return msg