class StackUnderflowError(Exception):
    pass

def evaluate(input_data):
    stack = []
    words = input_data.split()
    for word in words:
        if word.isdigit():
            stack.append(int(word))
        elif word == '+':
            if len(stack) < 2:
                raise StackUnderflowError("Not enough values on the stack")
            stack.append(stack.pop() + stack.pop())
        elif word == '-':
            if len(stack) < 2:
                raise StackUnderflowError("Not enough values on the stack")
            stack.append(-stack.pop() + stack.pop())
        elif word == '*':
            if len(stack) < 2:
                raise StackUnderflowError("Not enough values on the stack")
            stack.append(stack.pop() * stack.pop())
        elif word == '/':
            if len(stack) < 2:
                raise StackUnderflowError("Not enough values on the stack")
            divisor = stack.pop()
            if divisor == 0:
                raise ValueError("Division by zero")
            stack.append(int(stack.pop() / divisor))
        elif word == 'DUP':
            if len(stack) < 1:
                raise StackUnderflowError("Not enough values on the stack")
            stack.append(stack[-1])
        elif word == 'DROP':
            if len(stack) < 1:
                raise StackUnderflowError("Not enough values on the stack")
            stack.pop()
        elif word == 'SWAP':
            if len(stack) < 2:
                raise StackUnderflowError("Not enough values on the stack")
            stack[-1], stack[-2] = stack[-2], stack[-1]
        else:
            raise ValueError(f"Unknown word: {word}")
    return stack
