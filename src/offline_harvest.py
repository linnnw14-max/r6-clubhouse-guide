# -*- coding: utf-8 -*-
# 离线收割: 解析 <mid>.svg 的房名标签框(shape-inside path)中心 -> topx 像素空间 -> <mid>_harvest.json
# 等价于浏览器收割, 免浏览器。 用法: python3 offline_harvest.py <mid> [--validate]
import xml.etree.ElementTree as ET
import re, json, math, sys, os
D=os.path.dirname(os.path.abspath(__file__))+"/"
mid=sys.argv[1]; VALIDATE='--validate' in sys.argv
SVG='{http://www.w3.org/2000/svg}'
tree=ET.parse(D+mid+".svg"); parent={c:p for p in tree.iter() for c in p}
byid={el.get('id'):el for el in tree.iter() if el.get('id')}
manifest=json.load(open(D+mid+"_manifest.json")); PIC=manifest["picrect"]
YFIX=-24.0   # 标签框中心->浏览器锚点 的经验竖直修正(约半行高)
XLINK='{http://www.w3.org/1999/xlink}'

def mul(m1,m2):
    a1,b1,c1,d1,e1,f1=m1;a2,b2,c2,d2,e2,f2=m2
    return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]
def ptf(t):
    M=[1,0,0,1,0,0]
    for m in re.finditer(r'(matrix|translate|scale|rotate)\(([^)]*)\)',t or ''):
        k,a=m.group(1),[float(x) for x in re.split(r'[\s,]+',m.group(2).strip()) if x]
        if k=='matrix':M=mul(M,a)
        elif k=='translate':M=mul(M,[1,0,0,1,a[0],a[1] if len(a)>1 else 0])
        elif k=='scale':M=mul(M,[a[0],0,0,a[1] if len(a)>1 else a[0],0,0])
        elif k=='rotate':
            r=math.radians(a[0]);R=[math.cos(r),math.sin(r),-math.sin(r),math.cos(r),0,0]
            if len(a)==3:M=mul(M,[1,0,0,1,a[1],a[2]]);M=mul(M,R);M=mul(M,[1,0,0,1,-a[1],-a[2]])
            else:M=mul(M,R)
    return M
def res(el):
    ch=[];e=el
    while e is not None:ch.append(e);e=parent.get(e)
    M=[1,0,0,1,0,0]
    for e in reversed(ch):M=mul(M,ptf(e.get('transform')))
    return M
def ap(M,x,y):a,b,c,d,e,f=M;return(a*x+c*y+e,b*x+d*y+f)
def topg(el):
    e=el;l=None
    while e is not None:
        if e.tag.endswith('}g') and e.get('id'):l=e.get('id')
        e=parent.get(e)
    return l
def pathbbox(d):
    toks=re.findall(r'[MmHhVvLlZz]|-?\d+\.?\d*',d)
    cx=cy=0;xs=[];ys=[];i=0
    while i<len(toks):
        t=toks[i]
        if t in 'Mm':cx=float(toks[i+1]);cy=float(toks[i+2]);xs.append(cx);ys.append(cy);i+=3
        elif t in 'Ll':
            nx=float(toks[i+1]);ny=float(toks[i+2])
            if t=='l':nx+=cx;ny+=cy
            cx,cy=nx,ny;xs.append(cx);ys.append(cy);i+=3
        elif t in 'Hh':cx=float(toks[i+1])+(cx if t=='h' else 0);xs.append(cx);ys.append(cy);i+=2
        elif t in 'Vv':cy=float(toks[i+1])+(cy if t=='v' else 0);ys.append(cy);xs.append(cx);i+=2
        else:i+=1
    return (min(xs)+max(xs))/2,(min(ys)+max(ys))/2
# 每层各自的 pic 矩形(有些图各层俯视图位置不同, e.g. labs) -> floornum -> (x0,y0,w)
FPIC={}
for im in tree.iter(SVG+'image'):
    gid=im.get('id') or ''
    mm=re.match(r'^(\d+)-pic$',gid)
    if not mm:continue
    M=res(im)
    x=float(im.get('x'));y=float(im.get('y'));w=float(im.get('width'));h=float(im.get('height'))
    p0=ap(M,x,y);p1=ap(M,x+w,y+h)
    FPIC[mm.group(1)]={"x0":p0[0],"y0":p0[1],"w":p1[0]-p0[0]}
def topx(fn,X,Y):
    p=FPIC.get(fn,PIC)
    return ((X-p["x0"])/p["w"]*1024,(Y-p["y0"])/p["w"]*1024)

out={}
for t in tree.iter(SVG+'text'):
    nm=' '.join(''.join(t.itertext()).split());tg=topg(t)
    st=t.get('style') or ''
    m=re.search(r'shape-inside:url\(#([^)]+)\)',st)
    if not(nm and tg and tg.startswith('Floor')):continue
    if m and byid.get(m.group(1)) is not None and byid[m.group(1)].tag.endswith('}path'):
        cx,cy=pathbbox(byid[m.group(1)].get('d'))
        M=res(t);sx,sy=ap(M,cx,cy)
    else:
        # 回退: 用 text/tspan x,y
        xs=t.get('x');ys=t.get('y')
        if xs is None:
            sp=t.find(SVG+'tspan')
            if sp is None:continue
            xs=sp.get('x');ys=sp.get('y')
        M=res(t);sx,sy=ap(M,float(re.split(r'[\s,]+',xs)[0]),float(re.split(r'[\s,]+',ys)[0]))
    fn=tg.split()[1]
    px,py=topx(fn,sx,sy); py+=YFIX
    out.setdefault("F"+fn,[]).append([nm,int(round(px)),int(round(py))])

if VALIDATE:
    real=json.load(open(D+mid+"_harvest.json"))
    tot=[];
    for fk in sorted(real):
        rv={n:(x,y) for n,x,y in real[fk]}
        ov={n:(x,y) for n,x,y in out.get(fk,[])}
        errs=[]
        for n in set(rv)&set(ov):
            dx=ov[n][0]-rv[n][0];dy=ov[n][1]-rv[n][1];errs.append((dx*dx+dy*dy)**.5);tot.append((dx*dx+dy*dy)**.5)
        if errs:
            errs.sort()
            print("%s n=%d  median=%.1f  p90=%.1f  max=%.1f"%(fk,len(errs),errs[len(errs)//2],errs[int(len(errs)*.9)],max(errs)))
    if tot:
        tot.sort();print("ALL n=%d median=%.1f p90=%.1f max=%.1f"%(len(tot),tot[len(tot)//2],tot[int(len(tot)*.9)],max(tot)))
else:
    for fk in out:out[fk].sort()
    json.dump(out,open(D+mid+"_harvest.json","w"),ensure_ascii=False)
    print(mid,"-> harvest floors:",{k:len(v) for k,v in sorted(out.items())})
