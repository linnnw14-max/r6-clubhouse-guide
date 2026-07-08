# -*- coding: utf-8 -*-
# 通用解剖: python3 dissect_map.py <mapid>
# 读 <mapid>.svg -> 提取各层俯视图(N-pic)到 <mapid>_imgs/ + 算图片矩形 + 列楼层号/图层组 -> <mapid>_manifest.json
import xml.etree.ElementTree as ET
import re, json, base64, os, math, sys
from PIL import Image

D = os.path.dirname(os.path.abspath(__file__)) + "/"
mid = sys.argv[1]
SVGF = D + mid + ".svg"
IMGDIR = D + mid + "_imgs/"
os.makedirs(IMGDIR, exist_ok=True)
SVG = '{http://www.w3.org/2000/svg}'; XLINK = '{http://www.w3.org/1999/xlink}'

tree = ET.parse(SVGF)
parent = {c: p for p in tree.iter() for c in p}

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
def res(el):
    ch=[];e=el
    while e is not None:ch.append(e);e=parent.get(e)
    M=[1,0,0,1,0,0]
    def mul(m1,m2):
        a1,b1,c1,d1,e1,f1=m1;a2,b2,c2,d2,e2,f2=m2
        return [a1*a2+c1*b2,b1*a2+d1*b2,a1*c2+c1*d2,b1*c2+d1*d2,a1*e2+c1*f2+e1,b1*e2+d1*f2+f1]
    for e in reversed(ch):M=mul(M,ptf(e.get('transform')))
    return M
def ap(M,x,y):a,b,c,d,e,f=M;return(a*x+c*y+e,b*x+d*y+f)
def top(el):
    e=el;l=None
    while e is not None:
        if e.tag.endswith('}g') and e.get('id'):l=e.get('id')
        e=parent.get(e)
    return l

# 楼层图
rects={}
for im in tree.iter(SVG+'image'):
    gid=im.get('id') or ''
    if re.match(r'^\d+-pic$', gid):
        href=im.get(XLINK+'href') or im.get('href') or ''
        m=re.match(r'data:image/(png|jpeg);base64,(.*)', href, re.S)
        fn=IMGDIR+gid+'.png'
        if m: open(fn,'wb').write(base64.b64decode(m.group(2)))
        M=res(im)
        x=float(im.get('x'));y=float(im.get('y'));w=float(im.get('width'));h=float(im.get('height'))
        p0=ap(M,x,y);p1=ap(M,x+w,y+h)
        sz=Image.open(fn).size if m else None
        rects[gid]={'x0':round(p0[0],3),'y0':round(p0[1],3),'x1':round(p1[0],3),'y1':round(p1[1],3),'top':top(im),'px':sz}

# 图层组 <floor>-<layer>
import collections
pat=re.compile(r'^(\d+)-([a-zA-Z]+)$')
layers=collections.defaultdict(list)
for g in tree.iter(SVG+'g'):
    i=g.get('id') or ''
    m=pat.match(i)
    if m:layers[m.group(2)].append(m.group(1))
# 各层文字(仅参考,坐标不准)
texts=collections.defaultdict(list)
for t in tree.iter(SVG+'text'):
    nm=' '.join(''.join(t.itertext()).split())
    tg=top(t)
    if nm and tg and re.match(r'Floor ', tg): texts[tg].append(nm)

# pic 矩形一致性(全层一般相同)
r0=list(rects.values())[0] if rects else None
manifest={
 'map':mid,
 'picrect':{'x0':r0['x0'],'y0':r0['y0'],'w':round(r0['x1']-r0['x0'],3)} if r0 else None,
 'pics':{k:{'top':v['top'],'px':v['px']} for k,v in rects.items()},
 'layers':{k:sorted(v) for k,v in sorted(layers.items())},
 'floorTexts':{k:sorted(set(v)) for k,v in texts.items()},
}
json.dump(manifest, open(D+mid+'_manifest.json','w'), ensure_ascii=False)
print(mid,'pics:',sorted(rects.keys()),'rect:',manifest['picrect'])
print('layers:',manifest['layers'])
for k in sorted(texts):
    print(k,':',sorted(set(texts[k])))
