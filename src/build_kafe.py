# -*- coding: utf-8 -*-
# 咖啡馆(Kafe Dostoyevsky) 一体化构建：房间填充 + 标注提取 + 墙板拆分 -> data_kafe.json + ref_kafe_*.webp
# 复用会所验证过的算法。坐标系=r6calls 原图纯平移(our=pic+偏移)。
import io, json, os, math, re, base64
import numpy as np
from PIL import Image, ImageFilter
import xml.etree.ElementTree as ET

D = os.path.dirname(os.path.abspath(__file__)) + "/"
SP = os.path.dirname(D.rstrip("/")) + "/"
MAPW, MAPH, CELL = 1374, 1048, 10
GW, GH = 138, 105
K, K2, MAXIT = 6, 12, 340
SVGF = SP + "kafe_r6calls.svg"
PIC = {"x0": 1115.581, "y0": 456.655, "w": 361.244}  # kafe 图片矩形(根坐标)
IMGDIR = SP + "kafe_imgs/"

CH = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
CYCLE = ["#4C9BE8", "#3FBFA0", "#B07FD8", "#6FBF5F", "#45C0E8", "#D8B04A", "#E07A9E", "#8E9AF0", "#A8C25A", "#E8935B", "#5FD3B8", "#C98BD6"]
EXTC = ["#4A6172", "#3F6D63", "#566B85", "#5E7A6E"]
GOLD_C, CORR_C = "#F0A93F", "#6E8296"

# 楼层：key -> (harvest key, pic文件, r6calls图层号, 楼层中文, note)
FLOORS_META = {
 "4": ("F4", "4-pic.png", "4", "屋顶", "屋顶层 · 天窗"),
 "3": ("F3", "3-pic.png", "3", "三楼", "鸡尾酒吧 + 酒吧 + 雪茄室"),
 "2": ("F2", "2-pic.png", "2", "二楼", "采矿室 + 阅读室 + 餐厅"),
 "1": ("F1", "1-pic.png", "1", "一楼", "烹饪 + 面包房 + 餐厅"),
}
ORDER = ["4", "3", "2", "1"]  # 显示从上到下

# 每层房间: (r6calls名, cn, en, kind, k, 色型)  色型 gold/corr/room/ext
ROOMS = {
"1": [
 ("Cooking","烹饪室","Cooking","目标","obj","gold"),
 ("Service","服务区","Service","目标","obj","gold"),
 ("Bakery","面包房","Bakery","","room","room"),
 ("Small Bakery","小面包房","Small Bakery","","room","room"),
 ("Prep","备餐区","Prep","","room","room"),
 ("Freezer","冷冻库","Freezer","","room","room"),
 ("Restaurant","餐厅","Restaurant","","room","room"),
 ("Bottom Bar","底层吧台","Bottom Bar","","room","room"),
 ("VIP","VIP室","VIP","","room","room"),
 ("Reception","接待处","Reception","","room","room"),
 ("Coat","衣帽间","Coat","","room","room"),
 ("Garage","车库","Garage","","room","room"),
 ("Bakery Corridor","面包房走廊","B.Corridor","","room","corr"),
 ("VIP Corridor","VIP走廊","VIP Corridor","","room","corr"),
 ("Red Stairs","红楼梯","Red Stairs","","room","corr"),
 ("White Stairs","白楼梯","White Stairs","","room","corr"),
 ("Wood Stairs","木楼梯","Wood Stairs","","room","corr"),
 ("Terrace","露台","Terrace","室外","ext","ext"),
],
"2": [
 ("Mining","采矿室","Mining","目标","obj","gold"),
 ("Reading","阅读室","Reading","目标","obj","gold"),
 ("Dining","餐厅","Dining","目标","obj","gold"),
 ("Fireplace","壁炉厅","Fireplace","","room","room"),
 ("Train","火车博物馆","Train","","room","room"),
 ("Pillar","柱厅","Pillar","","room","room"),
 ("Main","主厅","Main","","room","room"),
 ("Laundry","洗衣房","Laundry","","room","room"),
 ("Mining Corridor","采矿室走廊","M.Corridor","","room","corr"),
 ("Reading Corridor","阅读室走廊","R.Corridor","","room","corr"),
 ("Red Corridor","红色走廊","Red Corridor","","room","corr"),
 ("TerraceEntrance","露台入口","Terrace Ent.","","room","corr"),
 ("Red Stairs","红楼梯","Red Stairs","","room","corr"),
 ("White Stairs","白楼梯","White Stairs","","room","corr"),
 ("Wood Stairs","木楼梯","Wood Stairs","","room","corr"),
 ("Terrace","露台","Terrace","室外","ext","ext"),
],
"3": [
 ("Cocktail","鸡尾酒吧","Cocktail","目标","obj","gold"),
 ("Bar","酒吧","Bar","目标","obj","gold"),
 ("Cigar","雪茄室","Cigar","","room","room"),
 ("Piano","钢琴室","Piano","","room","room"),
 ("Bathroom","洗手间","Bathroom","","room","room"),
 ("Storage","储藏室","Storage","","room","room"),
 ("BarFreezer","吧台冷冻库","Bar Freezer","","room","room"),
 ("Cocktail Entrance","鸡尾酒吧入口","Cocktail Ent.","","room","corr"),
 ("White Corridor","白色走廊","White Corridor","","room","corr"),
 ("Red Stairs","红楼梯","Red Stairs","","room","corr"),
 ("White Stairs","白楼梯","White Stairs","","room","corr"),
 ("Wood Stairs","木楼梯","Wood Stairs","","room","corr"),
 ("Cigar Balcony","雪茄室阳台","Cigar Balcony","室外","ext","ext"),
 ("CocktailBalcony","鸡尾酒吧阳台","Cocktail Balcony","室外","ext","ext"),
],
"4": [
 ("Roof","屋顶","Roof","室外","ext","ext"),
 ("Bakery Roof","面包房屋顶","Bakery Roof","室外","ext","ext"),
 ("Terrace","露台","Terrace","室外","ext","ext"),
],
}
BOMBN = {"1": ["4A","4B"], "2": ["2A","2B","3A","3B"], "3": ["1A","1B"], "4": []}

harvest = json.load(io.open(SP + "kafe_harvest.json", encoding="utf-8"))
def hpos(f, name):
    pts = [(x,y) for n,x,y in harvest[FLOORS_META[f][0]] if n == name]
    if not pts: return None
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

# 坐标系 our=pic+偏移
OX, OY = (MAPW-1024)/2.0, (MAPH-1024)/2.0
def our2pic(x,y): return (x-OX, y-OY)
def pic2our(u,v): return (u+OX, v+OY)

def grow(lab, free, iters):
    for _ in range(iters):
        nb = np.zeros_like(lab)
        for ax, sh in ((0,1),(0,-1),(1,1),(1,-1)):
            s = np.roll(lab, sh, axis=ax)
            if ax == 0: s[0 if sh==1 else -1,:] = 0
            else: s[:,0 if sh==1 else -1] = 0
            nb = np.where((nb==0)&(s>0), s, nb)
        g = (lab==0)&free&(nb>0)
        if not g.any(): break
        lab = np.where(g, nb, lab)
    return lab

# ---------- 标注提取(bw/fh/ch/cam/losf/dt) ----------
tree = ET.parse(SVGF)
parent = {c:p for p in tree.iter() for c in p}
SVG = '{http://www.w3.org/2000/svg}'
def parse_transform(t):
    M=[1,0,0,1,0,0]
    def mul(m1,m2):
        a1,b1,c1,d1,e1,f1=m1;a2,b2,c2,d2,e2,f2=m2
        return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]
    for m in re.finditer(r'(matrix|translate|scale|rotate)\(([^)]*)\)', t or ''):
        k,a=m.group(1),[float(x) for x in re.split(r'[\s,]+',m.group(2).strip()) if x]
        if k=='matrix':M=mul(M,a)
        elif k=='translate':M=mul(M,[1,0,0,1,a[0],a[1] if len(a)>1 else 0])
        elif k=='scale':M=mul(M,[a[0],0,0,a[1] if len(a)>1 else a[0],0,0])
        elif k=='rotate':
            r=math.radians(a[0]);R=[math.cos(r),math.sin(r),-math.sin(r),math.cos(r),0,0]
            if len(a)==3:M=mul(M,[1,0,0,1,a[1],a[2]]);M=mul(M,R);M=mul(M,[1,0,0,1,-a[1],-a[2]])
            else:M=mul(M,R)
    return M
def resolved(el):
    ch=[];e=el
    while e is not None:ch.append(e);e=parent.get(e)
    M=[1,0,0,1,0,0]
    def mul(m1,m2):
        a1,b1,c1,d1,e1,f1=m1;a2,b2,c2,d2,e2,f2=m2
        return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]
    for e in reversed(ch):M=mul(M,parse_transform(e.get('transform')))
    return M
def apM(M,x,y):a,b,c,d,e,f=M;return(a*x+c*y+e,b*x+d*y+f)
def topx(X,Y):return((X-PIC['x0'])/PIC['w']*1024,(Y-PIC['y0'])/PIC['w']*1024)
TOK=re.compile(r'([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+(?:e-?\d+)?)')
def sample_path(d,step=2.0):
    pts=[];cur=(0,0);start=(0,0);cmd=None
    seq=[('cmd',c) if c else ('num',float(n)) for c,n in TOK.findall(d)];i=0
    def emit(p0,p1):
        dist=math.hypot(p1[0]-p0[0],p1[1]-p0[1]);n=max(1,int(dist/step))
        for k in range(n+1):
            t=k/n;pts.append((p0[0]+(p1[0]-p0[0])*t,p0[1]+(p1[1]-p0[1])*t))
    while i<len(seq):
        kind,v=seq[i]
        if kind=='cmd':cmd=v;i+=1;continue
        def nums(k):
            nonlocal i
            out=[]
            while len(out)<k and i<len(seq) and seq[i][0]=='num':out.append(seq[i][1]);i+=1
            return out if len(out)==k else None
        if cmd in 'Mm':
            a=nums(2)
            if not a:break
            cur=(a[0],a[1]) if cmd=='M' else (cur[0]+a[0],cur[1]+a[1]);start=cur;cmd='L' if cmd=='M' else 'l'
        elif cmd in 'Ll':
            a=nums(2)
            if not a:break
            p=(a[0],a[1]) if cmd=='L' else (cur[0]+a[0],cur[1]+a[1]);emit(cur,p);cur=p
        elif cmd in 'Hh':
            a=nums(1)
            if not a:break
            p=(a[0],cur[1]) if cmd=='H' else (cur[0]+a[0],cur[1]);emit(cur,p);cur=p
        elif cmd in 'Vv':
            a=nums(1)
            if not a:break
            p=(cur[0],a[0]) if cmd=='V' else (cur[0],cur[1]+a[0]);emit(cur,p);cur=p
        elif cmd in 'CcSsQqTt':
            k={'C':6,'c':6,'S':4,'s':4,'Q':4,'q':4,'T':2,'t':2}[cmd]
            a=nums(k)
            if not a:break
            p=(a[-2],a[-1]) if cmd.isupper() else (cur[0]+a[-2],cur[1]+a[-1]);emit(cur,p);cur=p
        elif cmd in 'Aa':
            a=nums(7)
            if not a:break
            p=(a[-2],a[-1]) if cmd=='A' else (cur[0]+a[-2],cur[1]+a[-1]);emit(cur,p);cur=p
        elif cmd in 'Zz':emit(cur,start);cur=start
        else:i+=1
    return pts
def leaf_quads(g, only_pattern=False):
    out=[]
    for tag in ('rect','path','circle','image','ellipse'):
        for e in g.iter(SVG+tag):
            st=(e.get('style') or '')+';fill:'+(e.get('fill') or '')+';'
            if only_pattern and 'url(#pattern' not in st: continue
            M=resolved(e)
            if tag in ('rect','image'):
                x=float(e.get('x') or 0);y=float(e.get('y') or 0);w=float(e.get('width') or 0);h=float(e.get('height') or 0)
                pts=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
            elif tag in ('circle','ellipse'):
                cx=float(e.get('cx') or 0);cy=float(e.get('cy') or 0);r=float(e.get('r') or e.get('rx') or 3)
                pts=[(cx-r,cy-r),(cx+r,cy-r),(cx+r,cy+r),(cx-r,cy+r)]
            else:
                sp=sample_path(e.get('d') or '')
                if len(sp)<2: continue
                xs=[p[0] for p in sp];ys=[p[1] for p in sp]
                pts=[(min(xs),min(ys)),(max(xs),min(ys)),(max(xs),max(ys)),(min(xs),max(ys))]
            quad=[topx(*apM(M,px,py)) for px,py in pts]
            out.append([[round(a,1),round(b,1)] for a,b in quad])
    return out
LAYERS=['bw','fh','ch','cam','losf','dt']
marks_pic={f:{} for f in FLOORS_META}     # 图片像素坐标
LNUM2F={FLOORS_META[f][2]:f for f in FLOORS_META}
for g in tree.iter(SVG+'g'):
    gid=g.get('id') or ''
    m=re.match(r'^(\d+)-(%s)$'%'|'.join(LAYERS), gid)
    if not m or m.group(1) not in LNUM2F: continue
    f,layer=LNUM2F[m.group(1)],m.group(2)
    quads=leaf_quads(g, only_pattern=(layer=='bw'))
    ok=[]
    for q in quads:
        xs=[p[0] for p in q];ys=[p[1] for p in q]
        if max(xs)<-50 or min(xs)>1074 or max(ys)<-50 or min(ys)>1074: continue
        area=abs((xs[1]-xs[0])*(ys[3]-ys[0])-(xs[3]-xs[0])*(ys[1]-ys[0]))
        if area<0.5: continue
        ok.append(q)
    marks_pic[f].setdefault(layer,[]).extend(ok)

# ---------- 逐层房间填充 ----------
newfloors={}
refkb={}
for f in ORDER:
    hk, picfn, lnum, cn_fl, note = FLOORS_META[f]
    im=Image.open(IMGDIR+picfn).convert("RGBA")
    a=np.asarray(im).astype(np.int16)
    rgb,alpha=a[...,:3],a[...,3]
    content=(alpha>10)&(rgb.max(2)>18)
    wall=(rgb.min(2)>225)&((rgb.max(2)-rgb.min(2))<25)&content
    H_,W_=wall.shape
    wallD=np.asarray(Image.fromarray((wall*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2*K+1)))>0
    wallD2=np.asarray(Image.fromarray((wall*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2*K2+1)))>0
    labO=np.zeros((H_,W_),np.int16)
    for sl in (np.s_[0,:],np.s_[-1,:],np.s_[:,0],np.s_[:,-1]): labO[sl]=np.where(~wallD2[sl],1,0)
    labO=grow(labO,~wallD2,1200)
    outside=np.asarray(Image.fromarray(((labO>0)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2*(K2-K)+1)))>0
    rooms=ROOMS[f]; n_int=len(rooms)
    freeI=content&~wallD&~outside; freeE=content&~wallD
    lab=np.zeros((H_,W_),np.int16)
    seeds=[]
    for i,(rn,cn,en,kind,kk,ct) in enumerate(rooms,1):
        for x,y in [(x,y) for n,x,y in harvest[hk] if n==rn]: seeds.append((i,x,y))
    for i,x,y in seeds:
        ct=rooms[i-1][5]; openroom=(ct=="ext")
        target=freeE if openroom else freeI
        px,py=int(round(x)),int(round(y))
        if not (0<=px<W_ and 0<=py<H_): continue
        if not target[py,px]:
            ok=False; fb=(content&~wall) if openroom else (content&~wall&~outside)
            for tgt in (target,fb):
                for r in range(2,90,2):
                    ys,xs=np.mgrid[max(0,py-r):min(H_,py+r),max(0,px-r):min(W_,px+r)]
                    fm=tgt[ys,xs]
                    if fm.any():
                        j=np.flatnonzero(fm.ravel())[0];py,px=ys.ravel()[j],xs.ravel()[j];ok=True;break
                if ok:break
            if not ok: print("  !! seed lost:",f,rooms[i-1][1]); continue
        lab[py,px]=i
    isext=np.array([rooms[i-1][5]=="ext" for i in range(1,n_int+1)])
    lab_int=np.where(np.isin(lab,np.flatnonzero(~isext)+1),lab,0)
    lab_int=grow(lab_int,freeI,MAXIT); lab_int=grow(lab_int,content&~wall&~outside,K+2)
    lab_ext=np.where(np.isin(lab,np.flatnonzero(isext)+1),lab,0)
    # 室外(露台/阳台/屋顶)限制扩散步数，避免灌满整片户外街区
    lab_ext=grow(lab_ext,content&~wallD&(lab_int==0),34); lab_ext=grow(lab_ext,content&~wall&(lab_int==0),K+2)
    lab=np.where(lab_int>0,lab_int,lab_ext)
    sizes=np.bincount(lab.ravel(),minlength=n_int+1)
    for i in range(1,n_int+1):
        if 0<sizes[i]<500 and rooms[i-1][5]!="ext":
            labi=np.where(lab==i,np.int16(i),np.int16(0))
            fr=content&~wall&~outside&((lab==0)|(lab==i))
            labi=grow(labi,fr,70); lab=np.where((labi>0)&(lab==0),np.int16(i),lab)
            print("  rescue:",f,rooms[i-1][1],"->",int((lab==i).sum()))
    sizes=np.bincount(lab.ravel(),minlength=n_int+1)
    for i in range(1,n_int+1): print("  %s %-8s %6d px"%(f,rooms[i-1][1],sizes[i]))
    # 逐格采样
    rows=[]
    for gy in range(GH):
        row=[]
        for gx in range(GW):
            votes={}
            for ox,oy in ((5,5),(2,2),(8,2),(2,8),(8,8)):
                u,v=our2pic(gx*CELL+ox,gy*CELL+oy); ui,vi=int(round(u)),int(round(v))
                if 0<=ui<W_ and 0<=vi<H_:
                    li=int(lab[vi,ui])
                    if li>0: votes[li]=votes.get(li,0)+1
            best=max(votes.items(),key=lambda kv:kv[1]) if votes else (0,0)
            row.append("." if best[1]<3 else CH[best[0]-1])
        rows.append("".join(row))
    ci,ei=0,0; palette=[]
    for i,(rn,cn,en,kind,kk,ct) in enumerate(rooms):
        if ct=="gold":c=GOLD_C
        elif ct=="corr":c=CORR_C
        elif ct=="ext":c=EXTC[ei%len(EXTC)];ei+=1
        else:c=CYCLE[ci%len(CYCLE)];ci+=1
        palette.append({"ch":CH[i],"cn":cn,"c":c,"t":ct if ct in ("gold","corr","ext") else "room"})
    labels=[]
    for i,(rn,cn,en,kind,kk,ct) in enumerate(rooms):
        h=hpos(f,rn)
        if not h: continue
        x,y=pic2our(*h); labels.append({"cn":cn,"en":en,"kind":kind,"x":int(round(x)),"y":int(round(y)),"k":kk})
    ys,xs=np.nonzero(np.array([[c!="." for c in r] for r in rows]))
    if len(xs): x0,x1=xs.min()*CELL,(xs.max()+1)*CELL; y0,y1=ys.min()*CELL,(ys.max()+1)*CELL
    else: x0,y0,x1,y1=400,250,1100,850
    for l in labels:
        x0=min(x0,l["x"]-40);x1=max(x1,l["x"]+40);y0=min(y0,l["y"]-30);y1=max(y1,l["y"]+30)
    x0=max(0,int(x0)-10);y0=max(0,int(y0)-10);x1=min(MAPW,int(x1)+10);y1=min(MAPH,int(y1)+10)
    bombs=[]
    for bn in BOMBN[f]:
        h=hpos(f,bn)
        if h: x,y=pic2our(*h); bombs.append({"t":bn,"x":int(round(x)),"y":int(round(y))})
    # marks pic -> our
    mk={}
    for layer,quads in marks_pic[f].items():
        lst=[[[round(px+OX,1),round(py+OY,1)] for px,py in q] for q in quads]
        if lst: mk[layer]=lst
    newfloors[f]={"note":note,"bbox":{"x":x0,"y":y0,"w":x1-x0,"h":y1-y0},
                  "rooms":palette,"grid":rows,"labels":labels,"bombs":bombs,"marks":mk}
    # ref 2x 底图
    rgbim=Image.open(IMGDIR+picfn).convert("RGB")
    ref=rgbim.transform((MAPW*2,MAPH*2),Image.AFFINE,(0.5,0,-OX,0,0.5,-OY),resample=Image.BICUBIC)
    ref.save(D+"ref_kafe_%s.webp"%f,"WEBP",quality=62,method=6)
    refkb[f]=os.path.getsize(D+"ref_kafe_%s.webp"%f)//1024

data={"cell":CELL,"gw":GW,"gh":GH,"map":"kafe","mapcn":"咖啡馆",
      "floorOrder":ORDER,
      "floorNames":{f:FLOORS_META[f][3] for f in FLOORS_META},
      "floors":newfloors}
io.open(D+"data_kafe.json","w",encoding="utf-8").write(json.dumps(data,ensure_ascii=False))
print("marks:",{f:{k:len(v) for k,v in newfloors[f]["marks"].items()} for f in ORDER})
print("ref KB:",refkb)
print("-> data_kafe.json")
