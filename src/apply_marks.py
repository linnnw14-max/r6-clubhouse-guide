# -*- coding: utf-8 -*-
# 把 r6calls 标注(可破坏墙/天窗/摄像头/视线地板/无人机洞) 从图片像素系转换到我们坐标系写入 data.json，
# 并重新输出 2x 描图底图(正式版当原图底用)。
import io, json, os
import numpy as np
from PIL import Image

D = os.path.dirname(os.path.abspath(__file__)) + "/"
SP = os.path.dirname(D.rstrip("/")) + "/"
MAPW, MAPH = 1374, 1048
PICS = {"B": "img_05.png", "1": "img_15.png", "2": "img_29.png", "R": "img_45.png"}
HKEY = {"B": "F0", "1": "F1", "2": "F2", "R": "F3"}

harvest = json.load(io.open(SP + "r6c_harvest.json", encoding="utf-8"))
data = json.load(io.open(D + "data.json", encoding="utf-8"))
marks_pic = json.load(io.open(SP + "r6c_marks_pic.json", encoding="utf-8"))

# ---- 重建 our<->pic 仿射(锚点=现有labels,与生成时自洽) ----
ANCHORS = [("2","金库","Cash"),("2","监控室","CCTV"),("2","健身房","Gym"),("2","卧室","Bedroom"),
 ("2","洗手间","Bathroom"),("2","密室","Secret"),("2","后勤室","Office"),("2","建筑工地","Construction"),
 ("2","车库","Garage"),("2","车库楼梯","Garage Stairs"),("2","主楼梯","Main Stairs"),("2","卧室走廊","Bedroom Hallway"),
 ("1","酒吧","Bar"),("1","大贮藏室","Stock"),("1","厨房","Kitchen"),("1","休息室","Lounge"),
 ("1","脱衣舞厅","Strip Club"),("1","台球室","Pool"),("1","厕所","Toilets"),("1","主楼梯","Main Stairs"),("1","车库","Garage"),
 ("B","教堂","Church"),("B","军械库","Armory"),("B","蓝楼梯","Blue Stairs"),("B","教堂走廊","Church Hallway"),
 ("B","隧道","Tunnel"),("B","主楼梯","Main Stairs"),("B","车库","Bike"),("B","蓝色通道","Blue"),
 ("R","中央屋顶","Middle Roof"),("R","东屋顶","East Roof")]
def hpos(f, name):
    pts=[(x,y) for n,x,y in harvest[HKEY[f]] if n==name]
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts)) if pts else None
def opos(f, cn):
    for l in data["floors"][f]["labels"]:
        if l["cn"]==cn: return (l["x"], l["y"])
    return None
pairs=[(opos(f,cn),hpos(f,rn)) for f,cn,rn in ANCHORS]
pairs=[p for p in pairs if p[0] and p[1]]
X=np.array([[o[0],o[1],1] for o,h in pairs])
U=np.array([h[0] for o,h in pairs]);V=np.array([h[1] for o,h in pairs])
cu,*_=np.linalg.lstsq(X,U,rcond=None);cv,*_=np.linalg.lstsq(X,V,rcond=None)
res=np.hypot(X@cu-U,X@cv-V)
print("transform residual: mean %.2f max %.2f (px)"%(res.mean(),res.max()))
Ainv=np.linalg.inv(np.array([[cu[0],cu[1]],[cv[0],cv[1]]]))
def pic2our(u,v):
    d0,d1=u-cu[2],v-cv[2]
    return (Ainv[0,0]*d0+Ainv[0,1]*d1, Ainv[1,0]*d0+Ainv[1,1]*d1)

# ---- marks -> our 坐标 ----
for f in data["floors"]:
    src = marks_pic.get(f, {})
    out = {}
    for layer, quads in src.items():
        lst=[]
        for q in quads:
            oq=[[round(x,1),round(y,1)] for x,y in (pic2our(u,v) for u,v in q)]
            lst.append(oq)
        if lst: out[layer]=lst
    data["floors"][f]["marks"]=out
    print(f, {k:len(v) for k,v in out.items()})

# 保存变换供以后复用
data["t2pic"]={"cu":[round(v,6) for v in cu],"cv":[round(v,6) for v in cv]}
io.open(D+"data.json","w",encoding="utf-8").write(json.dumps(data,ensure_ascii=False))

# ---- 2x 底图(正式版原图底) ----
for f,fn in PICS.items():
    rgbim=Image.open(SP+"r6c_imgs/"+fn).convert("RGB")
    coeffs=(cu[0]/2,cu[1]/2,cu[2],cv[0]/2,cv[1]/2,cv[2])
    # 输出2x: 输出坐标(0..2748)先除2成 our 坐标,再映射到 pic
    ref=rgbim.transform((MAPW*2,MAPH*2),Image.AFFINE,(cu[0]*0.5,cu[1]*0.5,cu[2],cv[0]*0.5,cv[1]*0.5,cv[2]),resample=Image.BICUBIC)
    ref.save(D+"ref_%s.webp"%f,"WEBP",quality=62,method=6)
    print("ref2x",f,os.path.getsize(D+"ref_%s.webp"%f)//1024,"KB")
print("done")
