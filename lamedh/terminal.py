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

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

DEFAULT_NUMBER_OF_STEPS = 25
HELP = open(os.path.join(__location__, 'help.txt')).read()
HELP = HELP % DEFAULT_NUMBER_OF_STEPS


class Terminal:
    PS1 = "λh> "
    OUT = "OUT: "
    DEFAULT_NAME = '_'
    HIDDEN_NAMES = [DEFAULT_NAME, 'FORMAT']
    RESERVED_NAMES = ['?', 'exit', 'quit', 'dump', 'load']

    def __init__(self):
        self.memory = {}
        self.formatters = {
            'normal': NormalFormatter(),
            'pretty': PrettyFormatter(),
            'clean': CleanFormatter()
        }

    @property
    def formatter(self):
        default = self.formatters['pretty']
        name = str(self.memory.get('FORMAT', None))
        return self.formatters.get(name, default)

    def main(self):
        self.greetings()
        while True:
            try:
                cmd = input(self.PS1)
            except EOFError:
                print('\nBye!')
                break
            cmd = cmd.strip()
            if cmd == "?":
                self.help()
            elif cmd == "exit" or cmd == "quit":
                print('Bye!')
                break
            elif cmd == "dump":
                self.dump_memory()
            elif cmd.startswith("load "):
                filename = cmd[5:].strip()
                self.process_file(filename)
            else:
                if not cmd:
                    continue
                self.process_cmd(cmd)

    def process_def(self, definition):
        # FIXME: it seems that clean_split doesn't raise any exception.
        try:
            new_name, raw_expr = clean_split(definition, '=')
        except ValueError:
            print("Error: expression can have at most one '=', got '%s' instead" % definition.count('='))
            return
        return new_name, raw_expr

    def add_definition(self, new_name, expr):
        if new_name in self.RESERVED_NAMES:
            print("Error: name '%s' is reserved" % new_name)
            return
        if expr in self.memory:
            # actually "expr" is a name in memory and not an expression
            if new_name != self.DEFAULT_NAME:
                # creating a new name for existing expression
                self.memory[new_name] = self.memory[expr]
            else:
                # invoking print for existing expression
                print(self.OUT, self.formatter(self.memory[expr]))
        else:
            # creating a new expression, and saving it as new_name
            self.parse_expr(new_name, expr)

    def dump_memory(self):
        print("Dumping expressions saved in memory:")
        for k, v in self.memory.items():
            if k in self.HIDDEN_NAMES:
                continue
            print(f"{k}: {self.formatter(v)}")

    def process_cmd(self, cmd):
        if '=' in cmd:
            definition = self.process_def(cmd)
            if definition is None:
                return
            new_name, raw_expr = definition
        else:
            new_name = self.DEFAULT_NAME
            raw_expr = cmd
        if not new_name:
            print("Error: expression name can't be empty")
            return

        raw_expr = raw_expr.strip()
        if '->' in raw_expr:
            self.process_operation(new_name, raw_expr)
        else:
            self.add_definition(new_name, raw_expr)

    def parse_expr(self, new_name, raw_expr):
            try:
                parsed = Expr.from_string(raw_expr)
                mapping = {k: v.clone() for k, v in self.memory.items() if k not in self.HIDDEN_NAMES}
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
                        max_steps = DEFAULT_NUMBER_OF_STEPS
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

    def process_file(self, filename):
        try:
            with open(filename) as file:
                contents = file.readlines()
                for line in contents:
                    definition = self.process_def(line)
                    if definition is None:
                        continue
                    new_name, raw_expr = definition
                    self.add_definition(new_name, raw_expr)
        except Exception as e:
            print("Error: %s" % e)

    def help(self):
        print(HELP)

    def greetings(self):
        print("Greetings. This is the λ-Lamedh Calculus Terminal.")
        print("Type ? for help.")


class NormalFormatter:

    def __call__(self, expr):
        return str(expr)

    def justify_till_end(self, msg, gap):
        columns, _ = os.get_terminal_size()
        length = len(msg)
        if length < (columns - gap):
            msg += ' ' * (columns - gap - length)
        return msg


class CleanFormatter(NormalFormatter):

    def __call__(self, expr):
        txt = str(expr)
        # let's minimize the number of parentheses
        open_par = txt.count('(')
        assert open_par == txt.count(')')  # sanity check only
        removals = 0
        for i in range(open_par):
            new_txt = self.remove_pair_parentheses(txt, i - removals)
            try:
                parsed = Expr.from_string(new_txt)
            except Exception as e:
                parsed = None
            if repr(parsed) == repr(expr):
                # success
                txt = new_txt
                removals += 1
        return txt.strip()

    def find_nth(self, txt, key, idx=0):
        # find the nth occurrence of key in txt. Key is single character
        assert len(key) == 1
        length = 1
        i = -length
        for c in range(idx + 1):
            i = txt.find(key, i + length)
            if i < 0:
                break
        return i

    def remove_pair_parentheses(self, txt, open_idx):
        idx = self.find_nth(txt, '(', open_idx)
        prefix = txt[:idx]
        suffix = txt[idx+1:]
        still_open = prefix.count('(') - prefix.count(')')
        new_suffix = ''
        found = False
        for c in suffix:
            if c == '(' and not found:
                still_open += 1
                new_suffix += c
            elif c == ')' and not found:
                still_open -= 1
                if still_open > 0:
                    new_suffix += c
                else:
                    found = True
            else:
                new_suffix += c
        return prefix + new_suffix


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

    def __call__(self, expr):
        txt = str(expr)
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

    def justify_till_end(self, msg, gap):
        columns, _ = os.get_terminal_size()
        length = len(re.subn('\\x1b.*?m', '', msg)[0])
        if length < (columns - gap):
            msg += ' ' * (columns - gap - length)
        return msg