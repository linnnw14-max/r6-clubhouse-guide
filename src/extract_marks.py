# -*- coding: utf-8 -*-
# 从 r6calls club.svg 提取各楼层标注层(可破坏墙/地板天窗/天花板天窗/摄像头/视线地板/无人机洞)
# 组名规律: "<floor>-<layer>"; 这些图形与楼层图片同在根坐标系, 直接换算成图片像素四角(quad)
import xml.etree.ElementTree as ET
import re, json, math, os

SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"
SVGF = SP + "club_r6calls.svg"
PIC = {"x0": 758.56, "y0": 249.767, "w": 361.244}  # 图片矩形(根坐标) -> 1024px

tree = ET.parse(SVGF)
parent = {c: p for p in tree.iter() for c in p}
SVG = '{http://www.w3.org/2000/svg}'

def parse_transform(t):
    M = [1,0,0,1,0,0]
    def mul(m1,m2):
        a1,b1,c1,d1,e1,f1=m1;a2,b2,c2,d2,e2,f2=m2
        return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]
    for m in re.finditer(r'(matrix|translate|scale|rotate)\(([^)]*)\)', t or ''):
        kind,args=m.group(1),[float(x) for x in re.split(r'[\s,]+',m.group(2).strip()) if x]
        if kind=='matrix':M=mul(M,args)
        elif kind=='translate':M=mul(M,[1,0,0,1,args[0],args[1] if len(args)>1 else 0])
        elif kind=='scale':M=mul(M,[args[0],0,0,args[1] if len(args)>1 else args[0],0,0])
        elif kind=='rotate':
            a=math.radians(args[0]);R=[math.cos(a),math.sin(a),-math.sin(a),math.cos(a),0,0]
            if len(args)==3:
                M=mul(M,[1,0,0,1,args[1],args[2]]);M=mul(M,R);M=mul(M,[1,0,0,1,-args[1],-args[2]])
            else:M=mul(M,R)
    return M
def resolved(el):
    chain=[];e=el
    while e is not None:chain.append(e);e=parent.get(e)
    M=[1,0,0,1,0,0]
    def mul(m1,m2):
        a1,b1,c1,d1,e1,f1=m1;a2,b2,c2,d2,e2,f2=m2
        return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]
    for e in reversed(chain):M=mul(M,parse_transform(e.get('transform')))
    return M
def apply(M,x,y):
    a,b,c,d,e,f=M;return (a*x+c*y+e,b*x+d*y+f)
def to_px(X,Y):
    return ((X-PIC['x0'])/PIC['w']*1024,(Y-PIC['y0'])/PIC['w']*1024)

TOK=re.compile(r'([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+(?:e-?\d+)?)')
def sample_path(d,step=2.0):
    pts=[];cur=(0,0);start=(0,0);cmd=None
    seq=[('cmd',c) if c else ('num',float(n)) for c,n in TOK.findall(d)]
    i=0
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
            cur=(a[0],a[1]) if cmd=='M' else (cur[0]+a[0],cur[1]+a[1]);start=cur
            cmd='L' if cmd=='M' else 'l'
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
        elif cmd in 'Zz':
            emit(cur,start);cur=start
        else:i+=1
    return pts

def leaf_quads(g, only_pattern=False):
    out=[]
    for tag in ('rect','path','circle','image','ellipse'):
        for e in g.iter(SVG+tag):
            st=(e.get('style') or '')+';fill:'+(e.get('fill') or '')+';'
            if only_pattern and 'url(#pattern' not in st: continue
            M=resolved(e)
            if tag=='rect' or tag=='image':
                x=float(e.get('x') or 0);y=float(e.get('y') or 0)
                w=float(e.get('width') or 0);h=float(e.get('height') or 0)
                pts=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
            elif tag=='circle' or tag=='ellipse':
                cx=float(e.get('cx') or 0);cy=float(e.get('cy') or 0)
                r=float(e.get('r') or e.get('rx') or 3)
                pts=[(cx-r,cy-r),(cx+r,cy-r),(cx+r,cy+r),(cx-r,cy+r)]
            else:
                sp=sample_path(e.get('d') or '')
                if len(sp)<2: continue
                xs=[p[0] for p in sp];ys=[p[1] for p in sp]
                pts=[(min(xs),min(ys)),(max(xs),min(ys)),(max(xs),max(ys)),(min(xs),max(ys))]
            quad=[to_px(*apply(M,px,py)) for px,py in pts]
            out.append([[round(a,1),round(b,1)] for a,b in quad])
    return out

FLOORMAP={'0':'B','1':'1','2':'2','3':'R'}
LAYERS=['bw','fh','ch','cam','losf','dt']
marks={v:{} for v in FLOORMAP.values()}
for g in tree.iter(SVG+'g'):
    gid=g.get('id') or ''
    m=re.match(r'^([0-3])-(%s)$'%'|'.join(LAYERS),gid)
    if not m:continue
    f,layer=FLOORMAP[m.group(1)],m.group(2)
    quads=leaf_quads(g, only_pattern=(layer=='bw'))
    # 去重/过滤: 面积>0.5px², 且在图片范围内
    ok=[]
    for q in quads:
        xs=[p[0] for p in q];ys=[p[1] for p in q]
        if max(xs)<-50 or min(xs)>1074 or max(ys)<-50 or min(ys)>1074: continue
        area=abs((xs[1]-xs[0])*(ys[3]-ys[0])-(xs[3]-xs[0])*(ys[1]-ys[0]))
        if area<0.5: continue
        ok.append(q)
    marks[f].setdefault(layer,[]).extend(ok)
for f in marks:
    print(f, {k:len(v) for k,v in marks[f].items()})
json.dump(marks, open(SP+'r6c_marks_pic.json','w'))
print('->', SP+'r6c_marks_pic.json')
