# -*- coding: utf-8 -*-
# 用 r6calls.com 的现役会所数据自动生成格子：
# 1) 四层官方俯视图(白墙) → 墙掩码 → 从 r6calls 房名坐标(种子)多源BFS填房间
# 2) 用户已校准房名 ↔ r6calls 房名 做全局仿射对齐(our 1374x1048 ↔ pic 1024)
# 3) 逐格采样生成 grid + 重建 labels/rooms + warp 现役图当描图底图
import io, json, os, math
import numpy as np
from PIL import Image, ImageFilter

D = os.path.dirname(os.path.abspath(__file__)) + "/"
SP = os.path.dirname(D.rstrip("/")) + "/"   # scratchpad
MAPW, MAPH, CELL = 1374, 1048, 10
GW, GH = 138, 105
K, K2, MAXIT = 6, 12, 340

PICS = {"B": "img_05.png", "1": "img_15.png", "2": "img_29.png", "R": "img_45.png"}
HKEY = {"B": "F0", "1": "F1", "2": "F2", "R": "F3"}
CH = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
CYCLE = ["#4C9BE8", "#3FBFA0", "#B07FD8", "#6FBF5F", "#45C0E8", "#D8B04A", "#E07A9E", "#8E9AF0", "#A8C25A", "#E8935B", "#5FD3B8", "#C98BD6"]
EXTC = ["#4A6172", "#3F6D63", "#566B85", "#5E7A6E"]
GOLD_C, CORR_C = "#F0A93F", "#6E8296"

# 每层房间表: (r6calls名, cn, en, kind, k, 色型)  色型: gold/corr/room/ext
ROOMS = {
"2": [
 ("Cash","金库","Cash Room","目标·北","obj","gold"),
 ("CCTV","监控室","CCTV Room","目标·南","obj","gold"),
 ("Gym","健身房","Gym","","att","gold"),
 ("Bedroom","卧室","Bedroom","进攻集结","att","gold"),
 ("Bathroom","洗手间","Bathroom","","room","room"),
 ("Secret","密室","Secret Stash","","room","room"),
 ("Office","后勤室","Office","hatch·垂直","room","room"),
 ("Construction","建筑工地","Construction","","room","room"),
 ("Garage","车库","Garage","挑空·上层","room","room"),
 ("Garage Stairs","车库楼梯","Garage Stairs","","room","corr"),
 ("Red Stairs","红楼梯","Red Stairs","","room","corr"),
 ("Main Stairs","主楼梯","Main Stairs","","room","corr"),
 ("Bedroom Hallway","卧室走廊","B.Hallway","","room","corr"),
 ("Gym Hallway","健身房走廊","Gym Hallway","","room","corr"),
 ("Balcony","东天台","Balcony","室外","ext","ext"),
],
"1": [
 ("Bar","酒吧","Bar","目标","obj","gold"),
 ("Stock","大贮藏室","Stock Room","目标","obj","gold"),
 ("Kitchen","厨房","Kitchen","","room","room"),
 ("Lounge","休息室","Lounge","","room","room"),
 ("Strip Club","脱衣舞厅","Strip Club","","room","room"),
 ("Pool","台球室","Pool","","room","room"),
 ("Toilets","厕所","Toilets","","room","room"),
 ("Lobby","大堂","Lobby","","room","room"),
 ("Stage","舞台","Stage","","room","room"),
 ("Changing","更衣室","Changing","","room","room"),
 ("Storage","储藏室","Storage","","room","room"),
 ("Garage","车库","Garage","","room","room"),
 ("Garage Stairs","车库楼梯","Garage Stairs","","room","corr"),
 ("Main Stairs","主楼梯","Main Stairs","","room","corr"),
 ("Red Stairs","红楼梯","Red Stairs","","room","corr"),
 ("Blue Stairs","蓝楼梯","Blue Stairs","","room","corr"),
 ("Kitchen Hallway","厨房走廊","K.Hallway","","room","corr"),
 ("Strip Hallway","舞厅走廊","S.Hallway","","room","corr"),
],
"B": [
 ("Church","教堂","Church","目标","obj","gold"),
 ("Armory","军械库","Armory","目标","obj","gold"),
 ("Blue Stairs","蓝楼梯","Blue Stairs","","room","corr"),
 ("Church Hallway","教堂走廊","Ch.Hallway","","room","corr"),
 ("Main Stairs","主楼梯","Main Stairs","","room","corr"),
 ("Tunnel","隧道","Tunnel","","room","corr"),
 ("Blue","蓝色通道","Blue","","room","corr"),
 ("Bike","车库","Bike","","room","room"),
 ("Bike Hallway","车库走廊","Bike Hallway","","room","corr"),
 ("Container","货柜房","Container","","room","room"),
],
"R": [
 ("Middle Roof","中央屋顶","Middle Roof","室外","ext","ext"),
 ("East Roof","东屋顶","East Roof","室外","ext","ext"),
 ("Water Tank","水塔","Water Tank","室外","ext","ext"),
],
}
# 对齐锚点: (楼层, our房名cn, r6calls名)
ANCHORS = [
 ("2","金库","Cash"),("2","监控室","CCTV"),("2","健身房","Gym"),("2","卧室","Bedroom"),
 ("2","洗手间","Bathroom"),("2","密室","Secret"),("2","后勤室","Office"),("2","建筑工地","Construction"),
 ("2","车库","Garage"),("2","车库楼梯","Garage Stairs"),("2","主楼梯","Main Stairs"),("2","卧室走廊","Bedroom Hallway"),
 ("1","酒吧","Bar"),("1","大贮藏室","Stock"),("1","厨房","Kitchen"),("1","休息室","Lounge"),
 ("1","脱衣舞厅","Strip Club"),("1","台球室","Pool"),("1","厕所","Toilets"),("1","主楼梯","Main Stairs"),("1","车库","Garage"),
 ("B","教堂","Church"),("B","军械库","Armory"),("B","蓝楼梯","Blue Stairs"),("B","教堂走廊","Church Hallway"),
 ("B","隧道","Tunnel"),("B","主楼梯","Main Stairs"),("B","车库","Bike"),("B","蓝色通道","Blue"),
 ("R","中央屋顶","Middle Roof"),("R","东屋顶","East Roof"),
]

harvest = json.load(io.open(SP + "r6c_harvest.json", encoding="utf-8"))
data = json.load(io.open(D + "data.json", encoding="utf-8"))

def hpos(f, name):
    pts = [(x, y) for n, x, y in harvest[HKEY[f]] if n == name]
    if not pts: return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

def opos(f, cn):
    for l in data["floors"][f]["labels"]:
        if l["cn"] == cn: return (l["x"], l["y"])
    return None

# ---- 全局仿射 our->pic ----
pairs = []
for f, cn, rn in ANCHORS:
    o, h = opos(f, cn), hpos(f, rn)
    if o and h: pairs.append((o, h, f, cn))
X = np.array([[o[0], o[1], 1] for o, h, f, cn in pairs])
U = np.array([h[0] for o, h, f, cn in pairs]); V = np.array([h[1] for o, h, f, cn in pairs])
def fit(X, U, V):
    cu, *_ = np.linalg.lstsq(X, U, rcond=None)
    cv, *_ = np.linalg.lstsq(X, V, rcond=None)
    return cu, cv
cu, cv = fit(X, U, V)
res = np.hypot(X @ cu - U, X @ cv - V)
print("anchors:", len(pairs), "residual px: mean %.1f max %.1f" % (res.mean(), res.max()))
keep = res < 45
for (o, h, f, cn), r, k_ in zip(pairs, res, keep):
    if not k_: print("  drop outlier:", f, cn, "%.1f" % r)
X, U, V = X[keep], U[keep], V[keep]
cu, cv = fit(X, U, V)
res = np.hypot(X @ cu - U, X @ cv - V)
print("refit:", len(U), "residual px: mean %.1f max %.1f" % (res.mean(), res.max()))
def our2pic(x, y): return (cu[0]*x + cu[1]*y + cu[2], cv[0]*x + cv[1]*y + cv[2])
Ainv = np.linalg.inv(np.array([[cu[0], cu[1]], [cv[0], cv[1]]]))
def pic2our(u, v):
    d0, d1 = u - cu[2], v - cv[2]
    return (Ainv[0,0]*d0 + Ainv[0,1]*d1, Ainv[1,0]*d0 + Ainv[1,1]*d1)

def grow(lab, free, iters):
    for _ in range(iters):
        nb = np.zeros_like(lab)
        for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1)):
            s = np.roll(lab, sh, axis=ax)
            if ax == 0: s[0 if sh == 1 else -1, :] = 0
            else: s[:, 0 if sh == 1 else -1] = 0
            nb = np.where((nb == 0) & (s > 0), s, nb)
        g = (lab == 0) & free & (nb > 0)
        if not g.any(): break
        lab = np.where(g, nb, lab)
    return lab

newfloors = {}
refimgs = {}
for f in ["R", "2", "1", "B"]:
    im = Image.open(SP + "r6c_imgs/" + PICS[f]).convert("RGBA")
    a = np.asarray(im).astype(np.int16)
    rgb, alpha = a[..., :3], a[..., 3]
    content = (alpha > 10) & (rgb.max(2) > 18)   # 排除透明和纯黑背景
    wall = (rgb.min(2) > 225) & ((rgb.max(2) - rgb.min(2)) < 25) & content
    H_, W_ = wall.shape
    wallD = np.asarray(Image.fromarray((wall*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2*K+1))) > 0
    # 楼外 = 从边界经 ~wallD2 可达(含室外地面/透明区)
    wallD2 = np.asarray(Image.fromarray((wall*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2*K2+1))) > 0
    labO = np.zeros((H_, W_), np.int16)
    for sl in (np.s_[0, :], np.s_[-1, :], np.s_[:, 0], np.s_[:, -1]):
        labO[sl] = np.where(~wallD2[sl], 1, 0)
    labO = grow(labO, ~wallD2, 1200)
    outside = np.asarray(Image.fromarray(((labO>0)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2*(K2-K)+1))) > 0

    rooms = ROOMS[f]
    seeds = []   # (idx, x, y)
    for i, (rn, cn, en, kind, kk, ct) in enumerate(rooms, 1):
        pts = [(x, y) for n, x, y in harvest[HKEY[f]] if n == rn]
        for p in pts: seeds.append((i, p[0], p[1]))
    lab = np.zeros((H_, W_), np.int16)
    n_int = len(rooms)
    freeI = content & ~wallD & ~outside
    freeE = content & ~wallD
    OPEN0 = {"B": ["隧道", "货柜房"]}.get(f, [])
    for i, x, y in seeds:
        ct = rooms[i-1][5]
        openroom = (ct == "ext") or (rooms[i-1][1] in OPEN0)
        target = freeE if openroom else freeI
        px, py = int(round(x)), int(round(y))
        if not (0 <= px < W_ and 0 <= py < H_): continue
        if not target[py, px]:
            ok = False
            fb = (content & ~wall) if openroom else (content & ~wall & ~outside)
            for tgt in (target, fb):  # 窄房间(隧道等)被墙膨胀封死时用不膨胀的兜底
                for r in range(2, 90, 2):
                    ys, xs = np.mgrid[max(0,py-r):min(H_,py+r), max(0,px-r):min(W_,px+r)]
                    fm = tgt[ys, xs]
                    if fm.any():
                        j = np.flatnonzero(fm.ravel())[0]; py, px = ys.ravel()[j], xs.ravel()[j]; ok = True; break
                if ok: break
            if not ok: print("  !! seed lost:", f, rooms[i-1][1]); continue
        lab[py, px] = i
    # 室内先扩；ext 和「开口房间」(隧道/货柜房，一头通图外被判楼外)在受限开放模式下扩
    OPEN = {"B": ["隧道", "货柜房"]}.get(f, [])
    isext = np.array([rooms[i-1][5] == "ext" or rooms[i-1][1] in OPEN for i in range(1, n_int+1)])
    lab_int = np.where(np.isin(lab, np.flatnonzero(~isext)+1), lab, 0)
    lab_int = grow(lab_int, freeI, MAXIT)
    lab_int = grow(lab_int, content & ~wall & ~outside, K+2)
    lab_ext = np.where(np.isin(lab, np.flatnonzero(isext)+1), lab, 0)
    lab_ext = grow(lab_ext, content & ~wallD & (lab_int == 0), 120)
    lab_ext = grow(lab_ext, content & ~wall & (lab_int == 0), K+2)
    lab = np.where(lab_int > 0, lab_int, lab_ext)
    # 小房间抢救
    sizes = np.bincount(lab.ravel(), minlength=n_int+1)
    for i in range(1, n_int+1):
        if 0 < sizes[i] < 500 and rooms[i-1][5] != "ext":
            labi = np.where(lab == i, np.int16(i), np.int16(0))
            fr = content & ~wall & ~outside & ((lab == 0) | (lab == i))
            labi = grow(labi, fr, 70)
            lab = np.where((labi > 0) & (lab == 0), np.int16(i), lab)
            print("  rescue:", f, rooms[i-1][1], "->", int((lab==i).sum()))
    sizes = np.bincount(lab.ravel(), minlength=n_int+1)
    for i in range(1, n_int+1):
        print("  %s %-6s %6d px" % (f, rooms[i-1][1], sizes[i]))

    # ---- 逐格采样(our 网格中心 -> pic) ----
    rows = []
    for gy in range(GH):
        row = []
        for gx in range(GW):
            votes = {}
            for ox, oy in ((5,5),(2,2),(8,2),(2,8),(8,8)):
                u, v = our2pic(gx*CELL+ox, gy*CELL+oy)
                ui, vi = int(round(u)), int(round(v))
                if 0 <= ui < W_ and 0 <= vi < H_:
                    li = int(lab[vi, ui])
                    if li > 0: votes[li] = votes.get(li, 0) + 1
            best = max(votes.items(), key=lambda kv: kv[1]) if votes else (0, 0)
            row.append("." if best[1] < 3 else CH[best[0]-1])
        rows.append("".join(row))

    # rooms 调色板
    ci, ei = 0, 0
    palette = []
    for i, (rn, cn, en, kind, kk, ct) in enumerate(rooms):
        if ct == "gold": c = GOLD_C
        elif ct == "corr": c = CORR_C
        elif ct == "ext": c = EXTC[ei % len(EXTC)]; ei += 1
        else: c = CYCLE[ci % len(CYCLE)]; ci += 1
        palette.append({"ch": CH[i], "cn": cn, "c": c, "t": ct if ct in ("gold","corr","ext") else "room"})

    # labels：r6calls 位置 -> our 空间
    labels = []
    for i, (rn, cn, en, kind, kk, ct) in enumerate(rooms):
        h = hpos(f, rn)
        if not h: continue
        x, y = pic2our(h[0], h[1])
        labels.append({"cn": cn, "en": en, "kind": kind, "x": int(round(x)), "y": int(round(y)), "k": kk})
    # R 层保留用户的中庭天台标签(俯视可见)
    if f == "R":
        old = opos("R", "中庭天台")
        if old: labels.append({"cn": "中庭天台", "en": "C.Sub-roof", "kind": "室外", "x": int(old[0]), "y": int(old[1]), "k": "ext"})

    # bbox: 有格子的范围 + labels
    ys, xs = np.nonzero(np.array([[c != "." for c in r] for r in rows]))
    if len(xs):
        x0, x1 = xs.min()*CELL, (xs.max()+1)*CELL
        y0, y1 = ys.min()*CELL, (ys.max()+1)*CELL
    else:
        x0, y0, x1, y1 = 400, 250, 1100, 850
    for l in labels:
        x0 = min(x0, l["x"]-40); x1 = max(x1, l["x"]+40)
        y0 = min(y0, l["y"]-30); y1 = max(y1, l["y"]+30)
    x0 = max(0, int(x0)-10); y0 = max(0, int(y0)-10)
    x1 = min(MAPW, int(x1)+10); y1 = min(MAPH, int(y1)+10)

    # 下包点：改用 r6calls 的权威位置(与新房间形状同一坐标体系)
    BOMBN = {"2": ["1A","1B","2A","2B"], "1": ["3A","3B"], "B": ["4A","4B"], "R": []}
    bombs = []
    for bn in BOMBN[f]:
        h = hpos(f, bn)
        if h:
            x, y = pic2our(h[0], h[1])
            bombs.append({"t": bn, "x": int(round(x)), "y": int(round(y))})
    if not bombs: bombs = data["floors"][f]["bombs"] if f != "R" else []

    newfloors[f] = {
        "note": data["floors"][f]["note"],
        "bbox": {"x": x0, "y": y0, "w": x1-x0, "h": y1-y0},
        "rooms": palette, "grid": rows,
        "labels": labels,
        "bombs": bombs,
    }

    # ---- 描图底图: 现役图 warp 到 our 空间 ----
    rgbim = Image.open(SP + "r6c_imgs/" + PICS[f]).convert("RGB")
    coeffs = (cu[0], cu[1], cu[2], cv[0], cv[1], cv[2])
    ref = rgbim.transform((MAPW, MAPH), Image.AFFINE, coeffs, resample=Image.BILINEAR)
    ref.save(D + "ref_%s.webp" % f, "WEBP", quality=55, method=6)
    refimgs[f] = os.path.getsize(D + "ref_%s.webp" % f)//1024

data["floors"] = newfloors
io.open(D + "data.json", "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
print("data.json updated; ref imgs KB:", refimgs)
