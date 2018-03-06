from random import randint
for a in range(50):
    _i = open("p1in%d.txt"%(a+1),"w+")
    N = randint(21,10**5)
    _i.write(str(N) + "\r\n")
    for b in range(N):
        val = randint(1,75)
        sub = 1
        while val - sub >= 1:
            val = randint(1,75)
            sub += 1
        _i.write(str(val)+" ")
    _i.write("\r\n"+str(randint(1,75))+"\r\n")
