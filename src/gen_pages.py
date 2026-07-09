# -*- coding: utf-8 -*-
# 从 data*.json 生成各地图的规划器页面 + 会所校准工具。多地图数据驱动。
# 改数据: 改对应 data 文件 → 重跑本脚本。
import io, json, os, shutil, hashlib, base64

D = os.path.dirname(os.path.abspath(__file__)) + "/"
BASE = "/Users/laoba/Desktop/R6-Clubhouse-Guide/"

css = io.open(D + "style.css", encoding="utf-8").read()
view_js = io.open(D + "view.js", encoding="utf-8").read()
edit_js = io.open(D + "edit.js", encoding="utf-8").read()

def b64(p): return base64.b64encode(open(p, "rb").read()).decode()

# 地图清单（顺序=切换器里的顺序）
MAPS = [
    {"id": "club", "data": "data.json",      "refpat": "ref_%s.webp",      "out": "club.html", "mapcn": "会所", "mapen": "Clubhouse",
     "cover": "cover_club.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "监控室 + 金库经典防守点",
     "ey": "R6S · CLUBHOUSE · SETUP PLANNER", "h1": "会所 · 防守装修规划器",
     "title": "彩虹六号 · 会所防守装修规划器"},
    {"id": "kafe", "data": "data_kafe.json", "refpat": "ref_kafe_%s.webp", "out": "kafe.html",  "mapcn": "咖啡馆", "mapen": "Kafe Dostoyevsky",
     "cover": "cover_kafe.webp", "floors": "屋顶 / 三楼 / 二楼 / 一楼", "desc": "鸡尾酒吧 + 阅读室多层立体防守",
     "ey": "R6S · KAFE DOSTOYEVSKY · SETUP PLANNER", "h1": "咖啡馆 · 防守装修规划器",
     "title": "彩虹六号 · 咖啡馆防守装修规划器"},
    {"id": "bank", "data": "data_bank.json", "refpat": "ref_bank_%s.webp", "out": "bank.html",  "mapcn": "银行", "mapen": "Bank",
     "cover": "cover_bank.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "金库 + 柜员大厅经典银行攻防",
     "ey": "R6S · BANK · SETUP PLANNER", "h1": "银行 · 防守装修规划器",
     "title": "彩虹六号 · 银行防守装修规划器"},
    {"id": "oregon", "data": "data_oregon.json", "refpat": "ref_oregon_%s.webp", "out": "oregon.html", "mapcn": "俄勒冈", "mapen": "Oregon",
     "cover": "cover_oregon.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "儿童房 + 主卧 + 塔楼多点攻防",
     "ey": "R6S · OREGON · SETUP PLANNER", "h1": "俄勒冈 · 防守装修规划器",
     "title": "彩虹六号 · 俄勒冈防守装修规划器"},
    {"id": "border", "data": "data_border.json", "refpat": "ref_border_%s.webp", "out": "border.html", "mapcn": "边境", "mapen": "Border",
     "cover": "cover_border.webp", "floors": "屋顶 / 二楼 / 一楼", "desc": "海关 + 军械库口岸攻防",
     "ey": "R6S · BORDER · SETUP PLANNER", "h1": "边境 · 防守装修规划器",
     "title": "彩虹六号 · 边境防守装修规划器"},
    {"id": "coastline", "data": "data_coastline.json", "refpat": "ref_coastline_%s.webp", "out": "coastline.html", "mapcn": "海岸线", "mapen": "Coastline",
     "cover": "cover_coastline.webp", "floors": "屋顶 / 二楼 / 一楼", "desc": "水烟房 + 顶层套房度假村攻防",
     "ey": "R6S · COASTLINE · SETUP PLANNER", "h1": "海岸线 · 防守装修规划器",
     "title": "彩虹六号 · 海岸线防守装修规划器"},
    {"id": "consulate", "data": "data_consulate.json", "refpat": "ref_consulate_%s.webp", "out": "consulate.html", "mapcn": "领事馆", "mapen": "Consulate",
     "cover": "cover_consulate.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "领事办公室 + 车库多层攻防",
     "ey": "R6S · CONSULATE · SETUP PLANNER", "h1": "领事馆 · 防守装修规划器",
     "title": "彩虹六号 · 领事馆防守装修规划器"},
    {"id": "villa", "data": "data_villa.json", "refpat": "ref_villa_%s.webp", "out": "villa.html", "mapcn": "别墅", "mapen": "Villa",
     "cover": "cover_villa.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "飞行家 + 奖杯室 + 画廊豪宅攻防",
     "ey": "R6S · VILLA · SETUP PLANNER", "h1": "别墅 · 防守装修规划器",
     "title": "彩虹六号 · 别墅防守装修规划器"},
    {"id": "chalet", "data": "data_chalet.json", "refpat": "ref_chalet_%s.webp", "out": "chalet.html", "mapcn": "木屋", "mapen": "Chalet",
     "cover": "cover_chalet.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "主卧 + 游戏室 + 酒窖雪山木屋",
     "ey": "R6S · CHALET · SETUP PLANNER", "h1": "木屋 · 防守装修规划器",
     "title": "彩虹六号 · 木屋防守装修规划器"},
    {"id": "labs", "data": "data_labs.json", "refpat": "ref_labs_%s.webp", "out": "labs.html", "mapcn": "夜鹰实验室", "mapen": "Nighthaven Labs",
     "cover": "cover_labs.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "指挥室 + 外骨骼室科研设施攻防",
     "ey": "R6S · NIGHTHAVEN LABS · SETUP PLANNER", "h1": "夜鹰实验室 · 防守装修规划器",
     "title": "彩虹六号 · 夜鹰实验室防守装修规划器"},
    {"id": "lair", "data": "data_lair.json", "refpat": "ref_lair_%s.webp", "out": "lair.html", "mapcn": "巢穴", "mapen": "Lair",
     "cover": "cover_lair.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "面具室 + 导弹室夜鹰基地攻防",
     "ey": "R6S · LAIR · SETUP PLANNER", "h1": "巢穴 · 防守装修规划器",
     "title": "彩虹六号 · 巢穴防守装修规划器"},
    {"id": "skyscraper", "data": "data_skyscraper.json", "refpat": "ref_skyscraper_%s.webp", "out": "skyscraper.html", "mapcn": "摩天", "mapen": "Skyscraper",
     "cover": "cover_skyscraper.webp", "floors": "屋顶 / 二楼 / 一楼", "desc": "茶室 + 博物馆日式高楼攻防",
     "ey": "R6S · SKYSCRAPER · SETUP PLANNER", "h1": "摩天 · 防守装修规划器",
     "title": "彩虹六号 · 摩天防守装修规划器"},
    {"id": "themepark", "data": "data_themepark.json", "refpat": "ref_themepark_%s.webp", "out": "themepark.html", "mapcn": "主题公园", "mapen": "Theme Park",
     "cover": "cover_themepark.webp", "floors": "屋顶 / 二楼 / 一楼", "desc": "吧台 + 王座厅鬼屋乐园攻防",
     "ey": "R6S · THEME PARK · SETUP PLANNER", "h1": "主题公园 · 防守装修规划器",
     "title": "彩虹六号 · 主题公园防守装修规划器"},
    {"id": "emerald", "data": "data_emerald.json", "refpat": "ref_emerald_%s.webp", "out": "emerald.html", "mapcn": "翠绿平原", "mapen": "Emerald Plains",
     "cover": "cover_emerald.webp", "floors": "二楼 / 一楼", "desc": "总裁办公室 + 九十号庄园攻防",
     "ey": "R6S · EMERALD PLAINS · SETUP PLANNER", "h1": "翠绿平原 · 防守装修规划器",
     "title": "彩虹六号 · 翠绿平原防守装修规划器"},
    {"id": "kanal", "data": "data_kanal.json", "refpat": "ref_kanal_%s.webp", "out": "kanal.html", "mapcn": "运河", "mapen": "Kanal",
     "cover": "cover_kanal.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "服务器 + 皮划艇双楼海港攻防",
     "ey": "R6S · KANAL · SETUP PLANNER", "h1": "运河 · 防守装修规划器", "title": "彩虹六号 · 运河防守装修规划器"},
    {"id": "outback", "data": "data_outback.json", "refpat": "ref_outback_%s.webp", "out": "outback.html", "mapcn": "内陆", "mapen": "Outback",
     "cover": "cover_outback.webp", "floors": "屋顶 / 二楼 / 一楼", "desc": "洗衣房 + 爬行动物馆公路旅馆攻防",
     "ey": "R6S · OUTBACK · SETUP PLANNER", "h1": "内陆 · 防守装修规划器", "title": "彩虹六号 · 内陆防守装修规划器"},
    {"id": "fortress", "data": "data_fortress.json", "refpat": "ref_fortress_%s.webp", "out": "fortress.html", "mapcn": "堡垒", "mapen": "Fortress",
     "cover": "cover_fortress.webp", "floors": "二楼 / 一楼", "desc": "指挥官室 + 食堂摩洛哥要塞攻防",
     "ey": "R6S · FORTRESS · SETUP PLANNER", "h1": "堡垒 · 防守装修规划器", "title": "彩虹六号 · 堡垒防守装修规划器"},
    {"id": "favela", "data": "data_favela.json", "refpat": "ref_favela_%s.webp", "out": "favela.html", "mapcn": "贫民窟", "mapen": "Favela",
     "cover": "cover_favela.webp", "floors": "二楼 / 一楼", "desc": "服务器 + 彩色房屋巴西棚户攻防",
     "ey": "R6S · FAVELA · SETUP PLANNER", "h1": "贫民窟 · 防守装修规划器", "title": "彩虹六号 · 贫民窟防守装修规划器"},
    {"id": "stadiumbravo", "data": "data_stadiumbravo.json", "refpat": "ref_stadiumbravo_%s.webp", "out": "stadiumbravo.html", "mapcn": "体育场", "mapen": "Stadium Bravo",
     "cover": "cover_stadiumbravo.webp", "floors": "二楼 / 一楼", "desc": "军械库 + 顶层套房融合竞技场攻防",
     "ey": "R6S · STADIUM BRAVO · SETUP PLANNER", "h1": "体育场 · 防守装修规划器", "title": "彩虹六号 · 体育场防守装修规划器"},
    {"id": "house", "data": "data_house.json", "refpat": "ref_house_%s.webp", "out": "house.html", "mapcn": "小屋", "mapen": "House",
     "cover": "cover_house.webp", "floors": "屋顶 / 二楼 / 一楼 / 地下室", "desc": "主卧 + 粉色儿童房 + 车库经典民居",
     "ey": "R6S · HOUSE · SETUP PLANNER", "h1": "小屋 · 防守装修规划器",
     "title": "彩虹六号 · 小屋防守装修规划器"},
    {"id": "hereford", "data": "data_hereford.json", "refpat": "ref_hereford_%s.webp", "out": "hereford.html", "mapcn": "赫里福德基地", "mapen": "Hereford Base",
     "cover": "cover_hereford.webp", "floors": "屋顶 / 阁楼 / 三楼 / 二楼 / 一楼", "desc": "酿造室 + 阁楼 + 靶场训练基地老图",
     "ey": "R6S · HEREFORD BASE · SETUP PLANNER", "h1": "赫里福德基地 · 防守装修规划器",
     "title": "彩虹六号 · 赫里福德基地防守装修规划器"},
    {"id": "plane", "data": "data_plane.json", "refpat": "ref_plane_%s.webp", "out": "plane.html", "mapcn": "总统专机", "mapen": "Presidential Plane",
     "cover": "cover_plane.webp", "floors": "屋顶 / 上层 / 主客舱 / 货舱层", "desc": "会议室 + 货舱 + 驾驶舱三层专机",
     "ey": "R6S · PRESIDENTIAL PLANE · SETUP PLANNER", "h1": "总统专机 · 防守装修规划器",
     "title": "彩虹六号 · 总统专机防守装修规划器"},
    {"id": "yacht", "data": "data_yacht.json", "refpat": "ref_yacht_%s.webp", "out": "yacht.html", "mapcn": "游艇", "mapen": "Yacht",
     "cover": "cover_yacht.webp", "floors": "屋顶 / 顶层甲板 / 上层甲板 / 中层甲板 / 引擎甲板", "desc": "赌场 + 引擎室 + 驾驶舱破冰游艇",
     "ey": "R6S · YACHT · SETUP PLANNER", "h1": "游艇 · 防守装修规划器",
     "title": "彩虹六号 · 游艇防守装修规划器"},
    {"id": "tower", "data": "data_tower.json", "refpat": "ref_tower_%s.webp", "out": "tower.html", "mapcn": "高塔", "mapen": "Tower",
     "cover": "cover_tower.webp", "floors": "屋顶 / 顶层 / 夹层 / 二楼 / 一楼", "desc": "餐厅 + 画廊 + 旋转观光塔",
     "ey": "R6S · TOWER · SETUP PLANNER", "h1": "高塔 · 防守装修规划器",
     "title": "彩虹六号 · 高塔防守装修规划器"},
]

def floor_btns(d):
    order = d["floorOrder"]; names = d["floorNames"]; en = d.get("floorEn", {}); dflt = d.get("defaultFloor", order[0])
    out = []
    for f in order:
        out.append('    <button class="fbtn%s" data-f="%s">%s<span class="en">%s</span></button>'
                   % (" on" if f == dflt else "", f, names.get(f, f), en.get(f, "")))
    out += ['    <span class="fnote" id="fnote"></span>', '    <span class="spacer"></span>']
    return "\n".join(out)

def site_sel(d):
    out = ['    <span class="sitegrp">包点', '      <button class="sbtn on" data-site="all">全部</button>']
    for s in d.get("sites", []):
        out.append('      <button class="sbtn" data-site="%s">%s</button>' % (s["id"], s["n"]))
    out.append('    </span>')
    return "\n".join(out)

def ref_js_for(d, refpat):
    return "var REF={" + ",".join(
        '"%s":"data:image/webp;base64,%s"' % (f, b64(D + refpat % f)) for f in d["floorOrder"]) + "};"

def map_switch(cur):
    # 详细地图页只留「返回主页」按钮，换图走主页画廊
    return '<div class="mapsw"><a href="index.html" class="msw home" title="返回地图主页">🏠 主页</a></div>'

LEGEND = '''      <div class="card legcard">
        <details>
        <summary><h3>图例 <span class="mono">LEGEND</span><span class="fold"></span></h3></summary>
        <div class="leg">
          <div class="row"><span class="sw" style="background:rgba(255,179,0,.9);border-color:#8a6000"></span>橙板 = 可破坏墙（一格=一块板）</div>
          <div class="row"><span class="sw" style="background:rgba(178,196,214,.96);border-color:#f0f7ff"></span>银板 = 你放的强化板（点击放/取消）</div>
          <div class="row"><span class="sw" style="background:#0c0c0e;border-color:#46B36B;color:#46B36B;font-size:9px;display:flex;align-items:center;justify-content:center">洞</span>深色缺口 = 打的洞（蹲/枪/脚/翻）</div>
          <div class="row"><span class="sw" style="background:rgba(110,230,110,.5);border-color:#1ea03c"></span>绿框 = 地板天窗(hatch)</div>
          <div class="row"><span class="sw" style="background:rgba(255,105,105,.45);border-color:#dc3232"></span>红框 = 天花板天窗</div>
          <div class="row"><span class="sw" style="background:rgba(255,60,255,.15);border-color:#ff50ff"></span>洋红框 = 软地板区（可垂直打穿）</div>
          <div class="row"><span class="sw" style="background:rgba(0,214,255,.9);border-color:#04303a;border-radius:50%"></span>青点 = 摄像头</div>
          <div class="row"><span class="sw" style="background:rgba(190,110,255,.8);border-color:#501478"></span>紫块 = 无人机洞</div>
          <div class="row"><span class="sw" style="background:#fff;border-color:#999"></span>纯白墙 = 不可破坏（承重墙）</div>
          <div class="row"><span class="sw" style="background:repeating-linear-gradient(90deg,#fff 0 2px,#333 2px 4px);border-color:#999"></span>墙上条纹 = 窗户 · 缺口 = 门</div>
          <div class="row"><span class="sw bomb" style="width:16px;height:16px;font-size:9px">A</span>下包点(A/B)</div>
        </div>
        </details>
      </div>'''

VIEWER_STAGE = '''    <div class="viewer" id="viewer">
      <div class="canvas" id="canvas"><img id="refimg" alt=""><canvas id="mapcv"></canvas></div>
      <div class="ov" id="ov"></div>
      <div class="zc"><button id="zin">+</button><div class="lvl" id="zlvl">100%</div><button id="zout">−</button><button class="wide" id="zfit">适应</button></div>
      <div class="hint" id="modehint">滚轮缩放 · 拖动平移 · 高亮 = 可破坏墙/天窗等（见右侧图例）</div>
    </div>'''

VIEWER_TOOLS = '''      <div class="card" id="toolcard" style="border-color:rgba(232,135,58,.45)">
        <h3>防守装修 <span class="mono">SETUP</span></h3>
        <div class="armrow" id="armrow"><span>🛡 强化板（点墙板/天窗）</span><span class="armn-wrap">剩 <b id="armn">10</b>/10</span></div>
        <div class="gsec" style="margin-top:6px">打洞（选类型后点橙色墙板）</div>
        <div class="gpal" id="hpal"></div>
        <div id="gpal"></div>
        <p class="note2f">选中道具后<b>点地图放置</b>；点已放的图标=移除；数量为各干员自带配额。</p>
        <button class="saveimg" id="saveImg">📸 保存成图（当前楼层）</button>
        <button class="resetall" id="armClear">清空全部装修</button>
      </div>
'''

def page(title, ey, h1, small, headright, floor_btns_html, bar_extra, side_pre, side_post, disc, foot1, foot2, tail, js, ref_js="", page_data=None, bar2=""):
    bar2_html = ('  <div class="bar bar2">\n' + bar2 + '\n  </div>\n') if bar2 else ''
    return ('''<meta charset="utf-8">
<title>''' + title + '''</title>
<style>
''' + css + '''
</style>

<div class="wrap">
  <header class="top">
    <div class="brand">
      <span class="ey">''' + ey + '''</span>
      <h1>''' + h1 + '''
        <small>''' + small + '''</small>
      </h1>
    </div>
    ''' + headright + '''
  </header>

  <div class="bar" id="floorbar">
''' + floor_btns_html + '''
''' + bar_extra + '''
  </div>
''' + bar2_html + '''

  <div class="stage-wrap">
''' + VIEWER_STAGE + '''

    <div class="side">
''' + side_pre + LEGEND + side_post + '''
    </div>
  </div>

  <div class="disc">''' + disc + '''</div>

  <footer>
    <span>''' + foot1 + '''</span>
    <span class="mono">''' + foot2 + '''</span>
  </footer>
</div>

<div id="pop"></div>
''' + tail + '''
<script>
var DATA=''' + page_data + ''';
''' + ref_js + '''
''' + js + '''
</script>
''')

EXPMODAL = '''<div id="expmodal"><div class="ebox">
  <div class="eh"><b>📸 装修图已生成</b><button class="x" id="eclose">×</button></div>
  <img id="eimg" alt="导出图">
  <div class="ebtns"><a id="edl" class="saveimg" download>⬇ 下载 PNG</a></div>
  <p class="mnote">下载没反应的话，直接右键 / 长按上面的图片「另存为」即可。</p>
</div></div>'''

# ---------- 各地图规划器 ----------
for m in MAPS:
    d = json.load(io.open(D + m["data"], encoding="utf-8"))
    data_str = io.open(D + m["data"], encoding="utf-8").read()
    html = page(
        title=m["title"], ey=m["ey"], h1=m["h1"],
        small="现役官方地图 · 强化墙 / 打洞 / 全防守道具摆放 · 一键导出方案图",
        headright=map_switch(m["id"]),
        floor_btns_html=floor_btns(d),
        bar_extra=site_sel(d),
        bar2='''    <span class="barlabel">显示</span>
    <button class="tog on" id="tBase"><span class="dot"></span>原图底图</button>
    <button class="tog on" id="tMarks"><span class="dot"></span>破坏/摄像头标注</button>
    <button class="tog on" id="tLabels"><span class="dot"></span>房间名</button>
    <button class="tog" id="tFills"><span class="dot"></span>房间色块</button>''',
        side_pre=VIEWER_TOOLS, side_post="",
        disc='<b>说明：</b>底图=<b>现役版本官方俯视图</b>；高亮标注取自 r6calls.com 现役数据，可破坏墙已按游戏拆成<b>单块板</b>。<b>自定义装修：点橙墙板/绿天窗放强化板（共10块）；选洞型给软墙打洞（过人/对枪/修脚/翻越）；选道具点地图摆位</b>。所有摆放自动保存在本机。纯白墙=不可破坏；条纹=窗、缺口=门。板块数按长度推算，不对随时说。',
        foot1=m["mapcn"] + "防守装修规划器 · 现役官方地图 · 强化/打洞/道具/方案导出",
        foot2="LIVE MAP · DESTRUCTIBLES HIGHLIGHTED",
        tail=EXPMODAL, js=view_js, ref_js=ref_js_for(d, m["refpat"]), page_data=data_str)
    p = BASE + m["out"]
    io.open(p, "w", encoding="utf-8").write(html)
    print("->", p, len(html) // 1024, "KB")

# ---------- 主页（地图封面画廊，分排位 / 非排位 / 快速匹配三池） ----------
# 排位地图池（可编辑；轮换变了改这里）
RANKED = {"club", "kafe", "bank", "border", "chalet", "coastline", "consulate",
          "oregon", "skyscraper", "labs", "lair", "themepark", "emerald", "villa"}
# 快速匹配经典老图（不进标准 / 排位，仅快速匹配保留）
QUICK = {"house", "hereford", "plane", "yacht", "tower"}

def card_html(m, cls):
    nfl = m["floors"].count("/") + 1
    return '''    <a class="mcard %s" href="%s">
      <div class="mcov" style="background-image:url('data:image/webp;base64,%s')"><span class="mchip">%d 层</span></div>
      <div class="minfo">
        <div class="mtitle">%s <span class="men">%s</span></div>
        <div class="mdesc">%s</div>
        <div class="mmeta"><span class="mfl">%s</span><span class="mgo">打开规划器 →</span></div>
      </div>
    </a>
''' % (cls, m["out"], b64(D + m["cover"]), nfl, m["mapcn"], m["mapen"], m["desc"], m["floors"])

ranked_maps = [m for m in MAPS if m["id"] in RANKED]
quick_maps  = [m for m in MAPS if m["id"] in QUICK]
std_maps    = [m for m in MAPS if m["id"] not in RANKED and m["id"] not in QUICK]

def section(cls, title_cn, title_en, note, maps):
    if not maps: return ""
    return ('''  <div class="poolhead %s"><span class="pbar"></span><h2>%s <span class="poolen">%s</span></h2><span class="poolcnt">%d 张</span></div>
  <p class="poolnote">%s</p>
  <div class="mgrid">
''' % (cls, title_cn, title_en, len(maps), note)) + "".join(card_html(m, cls) for m in maps) + '''  </div>
'''

sections = section("ranked", "排位地图池", "RANKED POOL", "当前排位 / 竞技轮换的地图", ranked_maps) \
         + section("casual", "非排位 · 标准图", "STANDARD", "在标准 / 快速匹配里，但不进当前排位轮换", std_maps) \
         + section("quick", "快速匹配 · 经典老图", "QUICK MATCH", "退出标准竞技、仅快速匹配保留的经典地图", quick_maps)

home_html = '''<meta charset="utf-8">
<title>彩虹六号 · 防守装修规划器</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
''' + css + '''
.home-wrap{max-width:1216px;margin:0 auto;padding:40px 24px 60px}
.home-head{text-align:center;margin-bottom:6px}
.home-head .ey{font-family:var(--font-mono);font-size:11.5px;letter-spacing:.34em;text-transform:uppercase;color:var(--amber);font-weight:600}
.home-head h1{font-size:31px;margin:11px 0 9px;font-weight:800;letter-spacing:.01em}
.home-head p{font-size:14px;color:var(--ink-dim);margin:0 auto;max-width:640px;line-height:1.6}
.hero-stats{display:flex;align-items:center;justify-content:center;gap:15px;margin:20px 0 2px;font-size:12.5px;color:var(--ink-dim)}
.hero-stats b{font-family:var(--font-mono);font-size:17px;font-weight:800;color:var(--ink);margin-right:5px}
.hero-stats i{width:1px;height:15px;background:var(--line2)}
.hero-stats .s-rk b{color:var(--amber)}
.hero-stats .s-st b{color:var(--angle)}
.hero-stats .s-qk b{color:var(--roam)}
.poolhead{display:flex;align-items:center;gap:11px;margin:40px 0 2px;padding-bottom:9px;border-bottom:1px solid var(--line)}
.poolhead .pbar{width:4px;height:19px;border-radius:2px;background:var(--amber);flex:0 0 auto}
.poolhead.casual .pbar{background:var(--angle)}
.poolhead.quick .pbar{background:var(--roam)}
.poolhead h2{font-size:20px;font-weight:800;margin:0}
.poolhead .poolen{font-family:var(--font-mono);font-size:11px;letter-spacing:.18em;color:var(--amber);margin-left:6px}
.poolhead.casual .poolen{color:var(--angle)}
.poolhead.quick .poolen{color:var(--roam)}
.poolhead .poolcnt{margin-left:auto;font-size:12px;color:var(--ink-faint);font-family:var(--font-mono)}
.poolnote{font-size:12.5px;color:var(--ink-faint);margin:8px 0 15px}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(252px,1fr));gap:16px}
.mcard{position:relative;display:flex;flex-direction:column;background:var(--panel);border:1px solid var(--line);border-radius:15px;overflow:hidden;text-decoration:none;color:inherit;transition:transform .16s,border-color .16s,box-shadow .16s}
.mcard::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;z-index:2;background:var(--amber);opacity:.9}
.mcard.casual::before{background:var(--angle)}
.mcard.quick::before{background:var(--roam)}
.mcard:hover{transform:translateY(-4px);border-color:var(--amber);box-shadow:0 14px 34px rgba(0,0,0,.5)}
.mcard.casual:hover{border-color:var(--angle)}
.mcard.quick:hover{border-color:var(--roam)}
.mcard.casual .mgo{color:var(--angle)}
.mcard.quick .mgo{color:var(--roam)}
.mcov{position:relative;aspect-ratio:16/9;background-size:cover;background-position:center;border-bottom:1px solid var(--line)}
.mcov::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,15,20,0) 58%%,rgba(11,15,20,.5))}
.mchip{position:absolute;top:9px;left:9px;z-index:1;font-family:var(--font-mono);font-size:10px;font-weight:700;color:var(--ink);background:rgba(10,14,19,.68);border:1px solid var(--line2);border-radius:6px;padding:3px 7px;backdrop-filter:blur(3px)}
.minfo{padding:12px 14px 13px}
.mtitle{font-size:17px;font-weight:800}
.mtitle .men{font-family:var(--font-mono);font-size:10.5px;font-weight:500;color:var(--ink-faint);letter-spacing:.05em;margin-left:5px}
.mdesc{font-size:12.5px;color:var(--ink-dim);margin:5px 0 10px;line-height:1.5}
.mmeta{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-top:9px;border-top:1px solid var(--line)}
.mfl{font-size:10.5px;color:var(--ink-faint);font-family:var(--font-mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.mgo{font-size:12.5px;font-weight:700;color:var(--amber);flex:0 0 auto;white-space:nowrap}
.mcard:hover .mgo{text-decoration:underline}
.home-foot{text-align:center;margin-top:44px;font-size:12px;color:var(--ink-faint);line-height:1.7}
.home-foot a{color:var(--ink-dim)}
</style>

<div class="home-wrap">
  <div class="home-head">
    <span class="ey">R6S · SETUP PLANNER</span>
    <h1>彩虹六号 · 防守装修规划器</h1>
    <p>选一张地图开始规划：现役官方地图 · 强化墙 / 打洞 / 全防守道具摆放 · 一键导出方案图</p>
    <div class="hero-stats"><span><b>%d</b>张地图</span><i></i><span class="s-rk"><b>%d</b>排位</span><i></i><span class="s-st"><b>%d</b>非排位</span><i></i><span class="s-qk"><b>%d</b>经典</span></div>
  </div>
''' % (len(MAPS), len(ranked_maps), len(std_maps), len(quick_maps)) + sections + '''  <div class="home-foot">
    地图与结构数据取自 r6calls.com · 素材版权归 Ubisoft Entertainment · 个人非商业粉丝项目<br>
    <a href="https://github.com/linnnw14-max/r6-clubhouse-guide">GitHub 源码</a>
  </div>
</div>
'''
io.open(BASE + "index.html", "w", encoding="utf-8").write(home_html)
print("->", BASE + "index.html (主页)", len(home_html) // 1024, "KB")

# ---------- 会所校准工具（沿用 data.json，仅会所） ----------
club_data = io.open(D + "data.json", encoding="utf-8").read()
dataver = "clubhouse-" + hashlib.md5(club_data.encode("utf-8")).hexdigest()[:10]
assert "__DATAVER__" in edit_js
edit_js = edit_js.replace("__DATAVER__", dataver)
print("DATAVER =", dataver)
club = json.load(io.open(D + "data.json", encoding="utf-8"))

editor_side_pre = '''      <div class="card" style="border-color:rgba(232,135,58,.5)">
        <h3>怎么用 <span class="mono">HOW TO</span></h3>
        <ol class="howto">
          <li>开顶上<b>「🗺 底图对照」</b>：官方原图垫在格子下面，色块自动变半透明，<b>照着描</b>就行</li>
          <li><b>画格子</b>模式：右边选房间颜色（或橡皮擦），在图上<b>单击/拖动涂格子</b>，把形状改对</li>
          <li><b>拖标注</b>模式：按住房名/下包点拖=挪位置；点一下房名=改名/删除/恢复</li>
          <li>全部弄好点右上<b>「✅ 完成 · 复制校准结果」</b>，回对话框<b>粘贴发送</b></li>
        </ol>
        <p class="note2f">进度自动保存在当前这个浏览器里（换浏览器/无痕窗口看不到）。弄完记得点右上导出发我。</p>
        <button class="resetall" id="resetAll">全部恢复本版初始状态</button>
      </div>
      <div class="card" id="palcard" style="display:none;border-color:rgba(76,155,232,.5)">
        <h3>画格子调色板 <span class="mono">PALETTE</span></h3>
        <div class="pal" id="pal"></div>
        <div class="paltools">
          <button id="b1">笔刷 1格</button><button id="b3">笔刷 3格</button>
          <button id="undoBtn">↩ 撤销一笔</button>
          <button id="addRoom">＋ 新色块</button>
          <button id="resetGrid">恢复本层格子</button>
        </div>
      </div>
      <div class="card" id="delcard" style="display:none">
        <h3>已删除 <span class="mono">DELETED</span></h3>
        <div class="dellist" id="dellist"></div>
      </div>
'''
editor_tail = '''<div id="mini"></div>
<div id="modal"><div class="mbox">
  <div class="mh"><b>校准结果</b><span id="mstatus"></span><button class="x" id="mclose">×</button></div>
  <textarea id="mtext" readonly spellcheck="false"></textarea>
  <div class="mbtns"><button id="mcopy">📋 全选并复制</button><button id="msave">💾 存成文件</button></div>
  <p class="mnote">复制后，回到 Claude 对话框粘贴发送即可。</p>
</div></div>
'''
editor_html = page(
    title="彩虹六号 · 会所校准工具（拖标注 + 画格子）",
    ey="R6S · CLUBHOUSE · 校准工具", h1="会所 · 校准工具",
    small="拖标注挪房名 · 画格子改房间形状 → 点右上「复制校准结果」→ 粘贴发给 Claude",
    headright='<button class="exportbtn" id="exportBtn">✅ 完成 · 复制校准结果</button>',
    floor_btns_html=floor_btns(club),
    bar_extra='''    <button class="modebtn on" id="mLabel">✋ 拖标注</button>
    <button class="modebtn" id="mPaint">🖌 画格子</button>
    <button class="tog" id="tRef"><span class="dot"></span>🗺 底图对照</button>
    <button class="tog on" id="tLabels"><span class="dot"></span>房间名</button>
    <button class="tog" id="addLbl"><span class="dot"></span>＋ 新增房名</button>
    <span class="chgchip">已调整 <b id="chgn">0</b></span>''',
    side_pre=editor_side_pre, side_post="",
    disc='<b>这是校准工具：</b>房名/点位不准就<b>拖</b>，房间形状不对就切到<b>画格子</b>模式涂改（涂错了「撤销一笔」）。弄完点右上<b>「✅ 完成 · 复制校准结果」</b>粘贴发给 Claude，我来更新正式版。',
    foot1="会所校准工具 · 拖标注 + 画格子 + 底图对照描图 · 结果发回 Claude 生成正式版",
    foot2="CALIBRATION · DRAG & PAINT & TRACE",
    tail=editor_tail, js=edit_js,
    ref_js=ref_js_for(club, "ref_%s.webp"), page_data=club_data)
io.open(BASE + "校准工具.html", "w", encoding="utf-8").write(editor_html)
print("->", BASE + "校准工具.html", len(editor_html) // 1024, "KB")
