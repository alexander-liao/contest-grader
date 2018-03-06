from random import randint
subtasks = [100,1000,10**5]
for a in range(3):
    for b in range(50):
        _i = open("p3in%d.txt"%(a*50+b+1),"w+")
        N = subtasks[a]
        M = randint(0,N*4)
        _i.write(str(N) + " " + str(M) + "\r\n")
        pairs = set()
        for c in range(M):
            x,y = randint(1,N),randint(1,N)
            while (x,y) in pairs or x == y:
                x,y = randint(1,N),randint(1,N)
            pairs.add((x,y))
            _i.write(str(x)+" "+str(y)+"\r\n")
