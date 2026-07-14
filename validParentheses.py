def isValid(s: str):
    stack = []
    start = '({['
    mapping = {
        ")": "(",
        "}": "{",
        "]": "[",
    }

    for char in s:
        if char in mapping:
            top_element = stack.pop() if stack else '#'
            if mapping[char] != top_element:
                return False
        elif char in start:
            stack.append(char)

    return not stack

print(isValid('123({[]})'))
print(isValid('([{'))
print(isValid(')}]'))