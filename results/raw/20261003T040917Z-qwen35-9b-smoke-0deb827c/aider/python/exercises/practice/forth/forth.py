# Forth interpreter implementation
class StackUnderflowError(Exception):
    pass

def evaluate(input_data):
    # Convert input to list of tokens if it's a string
    if isinstance(input_data, str):
        tokens = input_data.replace('\n', ' ').split()
    else:
        tokens = input_data
    
    # Stack to hold values
    stack = []
    
    # Dictionary of built-in operations (case-insensitive)
    operations = {
        '+': lambda s: s.pop() + s.pop(),
        '-': lambda s: s.pop() - s.pop(),
        '*': lambda s: s.pop() * s.pop(),
        '/': lambda s: s.pop() // s.pop(),
        'DUP': lambda s: s.append(s[-1]),
        'DROP': lambda s: s.pop(),
        'SWAP': lambda s: s.append(s.pop(-2)),
        'OVER': lambda s: s.append(s[-2]),
    }
    
    # Dictionary to store user-defined words
    word_definitions = {}
    
    # Process tokens
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Check if this is a word definition starting with ':'
        if token == ':':
            # Find the end of the definition
            j = i + 1
            while j < len(tokens) and tokens[j] != ';':
                j += 1
            
            # Extract the definition (everything between : and ;)
            definition_tokens = tokens[i+1:j]
            
            # Remove any leading name (first token after :) if it's not a built-in word
            # The first token after : is the word name, skip it
            if len(definition_tokens) > 0:
                word_name = definition_tokens[0].upper()
                
                # Check if the first token is a number or starts with digit/minus (not a valid word name)
                # In Forth, word names can't start with digits or minus signs
                if word_name.isdigit() or (word_name.startswith('-') and len(word_name) > 1):
                    raise ValueError("illegal operation")
                
                # Build the definition by expanding any built-in words
                expanded_definition = []
                for def_token in definition_tokens[1:]:  # Skip the word name itself
                    def_upper = def_token.upper()
                    
                    # If it's a defined word, use its definition
                    if def_upper in word_definitions:
                        expanded_definition.extend(word_definitions[def_upper])
                    # If it's a built-in operation, add it directly
                    elif def_upper in operations:
                        expanded_definition.append(def_token)
                    # If it's a number or unknown word, keep as is (for later evaluation)
                    else:
                        expanded_definition.append(def_token)
                
                # Store the definition
                word_definitions[word_name] = expanded_definition
            
            i = j + 1  # Move past the ';'
        else:
            # Process the token
            token_upper = token.upper()
            
            # Check if it's a number (sequence of digits, possibly with minus sign)
            if token.isdigit() or (token.startswith('-') and len(token) > 1 and token[1:].isdigit()):
                stack.append(int(token))
            elif token_upper in operations:
                # Get the operation function
                op_func = operations[token_upper]
                
                # For operations that need 2 items, check stack first
                if token_upper in ['+', '-', '*', '/']:
                    if len(stack) < 2:
                        raise StackUnderflowError("Insufficient number of items in stack")
                    
                    # Perform the operation
                    if token_upper == '+':
                        result = stack.pop() + stack.pop()
                    elif token_upper == '-':
                        result = stack.pop() - stack.pop()
                    elif token_upper == '*':
                        result = stack.pop() * stack.pop()
                    elif token_upper == '/':
                        if stack[-1] == 0:
                            raise ZeroDivisionError("divide by zero")
                        # Pop twice for subtraction/division (LIFO order)
                        b = stack.pop()
                        a = stack.pop()
                        result = a - b if token_upper == '-' else a // b
                    
                    stack.append(result)
                elif token_upper in ['DUP', 'DROP', 'SWAP', 'OVER']:
                    # These need to check stack size first
                    if len(stack) < 1:
                        raise StackUnderflowError("Insufficient number of items in stack")
                    
                    if token_upper == 'DUP':
                        stack.append(stack[-1])
                    elif token_upper == 'DROP':
                        stack.pop()
                    elif token_upper == 'SWAP':
                        if len(stack) < 2:
                            raise StackUnderflowError("Insufficient number of items in stack")
                        a = stack.pop()
                        b = stack.pop()
                        stack.append(a)
                        stack.append(b)
                    elif token_upper == 'OVER':
                        if len(stack) < 2:
                            raise StackUnderflowError("Insufficient number of items in stack")
                        stack.append(stack[-2])
            else:
                # Unknown word/operation
                raise ValueError("undefined operation")
    
    return stack
