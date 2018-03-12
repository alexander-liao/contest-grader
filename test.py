def parse(string):
    if string[0] in "+*":
        return [string.pop(0), parse(string), parse(string)]
    else:
        return string.pop(0)

def unparse(tree):
    if isinstance(tree, str):
        return tree
    return unparse(tree[1]) + unparse(tree[2]) + tree[0]

print(unparse(parse(list(input()))))
