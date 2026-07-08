# -*- coding: utf-8 -*-
# 把可破坏墙长条按游戏板块拆成单块(≈27.5px一块,约2.5米)，板间留缝。写回对应 data 文件 marks.bw。
# 用法: python3 split_bw.py [data文件, 默认 data.json]
# 注意: 非幂等! 已拆过的会再拆碎。脚本用 data['bwSplit'] 标记, 已拆则拒绝重跑。
# 板数不对 → 在 OVERRIDES 里按 (map, 楼层, 原条索引) 指定, 然后从原始 marks 重新拆(club 走 apply_marks 还原, kafe 走 build_kafe.py 重建)。
import io, json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__)) + "/"
UNIT = 27.5
GAP = 1.4
DATAFILE = sys.argv[1] if len(sys.argv) > 1 else "data.json"

# 用户游戏内核对的板数修正: {map: {(楼层,原条索引): 块数}}
OVERRIDES = {
    "club": {("2", 1): 3, ("2", 4): 2},          # 金库↔红楼梯=3, 后勤室↔建筑工地=2
    "kafe": {("1", 3): 2},                        # 1F 冷冻库↔白楼梯=2
}

data = json.load(io.open(D + DATAFILE, encoding="utf-8"))
mapid = data.get("map", "club")
ov = OVERRIDES.get(mapid, {})
assert not data.get("bwSplit"), "%s 的 bw 已拆过, 别重跑(会拆碎); 要改板数请从原始 marks 重建" % DATAFILE

def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])

def split_quad(q, n, gap):
    e01, e12 = dist(q[0], q[1]), dist(q[1], q[2])
    if e01 >= e12: A0, A1, B0, B1 = q[0], q[1], q[3], q[2]
    else: A0, A1, B0, B1 = q[1], q[2], q[0], q[3]
    L = dist(A0, A1); out = []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        g0 = gap / L if i > 0 else 0.3 / L
        g1 = gap / L if i < n - 1 else 0.3 / L
        s0, s1 = t0 + g0, t1 - g1
        def lerp(P, Q, t): return [round(P[0] + (Q[0]-P[0]) * t, 1), round(P[1] + (Q[1]-P[1]) * t, 1)]
        out.append([lerp(A0, A1, s0), lerp(A0, A1, s1), lerp(B0, B1, s1), lerp(B0, B1, s0)])
    return out

tb = ta = 0
for f in data["floors"]:
    mk = data["floors"][f].get("marks") or {}
    bw = mk.get("bw")
    if not bw: continue
    newbw = []
    for i, q in enumerate(bw):
        L = max(dist(q[0], q[1]), dist(q[1], q[2]))
        n = ov.get((f, i)) or max(1, round(L / UNIT))
        newbw.extend(split_quad(q, n, GAP))
        tb += 1; ta += n
    mk["bw"] = newbw
    data["floors"][f]["marks"] = mk

data["bwSplit"] = True
io.open(D + DATAFILE, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
print("%s (%s): %d 条 -> %d 块板" % (DATAFILE, mapid, tb, ta))
