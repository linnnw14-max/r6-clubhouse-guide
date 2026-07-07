# -*- coding: utf-8 -*-
# 套用用户从校准工具导出的 v2 结果：更新 data.json → 自动递增 edit.js 的 DATAVER → 重新生成两个页面
# 用法: python3 apply_v2.py 用户结果.json   (文件内容=用户粘贴的整段, 允许带前置说明文字, 从第一个"{"起解析)
import io, json, os, re, sys, subprocess

D = os.path.dirname(os.path.abspath(__file__)) + "/"
FMAP = {"屋顶Roof": "R", "二楼2F": "2", "一楼1F": "1", "地下室B": "B"}

raw = io.open(sys.argv[1], encoding="utf-8").read()
exp = json.loads(raw[raw.index("{"):])
assert exp.get("version", "").startswith("r6club-calib-v2"), "不是 v2 导出"

data = json.load(io.open(D + "data.json", encoding="utf-8"))

for fn, o in exp["floors"].items():
    f = FMAP[fn]
    F = data["floors"][f]
    F["labels"] = [{"cn": l["cn"], "en": l.get("en", ""), "kind": l.get("kind", ""),
                    "x": l["x"], "y": l["y"], "k": l.get("k", "room")} for l in o["labels"]]
    F["bombs"] = [{"t": b["t"], "x": b["x"], "y": b["y"]} for b in o["bombs"]]
    if "rooms" in o:
        F["rooms"] = [{"ch": r["ch"], "cn": r["cn"], "c": r["c"], "t": r.get("t", "room")} for r in o["rooms"]]
    if "grid" in o:
        assert len(o["grid"]) == data["gh"] and all(len(r) == data["gw"] for r in o["grid"]), "grid 尺寸不对"
        F["grid"] = o["grid"]
# 2026-07-07 装修点位已整体下线（hs 存档在 hs_backup_2026-07-07.json），导出里即使带 setup2F 也忽略

io.open(D + "data.json", "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
print("data.json updated")

# 套用过用户描的格子后，编辑器基线恢复为"跟 data.json 一致"（关掉一次性的空白重描模式）
gp = io.open(D + "gen_pages.py", encoding="utf-8").read()
if "EDITOR_GRID_BLANK = True" in gp:
    io.open(D + "gen_pages.py", "w", encoding="utf-8").write(gp.replace("EDITOR_GRID_BLANK = True", "EDITOR_GRID_BLANK = False", 1))
    print("EDITOR_GRID_BLANK -> False")

# DATAVER 由 gen_pages.py 按编辑器基线哈希自动生成，数据一变存档自动换代，无需手动 bump
subprocess.check_call(["python3", D + "gen_pages.py"])
print("pages regenerated")
