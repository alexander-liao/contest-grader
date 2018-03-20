import itertools

N, M = map(int, input().split())
products = [tuple(map(int, input().split())) for _ in range(N)]

DP = [0] + [-1] * M

revenues = []

for revenue, cost in products:
	if revenue <= M:
		DP[revenue] = min(DP[revenue], cost) if DP[revenue] != -1 else cost
		if revenue not in revenues:
			revenues.append(revenue)

max_achievable = 0

for _ in range(N):
	for a, b in itertools.product(revenues, revenues):
		if a + b <= M:
			if a + b not in revenues:
				revenues.append(a + b)
			if DP[a + b] == -1 or DP[a] + DP[b] < DP[a + b]:
				DP[a + b] = DP[a] + DP[b]

print(DP[M])