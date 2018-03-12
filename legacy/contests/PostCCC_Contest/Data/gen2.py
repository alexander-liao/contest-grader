from random import randint
fib = [1,1]
for a in range(2,10**5):
    fib.append(fib[a-1]+fib[a-2])
subtasks = [100,1000,10**5]
for a in range(3):
    for b in range(50):
        i=open("p2in%d.txt"%(a*50+b+1),"w+")
        o = open("p2out%d.txt"%(a*50+b+1),"w+")
        n = randint(subtasks[a]-subtasks[a]//10,subtasks[a])
        i.write(str(n)+"\r\n")
        o.write(str(fib[n-1]%(10**9+7))+"\r\n")
