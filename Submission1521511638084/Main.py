N,M = map(int,input().split())
current = M
best = M
for bribe,pot in [map(int,input().split()) for _ in range(N)]:
  if current >= bribe:
    current += pot - bribe
  else:
    break
  best = max(best,current)
print(best)