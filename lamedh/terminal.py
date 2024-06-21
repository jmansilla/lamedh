import os
import re
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, FuzzyWordCompleter
from prompt_toolkit.history import FileHistory

from lamedh.expr import Expr
from lamedh.visitors import SubstituteVisitor

COMMANDS = {"?": "shows help", "exit": "quit and exit"}

OPERATION_NAMES = ["some_operation", "other_operation"]


histfile = os.path.join(os.path.expanduser("~"), ".lamedh_history")
session = PromptSession(history=FileHistory(histfile))


def clean_split(txt, delimiter):
    return map(lambda s:s.strip(), txt.split(delimiter, 1))

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

DEFAULT_NUMBER_OF_STEPS = 25
HELP = open(os.path.join(__location__, 'help.txt')).read()
HELP = HELP % DEFAULT_NUMBER_OF_STEPS


class PromptCompleter(Completer):
    COMMAND_SEPARATOR = "-> "
    def __init__(self, commands, operations, memory):
        self.commands = commands
        self.operations = operations
        self.memory = memory

    def get_completions(self, document, complete_event):
        if self.COMMAND_SEPARATOR in document.text:
            autocomplete_words = self.operations
        else:
            autocomplete_words = list(self.memory) + list(self.commands)
            autocomplete_words.append(self.COMMAND_SEPARATOR)

        return FuzzyWordCompleter(autocomplete_words).get_completions(document, complete_event)


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
        self.completer = PromptCompleter(COMMANDS, OPERATION_NAMES, self.memory)

    @property
    def formatter(self):
        default = self.formatters['pretty']
        name = str(self.memory.get('FORMAT', None))
        return self.formatters.get(name, default)

    def autocomplete_prompt(self):
        return session.prompt(
            self.PS1, completer=self.completer, complete_while_typing=True, auto_suggest=AutoSuggestFromHistory()
        )

    def main(self):
        self.greetings()
        while True:
            try:
                cmd = self.autocomplete_prompt()
            except EOFError:
                print('\nBye!')
                break
            cmd = cmd.strip()
            if cmd == "?":
                self.help()
            elif cmd == "exit" or cmd == "quit":
                print('Bye!')
                break
            elif cmd.startswith("dump") and '=' not in cmd:
                filename = cmd[4:].strip()  # may be empty string, meaning no filename
                self.dump_memory(filename)
            elif cmd.startswith("load ") and '=' not in cmd:  # load <filename>
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

    def dump_memory(self, filename=None):
        print("Dumping expressions saved in memory", end='')
        if filename:
            open_file = open(filename, 'w')
            print(f' to file "{filename}"')
            dump_formatter = self.formatters['normal']  # needs to be easy to parse
        else:
            open_file = sys.stdout
            print(":")
            dump_formatter = self.formatter
        for k, v in self.memory.items():
            if k in self.HIDDEN_NAMES:
                continue
            print(f"{k} = {dump_formatter(v)}", file=open_file)
        if open_file is not sys.stdout:
            open_file.close()

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
            msg = 'new expression parsed:'
            if new_name != self.DEFAULT_NAME:
                msg += ' %s = %s' % (new_name, self.formatter(parsed))
            else:
                msg += ' %s' % self.formatter(parsed)
            print(msg)
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
        elif operation == 'as_tree()' or operation == 'as_tree':
            print(self.OUT, self.formatter.as_tree(repr(stored_expr)))
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
    indent = '|  '

    def __call__(self, expr):
        return str(expr)

    def justify_till_end(self, msg, gap):
        columns, _ = os.get_terminal_size()
        length = len(msg)
        if length < (columns - gap):
            msg += ' ' * (columns - gap - length)
        return msg

    def as_tree(self, expr_str):
        result = "\n"
        depth = 0
        for c in expr_str:
            if c == '(':
                depth += 1
                result += '('
                result += '\n' + (self.indent * depth)
            elif c == ')':
                depth -= 1
                result += '\n' + (self.indent * depth) + ')'
            elif c == ' ' or c == '.':
                result += c
                result += '\n' + (self.indent * depth)
            else:
                result += c
        return result


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


class PrettyFormatter(NormalFormatter):

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
