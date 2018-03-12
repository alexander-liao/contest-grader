for a in range(1,151):
    f = open("p3out%d.txt"%a)
    if f.readline() == -1:
        print("booga")
