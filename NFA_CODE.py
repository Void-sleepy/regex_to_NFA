from graphviz import Digraph

class NFA:
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept
        self.transitions = {}

    def add_transition(self, from_state, symbol, to_state):
        if (from_state, symbol) not in self.transitions:
            self.transitions[(from_state, symbol)] = set()
        self.transitions[(from_state, symbol)].add(to_state)

def insert_concat(regex):
    output = []
    i = 0

    while i < len(regex):
        current = regex[i]
        output.append(current)

        if current == '[':
            i += 1
            while i < len(regex) and regex[i] != ']':
                output.append(regex[i])
                i += 1
            if i < len(regex):
                output.append(regex[i])
            else:
                raise ValueError("Unclosed bracket in regex")
        elif current == '!' and i + 1 < len(regex) and regex[i+1] == '[':
            # Handle negated character class
            output.append('![')  # Keep the negation with bracket
            i += 2  # Skip past '!['
            while i < len(regex) and regex[i] != ']':
                output.append(regex[i])
                i += 1
            if i < len(regex):
                output.append(regex[i])  # Add the ']'
            else:
                raise ValueError("Unclosed bracket in negated character class")

        # Add concatenation operator
        if i < len(regex) - 1:
            next_char = regex[i + 1]
            # Don't add concat after '!'
            if current != '!' and ((current.isalnum() or current in '*?]') or current == ')') and \
               (next_char.isalnum() or next_char in '([!' or next_char == '!'):
                output.append('.')

        i += 1

    result = ''.join(output)
    print(f"After inserting concatenation: {result}")
    return result

def infix_to_postfix(regex):
    regex = insert_concat(regex)
    precedence = {'*': 3, '?': 3, '.': 2, '|': 1}
    output = []
    stack = []

    print(f"Processing expanded regex: {regex}")
    i = 0
    while i < len(regex):
        char = regex[i]
        print(f"  Processing char '{char}' at position {i}, remaining: '{regex[i:]}'")

        if char.isalnum():
            output.append(char)
            print(f"    Added operand: {''.join(output)}")
        elif char == '[':
            range_start = i
            i += 1
            while i < len(regex) and regex[i] != ']':
                i += 1
            if i >= len(regex):
                print(f"    ERROR: Unclosed bracket at {range_start}, regex: {regex}")
                raise ValueError("Unclosed bracket in regex")
            range_token = regex[range_start:i + 1]
            output.append(range_token)
            print(f"    Added character range: {range_token}")
        elif char == '!' and i + 1 < len(regex) and regex[i + 1] == '[':
            # Handle negated character class
            range_start = i
            i += 2  # Skip '!['
            while i < len(regex) and regex[i] != ']':
                i += 1
            if i >= len(regex):
                print(f"    ERROR: Unclosed bracket at {range_start}, regex: {regex}")
                raise ValueError("Unclosed bracket in negated regex")
            range_token = regex[range_start:i + 1]
            output.append(range_token)
            print(f"    Added negated character range: {range_token}")
        elif char == '(':
            stack.append(char)
            print(f"    Pushed '(' to stack: {stack}")
        elif char == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
                print(f"    Popped operator to output: {''.join(output)}")
            if stack and stack[-1] == '(':
                stack.pop()
                print(f"    Popped '(' from stack: {stack}")
            else:
                print("    ERROR: Mismatched parentheses")
        elif char in '*?.|':
            while (stack and stack[-1] != '(' and
                   precedence.get(stack[-1], 0) >= precedence.get(char, 0)):
                output.append(stack.pop())
                print(f"    Popped higher precedence operator: {''.join(output)}")
            stack.append(char)
            print(f"    Pushed operator to stack: {stack}")
        elif char == '!' and (i + 1 < len(regex) and regex[i + 1].isalnum()):
            output.append('!' + regex[i + 1])
            i += 1
            print(f"    Added negated character: !{regex[i]}")

        i += 1

    while stack:
        if stack[-1] == '(':
            stack.pop()
            print("    ERROR: Mismatched parentheses")
        else:
            output.append(stack.pop())
            print(f"    Popped remaining operator: {''.join(output)}")

    result = ''.join(output)
    print(f"Final postfix: {result}")
    return result

def postfix_to_nfa(postfix):
    state_counter = 0
    stack = []
    alphabet = set(chr(i) for i in range(32, 127))

    print(f"\nProcessing postfix: '{postfix}' (length: {len(postfix)})")
    i = 0
    while i < len(postfix):
        char = postfix[i]
        print(f"Step {i}: char = '{char}', Stack size = {len(stack)}")

        if char.isalnum():
            start = state_counter
            state_counter += 1
            accept = state_counter
            state_counter += 1
            nfa = NFA(start, accept)
            nfa.add_transition(start, char, accept)
            stack.append(nfa)
            print(f"  Added char {char}: S{start} --{char}--> S{accept}")
            print(f"  Stack size now: {len(stack)}")

        elif char == '[':
            range_start = i
            i += 1
            while i < len(postfix) and postfix[i] != ']':
                i += 1
            if i >= len(postfix):
                raise ValueError("Unclosed bracket in postfix")
            range_expr = postfix[range_start:i + 1]

            start = state_counter
            state_counter += 1
            accept = state_counter
            state_counter += 1
            nfa = NFA(start, accept)

            j = 1  # Skip first bracket
            allowed_chars = set()
            while j < len(range_expr) - 1:
                if j + 2 < len(range_expr) - 1 and range_expr[j + 1] == '-':
                    start_char, end_char = range_expr[j], range_expr[j + 2]
                    # Ensure range is in correct order
                    if ord(start_char) > ord(end_char):
                        start_char, end_char = end_char, start_char
                    for c in range(ord(start_char), ord(end_char) + 1):
                        allowed_chars.add(chr(c))
                    j += 3
                else:
                    allowed_chars.add(range_expr[j])
                    j += 1

            for c in allowed_chars:
                nfa.add_transition(start, c, accept)
            print(f"  Added range {range_expr}: S{start} --{allowed_chars}--> S{accept}")
            stack.append(nfa)
            print(f"  Stack size now: {len(stack)}")

        elif char == '!' and i + 1 < len(postfix) and postfix[i + 1] == '[':
            # Handle negated character class
            range_start = i
            i += 2  # Skip '!['
            while i < len(postfix) and postfix[i] != ']':
                i += 1
            if i >= len(postfix):
                raise ValueError("Unclosed bracket in negated postfix")
            range_expr = postfix[range_start:i + 1]

            start = state_counter
            state_counter += 1
            accept = state_counter
            state_counter += 1
            nfa = NFA(start, accept)

            j = 2  # Skip '!['
            excluded_chars = set()
            while j < len(range_expr) - 1:
                if j + 2 < len(range_expr) - 1 and range_expr[j + 1] == '-':
                    start_char, end_char = range_expr[j], range_expr[j + 2]
                    # Ensure range is in correct order
                    if ord(start_char) > ord(end_char):
                        start_char, end_char = end_char, start_char
                    for c in range(ord(start_char), ord(end_char) + 1):
                        excluded_chars.add(chr(c))
                    j += 3
                else:
                    excluded_chars.add(range_expr[j])
                    j += 1

            for c in alphabet - excluded_chars:
                nfa.add_transition(start, c, accept)
            print(f"  Added negated range {range_expr}: S{start} --(not {excluded_chars})--> S{accept}")
            stack.append(nfa)
            print(f"  Stack size now: {len(stack)}")

        elif char == '!' and i + 1 < len(postfix) and postfix[i + 1].isalnum():
            i += 1
            negated_char = postfix[i]
            start = state_counter
            state_counter += 1
            accept = state_counter
            state_counter += 1
            nfa = NFA(start, accept)
            for c in alphabet - {negated_char}:
                nfa.add_transition(start, c, accept)
            stack.append(nfa)
            print(f"  Added negated char !{negated_char}: S{start} --(not {negated_char})--> S{accept}")
            print(f"  Stack size now: {len(stack)}")

        elif char == '|':
            if len(stack) < 2:
                print(f"  ERROR: Not enough operands for '|' (stack size: {len(stack)})")
                raise ValueError("Not enough operands for '|'")
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            start = state_counter
            state_counter += 1
            accept = state_counter
            state_counter += 1
            nfa = NFA(start, accept)
            nfa.add_transition(start, None, nfa1.start)
            nfa.add_transition(start, None, nfa2.start)
            nfa.add_transition(nfa1.accept, None, accept)
            nfa.add_transition(nfa2.accept, None, accept)
            nfa.transitions.update(nfa1.transitions)
            nfa.transitions.update(nfa2.transitions)
            stack.append(nfa)
            print(f"  Union: S{start} --ε--> S{nfa1.start}, S{nfa2.start}; S{nfa1.accept}, S{nfa2.accept} --ε--> S{accept}")
            print(f"  Stack size now: {len(stack)}")

        elif char == '*':
            if not stack:
                print(f"  ERROR: No operand for '*' (stack size: {len(stack)})")
                raise ValueError("No operand for '*'")
            nfa1 = stack.pop()
            start = state_counter
            state_counter += 1
            accept = state_counter
            state_counter += 1
            nfa = NFA(start, accept)
            nfa.add_transition(start, None, nfa1.start)
            nfa.add_transition(nfa1.accept, None, accept)
            nfa.add_transition(start, None, accept)
            nfa.add_transition(nfa1.accept, None, nfa1.start)
            nfa.transitions.update(nfa1.transitions)
            stack.append(nfa)
            print(f"  Star: S{start} --ε--> S{nfa1.start}, S{accept}; S{nfa1.accept} --ε--> S{nfa1.start}, S{accept}")
            print(f"  Stack size now: {len(stack)}")

        elif char == '?':
            if not stack:
                print(f"  ERROR: No operand for '?' (stack size: {len(stack)})")
                raise ValueError("No operand for '?'")
            nfa1 = stack.pop()
            start = state_counter
            state_counter += 1
            accept = state_counter
            state_counter += 1
            nfa = NFA(start, accept)
            nfa.add_transition(start, None, nfa1.start)
            nfa.add_transition(nfa1.accept, None, accept)
            nfa.add_transition(start, None, accept)
            nfa.transitions.update(nfa1.transitions)
            stack.append(nfa)
            print(f"  Optional: S{start} --ε--> S{nfa1.start}, S{accept}; S{nfa1.accept} --ε--> S{accept}")
            print(f"  Stack size now: {len(stack)}")

        elif char == '.':
            if len(stack) < 2:
                print(f"  ERROR: Not enough operands for '.' (stack size: {len(stack)})")
                raise ValueError("Not enough operands for '.'")
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            nfa = NFA(nfa1.start, nfa2.accept)
            nfa.add_transition(nfa1.accept, None, nfa2.start)
            nfa.transitions.update(nfa1.transitions)
            nfa.transitions.update(nfa2.transitions)
            stack.append(nfa)
            print(f"  Concat: S{nfa1.accept} --ε--> S{nfa2.start}")
            print(f"  Stack size now: {len(stack)}")

        i += 1

    print(f"Final stack size: {len(stack)}")
    while len(stack) > 1:
        nfa2 = stack.pop()
        nfa1 = stack.pop()
        nfa = NFA(nfa1.start, nfa2.accept)
        nfa.add_transition(nfa1.accept, None, nfa2.start)
        nfa.transitions.update(nfa1.transitions)
        nfa.transitions.update(nfa2.transitions)
        stack.append(nfa)
        print(f"  Implicit concatenation: S{nfa1.accept} --ε--> S{nfa2.start}")
        print(f"  Stack size now: {len(stack)}")

    if len(stack) != 1:
        print(f"Stack still has wrong number of NFAs: {len(stack)}")
        raise ValueError("Invalid regex: incomplete expression")
    return stack[0]

def regex_to_nfa(regex):
    postfix = infix_to_postfix(regex)
    return postfix_to_nfa(postfix)


"""
def visualize_nfa(nfa, filename="nfa"):
    dot = Digraph(comment="NFA")
    dot.attr(rankdir="LR")
    dot.node("start", "", shape="point")
    dot.node(str(nfa.start), "S" + str(nfa.start), shape="circle")
    dot.node(str(nfa.accept), "S" + str(nfa.accept), shape="doublecircle")

    dot.edge("start", str(nfa.start))

    for (from_state, symbol), to_states in nfa.transitions.items():
        for to_state in to_states:
            # Escape special characters for DOT syntax
            if symbol is None:
                label = "ε"
            else:
                # Escape special characters for GraphViz
                label = str(symbol)
                # Replace problematic characters with their escaped versions
                label = label.replace('\\', '\\\\').replace('"', '\\"')
                label = label.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')

            dot.edge(str(from_state), str(to_state), label=label)

    dot.render(filename, view=True, format="png")

"""

def visualize_nfa(nfa, filename="nfa"):
    dot = Digraph(comment="NFA")
    dot.attr(rankdir="LR")
    dot.node("start", "", shape="point")
    dot.node(str(nfa.start), "S" + str(nfa.start), shape="circle")
    dot.node(str(nfa.accept), "S" + str(nfa.accept), shape="doublecircle")

    dot.edge("start", str(nfa.start))

    for (from_state, symbol), to_states in nfa.transitions.items():
        for to_state in to_states:
            # Escape special characters for DOT syntax
            if symbol is None:
                label = "ε"
            else:
                # Escape special characters for GraphViz
                label = str(symbol)
                # Replace problematic characters with their escaped versions
                label = label.replace('\\', '\\\\').replace('"', '\\"')
                label = label.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')

            dot.edge(str(from_state), str(to_state), label=label)

    # Render the graph to a PNG file and return the path
    output_path = dot.render(filename, view=False, format="png", cleanup=False)
    return output_path











"""




if __name__ == "__main__":
    try:
        # Regex examples:
        # 1. Match an optional 'a' followed by any letter, then any character except 'b'
        regex = "a?![b]"
        # 2. Match lowercase and uppercase letter pairs
        # regex = "[a-z][A-Z]"
        # 3. Match any alphanumeric character
        # regex = "[a-zA-Z0-9]"

        print(f"Converting regex: {regex}")

        expanded_regex = insert_concat(regex)
        print(f"Expanded regex with concatenation operators: {expanded_regex}")

        postfix = infix_to_postfix(regex)
        print(f"Postfix notation: {postfix}")

        nfa = regex_to_nfa(regex)

        print(f"\nFinal NFA:")
        print(f"Start state: S{nfa.start}")
        print(f"Accept state: S{nfa.accept}")
        print("Transitions:")
        for (state, symbol), targets in nfa.transitions.items():
            symbol_str = symbol if symbol else "ε"
            print(f"  S{state} --{symbol_str}--> {', '.join(f'S{t}' for t in targets)}")

        visualize_nfa(nfa, "nfa_output")
        print("NFA visualization complete.")
    except ValueError as e:
        print(f"Error: {e}")

"""
