# -*- coding: utf-8 -*-
# 把 workflow 产出的 JSON 配置 -> mapcfg.py 的 MAPCFG[...] Python 块; 并对照 harvest 校验房名
import json, os, re, sys
D=os.path.dirname(os.path.abspath(__file__))+"/"
configs=json.load(open(D+"cfginput/configs_out.json"))
FIX_MAPCN={"house":"小屋"}   # House=小屋 (别墅是Villa)
FIX_MAPEN={"house":"House"}

def pytuple(t):
    return "(" + ",".join('"%s"'%(s.replace('\\','\\\\').replace('"','\\"')) for s in t) + ")"

def emit(c):
    mid=c["map"]
    mapcn=FIX_MAPCN.get(mid,c["mapcn"]); mapen=FIX_MAPEN.get(mid,c["mapen"])
    order=c["order"]; default=c["default"]
    L=[]
    L.append('MAPCFG["%s"] = {'%mid)
    L.append(' "mapcn":"%s","mapen":"%s",'%(mapcn,mapen))
    L.append(' "order":%s, "default":"%s",'%(json.dumps(order),default))
    L.append(' "names":%s,'%json.dumps(c["names"],ensure_ascii=False))
    L.append(' "en":%s,'%json.dumps(c["en"],ensure_ascii=False))
    L.append(' "notes":%s,'%json.dumps(c["notes"],ensure_ascii=False))
    sites=",".join('{"id":"%s","f":"%s","n":"%s"}'%(s["id"],s["f"],s["n"]) for s in c["sites"])
    L.append(' "sites":[%s],'%sites)
    L.append(' "bombs":%s,'%json.dumps(c["bombs"],ensure_ascii=False))
    L.append(' "rooms":{')
    for f in order:
        rs=c["rooms"].get(f,[])
        if not rs: continue
        inner=",".join(pytuple(t) for t in rs)
        L.append('  "%s":[%s],'%(f,inner))
    L.append(' },')
    L.append('}')
    return "\n".join(L)

report=[]
for c in configs:
    mid=c["map"]
    harv=json.load(open(D+"%s_harvest.json"%mid))
    issues=[]
    for f,rs in c["rooms"].items():
        hv=set(n for n,x,y in harv.get("F"+f,[]))
        cfgnames=[t[0] for t in rs]
        # room in config but not in harvest -> won't render
        missing=[n for n in cfgnames if n not in hv]
        # harvest room (non marker) not in config -> unlabeled
        unl=[n for n in hv if n not in set(cfgnames) and not re.match(r'^\d[A-B]?$',n)]
        dup=[n for n in cfgnames if cfgnames.count(n)>1]
        if missing: issues.append("F%s 配置里有但harvest无(不会渲染): %s"%(f,missing))
        if unl: issues.append("F%s harvest有但配置漏(无标签): %s"%(f,sorted(set(unl))))
        if dup: issues.append("F%s 重复房名: %s"%(f,sorted(set(dup))))
    report.append((mid,issues))

print("===== 校验 =====")
for mid,issues in report:
    if not issues: print(mid,"OK ✓")
    else:
        print(mid,"⚠")
        for i in issues: print("   ",i)

if "--write" in sys.argv:
    with open(D+"mapcfg.py","a",encoding="utf-8") as f:
        f.write("\n\n# ===== 快速匹配经典老图 (house/hereford/plane/yacht/tower) =====\n")
        for c in configs:
            f.write("\n"+emit(c)+"\n")
    print("\n-> appended 5 entries to mapcfg.py")
