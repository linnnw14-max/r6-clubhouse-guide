# -*- coding: utf-8 -*-
# 通用地图构建: python3 build_map.py <mapid>
# 读 mapcfg.py[mapid] + <mapid>_manifest.json + <mapid>_harvest.json + <mapid>_imgs/
# 产出 r6gen/data_<mapid>.json + r6gen/ref_<mapid>_<floor>.webp (含房间填充+标注提取+墙板拆分)
import io, json, os, math, re, sys
import numpy as np
from PIL import Image, ImageFilter
import xml.etree.ElementTree as ET

D = os.path.dirname(os.path.abspath(__file__)) + "/"
R6GEN = os.path.dirname(D.rstrip("/")) + "/r6gen/"
sys.path.insert(0, D)
from mapcfg import MAPCFG

mid = sys.argv[1]
cfg = MAPCFG[mid]
MAPW, MAPH, CELL, GW, GH = 1374, 1048, 10, 138, 105
K, K2, MAXIT = 6, 12, 340
UNIT, GAP = 27.5, 1.4
manifest = json.load(io.open(D + mid + "_manifest.json", encoding="utf-8"))
PIC = manifest["picrect"]
IMGDIR = D + mid + "_imgs/"
SVGF = D + mid + ".svg"
harvest = json.load(io.open(D + mid + "_harvest.json", encoding="utf-8"))

CH = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
CYCLE = ["#4C9BE8","#3FBFA0","#B07FD8","#6FBF5F","#45C0E8","#D8B04A","#E07A9E","#8E9AF0","#A8C25A","#E8935B","#5FD3B8","#C98BD6","#6FA8D8","#B0C862"]
EXTC = ["#4A6172","#3F6D63","#566B85","#5E7A6E"]
GOLD_C, CORR_C = "#F0A93F", "#6E8296"

ORDER = cfg["order"]              # r6calls 楼层号, 上到下
def hk(f): return "F" + f
def hpos(f, name):
    pts = [(x,y) for n,x,y in harvest.get(hk(f), []) if n == name]
    if not pts: return None
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

OX, OY = (MAPW-1024)/2.0, (MAPH-1024)/2.0
def our2pic(x,y): return (x-OX, y-OY)
def pic2our(u,v): return (u+OX, v+OY)
def topx(X,Y): return ((X-PIC["x0"])/PIC["w"]*1024, (Y-PIC["y0"])/PIC["w"]*1024)

def grow(lab, free, iters):
    for _ in range(iters):
        nb = np.zeros_like(lab)
        for ax, sh in ((0,1),(0,-1),(1,1),(1,-1)):
            s = np.roll(lab, sh, axis=ax)
            if ax==0: s[0 if sh==1 else -1,:]=0
            else: s[:,0 if sh==1 else -1]=0
            nb = np.where((nb==0)&(s>0), s, nb)
        g = (lab==0)&free&(nb>0)
        if not g.any(): break
        lab = np.where(g, nb, lab)
    return lab

# ---- 标注提取 ----
tree = ET.parse(SVGF); parent = {c:p for p in tree.iter() for c in p}
SVG='{http://www.w3.org/2000/svg}'
def ptf(t):
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
def rres(el):
    ch=[];e=el
    while e is not None:ch.append(e);e=parent.get(e)
    M=[1,0,0,1,0,0]
    def mul(m1,m2):
        a1,b1,c1,d1,e1,f1=m1;a2,b2,c2,d2,e2,f2=m2
        return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]
    for e in reversed(ch):M=mul(M,ptf(e.get('transform')))
    return M
def apM(M,x,y):a,b,c,d,e,f=M;return(a*x+c*y+e,b*x+d*y+f)
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
            M=rres(e)
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
marks_pic={f:{} for f in ORDER}
for g in tree.iter(SVG+'g'):
    gid=g.get('id') or ''
    m=re.match(r'^(\d+)-(%s)$'%'|'.join(LAYERS), gid)
    if not m or m.group(1) not in ORDER: continue
    f,layer=m.group(1),m.group(2)
    quads=leaf_quads(g, only_pattern=(layer=='bw'))
    ok=[]
    for q in quads:
        xs=[p[0] for p in q];ys=[p[1] for p in q]
        if max(xs)<-50 or min(xs)>1074 or max(ys)<-50 or min(ys)>1074: continue
        area=abs((xs[1]-xs[0])*(ys[3]-ys[0])-(xs[3]-xs[0])*(ys[1]-ys[0]))
        if area<0.5: continue
        ok.append(q)
    marks_pic[f].setdefault(layer,[]).extend(ok)

def split_bw(quads):
    ov = cfg.get("bwOverride", {})
    def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
    out=[]
    for i,q in enumerate(quads):
        e01,e12=dist(q[0],q[1]),dist(q[1],q[2])
        A0,A1,B0,B1=(q[0],q[1],q[3],q[2]) if e01>=e12 else (q[1],q[2],q[0],q[3])
        L=dist(A0,A1); n=ov.get(str(i)) or max(1,round(max(e01,e12)/UNIT))
        for j in range(n):
            t0,t1=j/n,(j+1)/n
            g0=GAP/L if j>0 else 0.3/L; g1=GAP/L if j<n-1 else 0.3/L
            s0,s1=t0+g0,t1-g1
            def lp(P,Q,t): return [round(P[0]+(Q[0]-P[0])*t,1),round(P[1]+(Q[1]-P[1])*t,1)]
            out.append([lp(A0,A1,s0),lp(A0,A1,s1),lp(B0,B1,s1),lp(B0,B1,s0)])
    return out

# ---- 逐层房间填充 ----
newfloors={}; refkb={}
for f in ORDER:
    rooms=cfg["rooms"].get(f, [])
    picfn=IMGDIR+f+"-pic.png"
    im=Image.open(picfn).convert("RGBA"); a=np.asarray(im).astype(np.int16)
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
    n_int=len(rooms)
    freeI=content&~wallD&~outside; freeE=content&~wallD
    lab=np.zeros((H_,W_),np.int16); seeds=[]
    for i,(rn,cn,en,kind,kk,ct) in enumerate(rooms,1):
        for x,y in [(x,y) for n,x,y in harvest.get(hk(f),[]) if n==rn]: seeds.append((i,x,y))
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
    if n_int:
        isext=np.array([rooms[i-1][5]=="ext" for i in range(1,n_int+1)])
        lab_int=np.where(np.isin(lab,np.flatnonzero(~isext)+1),lab,0)
        lab_int=grow(lab_int,freeI,MAXIT); lab_int=grow(lab_int,content&~wall&~outside,K+2)
        lab_ext=np.where(np.isin(lab,np.flatnonzero(isext)+1),lab,0)
        lab_ext=grow(lab_ext,content&~wallD&(lab_int==0),34); lab_ext=grow(lab_ext,content&~wall&(lab_int==0),K+2)
        lab=np.where(lab_int>0,lab_int,lab_ext)
        sizes=np.bincount(lab.ravel(),minlength=n_int+1)
        for i in range(1,n_int+1):
            if 0<sizes[i]<500 and rooms[i-1][5]!="ext":
                labi=np.where(lab==i,np.int16(i),np.int16(0))
                fr=content&~wall&~outside&((lab==0)|(lab==i))
                labi=grow(labi,fr,70); lab=np.where((labi>0)&(lab==0),np.int16(i),lab)
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
    for bn in cfg["bombs"].get(f, []):
        h=hpos(f,bn)
        if h: x,y=pic2our(*h); bombs.append({"t":bn,"x":int(round(x)),"y":int(round(y))})
    mk={}
    for layer,quads in marks_pic[f].items():
        qs=[[[round(px+OX,1),round(py+OY,1)] for px,py in q] for q in quads]
        if layer=="bw": qs=split_bw(qs)
        if qs: mk[layer]=qs
    newfloors[f]={"note":cfg["notes"].get(f,""),"bbox":{"x":x0,"y":y0,"w":x1-x0,"h":y1-y0},
                  "rooms":palette,"grid":rows,"labels":labels,"bombs":bombs,"marks":mk}
    rgbim=Image.open(picfn).convert("RGB")
    ref=rgbim.transform((MAPW*2,MAPH*2),Image.AFFINE,(0.5,0,-OX,0,0.5,-OY),resample=Image.BICUBIC)
    ref.save(R6GEN+"ref_%s_%s.webp"%(mid,f),"WEBP",quality=60,method=6)
    refkb[f]=os.path.getsize(R6GEN+"ref_%s_%s.webp"%(mid,f))//1024

data={"cell":CELL,"gw":GW,"gh":GH,"map":mid,"mapcn":cfg["mapcn"],"bwSplit":True,
      "defaultFloor":cfg["default"],"floorOrder":ORDER,
      "floorNames":cfg["names"],"floorEn":cfg["en"],"sites":cfg.get("sites",[]),
      "floors":newfloors}
io.open(R6GEN+"data_%s.json"%mid,"w",encoding="utf-8").write(json.dumps(data,ensure_ascii=False))
print(mid,"floors:",{f:{"rooms":len(cfg['rooms'].get(f,[])),"bw":len(newfloors[f]['marks'].get('bw',[])),"labels":len(newfloors[f]['labels']),"bombs":len(newfloors[f]['bombs'])} for f in ORDER})
print("-> data_%s.json  ref KB:"%mid, refkb)
