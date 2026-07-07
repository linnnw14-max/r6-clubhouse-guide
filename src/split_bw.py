# -*- coding: utf-8 -*-
# 把可破坏墙长条按游戏里的板块拆成单块(≈27.5px一块,约2.5米)，板间留缝。
# 拆分结果直接写回 data.json 的 marks.bw；每块板可被"强化"(前端按 id 记录)。
import io, json, math, os

D = os.path.dirname(os.path.abspath(__file__)) + "/"
UNIT = 27.5
GAP = 1.4     # 每块板两端各缩 GAP px -> 相邻板间 2.8px 缝
# 人工修正: 某条墙实际板数和 round(len/UNIT) 不符时在这里按 (楼层,原条索引) 指定
# 2026-07-07 用户游戏内核对: 金库<->红楼梯=3块, 后勤室<->建筑工地=2块
OVERRIDES = {("2", 1): 3, ("2", 4): 2}

data = json.load(io.open(D + "data.json", encoding="utf-8"))

def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])

def split_quad(q, n, gap):
    # 找长轴: 边 p0-p1 vs p1-p2
    e01, e12 = dist(q[0], q[1]), dist(q[1], q[2])
    if e01 >= e12:
        A0, A1, B0, B1 = q[0], q[1], q[3], q[2]   # A边p0->p1 与对边 p3->p2 平行
    else:
        A0, A1, B0, B1 = q[1], q[2], q[0], q[3]
    L = dist(A0, A1)
    out = []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        # 板间留缝(首尾不缩太多)
        g0 = gap / L if i > 0 else 0.3 / L
        g1 = gap / L if i < n - 1 else 0.3 / L
        s0, s1 = t0 + g0, t1 - g1
        def lerp(P, Q, t): return [round(P[0] + (Q[0]-P[0]) * t, 1), round(P[1] + (Q[1]-P[1]) * t, 1)]
        out.append([lerp(A0, A1, s0), lerp(A0, A1, s1), lerp(B0, B1, s1), lerp(B0, B1, s0)])
    return out

total_before = total_after = 0
for f in data["floors"]:
    mk = data["floors"][f].get("marks") or {}
    bw = mk.get("bw")
    if not bw: continue
    newbw = []
    for i, q in enumerate(bw):
        e01, e12 = dist(q[0], q[1]), dist(q[1], q[2])
        L = max(e01, e12)
        n = OVERRIDES.get((f, i)) or max(1, round(L / UNIT))
        newbw.extend(split_quad(q, n, GAP))
        total_before += 1; total_after += n
        print("%s bw%-2d len=%5.1f -> %d 块" % (f, i, L, n))
    mk["bw"] = newbw
    data["floors"][f]["marks"] = mk

io.open(D + "data.json", "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
print("共 %d 条 -> %d 块板" % (total_before, total_after))
