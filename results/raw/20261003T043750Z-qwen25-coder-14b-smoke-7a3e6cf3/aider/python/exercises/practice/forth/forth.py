import re

class StackUnderflowError(Exception):
    """Exception raised when Stack is not full.
       message: explanation of the error.
    """
    def __init__(self, message):
        self.message = message


class ForthEvaluator:
    def __init__(self):
        self.stack = []
        self.definitions = {}

    def evaluate(self, input_data):
        tokens = self.tokenize(input_data)
        for token in tokens:
            self.handle_token(token)

    def tokenize(self, input_data):
        # Tokenize the input data into words and numbers
        return re.findall(r'\b\w+\b|\d+', input_data.upper())

    def handle_token(self, token):
        if token.isdigit():
            self.stack.append(int(token))
        elif token in self.definitions:
            self.evaluate(self.definitions[token])
        elif token in self.arithmetic_operations:
            self.arithmetic_operations[token]()
        elif token in self.stack_manipulation_operations:
            self.stack_manipulation_operations[token]()
        else:
            raise ValueError(f"undefined operation: {token}")

    arithmetic_operations = {
        '+': lambda: self.binary_operation(lambda a, b: a + b),
        '-': lambda: self.binary_operation(lambda a, b: a - b),
        '*': lambda: self.binary_operation(lambda a, b: a * b),
        '/': lambda: self.binary_operation(lambda a, b: a // b if b != 0 else self.raise_zero_division_error())
    }

    stack_manipulation_operations = {
        'DUP': lambda: self.stack.append(self.stack[-1]),
        'DROP': lambda: self.stack.pop() if self.stack else self.raise_stack_underflow_error(),
        'SWAP': lambda: (self.stack[-2], self.stack[-1] = self.stack[-1], self.stack[-2]) if len(self.stack) > 1 else self.raise_stack_underflow_error(),
        'OVER': lambda: self.stack.append(self.stack[-2]) if len(self.stack) > 1 else self.raise_stack_underflow_error()
    }

    def binary_operation(self, operation):
        if len(self.stack) < 2:
            raise StackUnderflowError("Insufficient number of items in stack")
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(operation(a, b))

    def raise_zero_division_error(self):
        raise ZeroDivisionError("divide by zero")

    def raise_stack_underflow_error(self):
        raise StackUnderflowError("Insufficient number of items in stack")


def evaluate(input_data):
    evaluator = ForthEvaluator()
    evaluator.evaluate(input_data)
    return evaluator.stack
