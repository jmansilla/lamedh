from lamedh.expr import Expr

import atexit
import os
import readline

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
                print(self.OUT, self.memory[raw_expr])
            else:
                print('Memory has', self.memory.keys())
                self.parse_expr(new_name, raw_expr)

    def parse_expr(self, new_name, raw_expr):
            try:
                parsed = Expr.from_string(raw_expr)
                # FIXME: if new parsed expression has free vars that are in memory, substitute them
            except Exception as e:
                print("Parsing Lambda Expr Error: %s" % e)
                return
            print('new expression parsed:', parsed)
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

        if operation == 'show()':
            print(self.OUT, stored_expr)
        elif operation == 'debug()':
            print(self.OUT, repr(stored_expr))
        else:
            print("Error: unknown operation: '%s'" % operation)
        return

    def help(self):
        print("Help:")
        print("Define expressions by typing: <name> = <expression>")
        print("Then you can:")
        print("  - show expressions by typing: <name> -> show()")
        print("  - show expressions by typing: <name> -> debug()")
        print("  - reduce to normal form by typing: <name> -> goto_normal(max_steps=N)")
        print("  - evaluate Eagerly an expression by typing: <name> -> evalE(max_steps=N)")
        print("  - evaluate Normally an expression by typing: <name> -> evalN(max_steps=N)")
        print("If max_steps is not specified, defaults to 10.")
        print("NOTEs:")
        print("   - parsing DOES NOT work with un-parenthesis applications.")
        print("     Instead of λx.λy.xyz you must write λx.λy.((x y) z)")
        print("   - expressions ARE NOT reduced/evaluated inplace, they are cloned, in order to")
        print("     save the result, type: <new_name> = <name> -> <operation>")

    def greetings(self):
        print("Greetings. This is the λ-Lamedh Calculus Terminal.")
        print("Type ? for help.")
