import random

def gen_random_string(weight):
    if random.random() < weight:
        return random.choice("012345678")
    else:
        return random.choice("+*") + gen_random_string(1 - (1 - weight) * 0.99) + gen_random_string(1 - (1 - weight) * 0.99)

def parse(string):
    if string[0] in "+*":
        return [string.pop(0), parse(string), parse(string)]
    else:
        return string.pop(0)

def unparse(tree):
    if isinstance(tree, str):
        return tree
    return unparse(tree[1]) + unparse(tree[2]) + tree[0]

def depth(obj):
    if isinstance(obj, list):
        return max(map(depth, obj)) + 1
    else:
        return 0

index = 0

while index <= 30:
    string = gen_random_string(0.3)
    if len(string) > 100:
        tree = parse(list(string))
        if depth(tree) < 100:
            index += 1
            with open("p1in%d.txt" % index, "w") as f:
                f.write(string)
            with open("p1out%d.txt" % index, "w") as f:
                f.write(unparse(tree))
