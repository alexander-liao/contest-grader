N,M = map(int,input().split())
costs = {}
for item in [list(map(float,input().split())) for _ in range(N)]:
  if item[0] in costs:
    costs[item[0]] = min(costs[item[0]],item[1])
  else:
    costs[item[0]] = item[1]
inf = float("inf")
dp = [inf for _ in range(M+1)]
dp[0] = 0
for cost in range(1,M+1):
  if cost in costs:
    dp[cost] = costs[cost]
  for partial in range(1,cost):
    if dp[partial] != inf and dp[cost-partial] != inf:
      dp[cost] = min(dp[cost],dp[partial]+dp[cost-partial])
if dp[M] != inf:
  print(dp[M])
else:
  print(-1)