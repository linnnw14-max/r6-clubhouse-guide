# -*- coding: utf-8 -*-
# 从 data.json(唯一数据源) 生成 正式版 index.html 和 校准工具.html
# 以后改数据: 改 data.json → 重跑本脚本。用户涂改的格子/挪的标注 → 先用套用脚本更新 data.json。
import io, json, os, shutil, hashlib, base64

D = os.path.dirname(os.path.abspath(__file__)) + "/"
BASE = "/Users/laoba/Desktop/R6-Clubhouse-Guide/"

# 官方蓝图描图底图（只进校准工具，不进可分享的正式版）
REF_JS = "var REF={" + ",".join(
    '"%s":"data:image/webp;base64,%s"' % (f, base64.b64encode(open(D + "ref_%s.webp" % f, "rb").read()).decode())
    for f in ["R", "2", "1", "B"]
) + "};"

data = io.open(D + "data.json", encoding="utf-8").read()
css = io.open(D + "style.css", encoding="utf-8").read()
view_js = io.open(D + "view.js", encoding="utf-8").read()
edit_js = io.open(D + "edit.js", encoding="utf-8").read()

# 2026-07-06 用户要求：校准工具里把已有房间涂色全清掉（保留房名/点位/调色板），从空白格子照官方底图重描。
# 正式版 index.html 仍用 data.json 里的彩色格子；等用户描完的 v2 导出套用后，把这个开关改回 False。
EDITOR_GRID_BLANK = False

data_obj = json.loads(data)
if EDITOR_GRID_BLANK:
    import copy
    eobj = copy.deepcopy(data_obj)
    blank = "." * eobj["gw"]
    for f in eobj["floors"]:
        eobj["floors"][f]["grid"] = [blank for _ in range(eobj["gh"])]
    edit_data = json.dumps(eobj, ensure_ascii=False)
    print("editor grid: BLANK (照底图重描模式)")
else:
    edit_data = data

# DATAVER = 编辑器基线数据的内容哈希，自动注入，忘 bump 这种事从机制上消灭
dataver = "clubhouse-" + hashlib.md5(edit_data.encode("utf-8")).hexdigest()[:10]
assert "__DATAVER__" in edit_js
edit_js = edit_js.replace("__DATAVER__", dataver)
print("DATAVER =", dataver)

FLOOR_BTNS = '''    <button class="fbtn" data-f="R">屋顶<span class="en">ROOF</span></button>
    <button class="fbtn on" data-f="2">二楼<span class="en">2F</span></button>
    <button class="fbtn" data-f="1">一楼<span class="en">1F</span></button>
    <button class="fbtn" data-f="B">地下室<span class="en">B</span></button>
    <span class="fnote" id="fnote"></span>
    <span class="spacer"></span>'''

LEGEND = '''      <div class="card">
        <h3>图例 <span class="mono">LEGEND</span></h3>
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
      </div>'''

VIEWER_STAGE = '''    <div class="viewer" id="viewer">
      <div class="canvas" id="canvas"><img id="refimg" alt=""><canvas id="mapcv"></canvas></div>
      <div class="ov" id="ov"></div>
      <div class="zc"><button id="zin">+</button><div class="lvl" id="zlvl">100%</div><button id="zout">−</button><button class="wide" id="zfit">适应</button></div>
      <div class="hint" id="modehint">滚轮缩放 · 拖动平移 · 高亮 = 可破坏墙/天窗等（见右侧图例）</div>
    </div>'''

def page(title, ey, h1, small, headright, bar_extra, side_pre, side_post, disc, foot1, foot2, tail, js, ref_js="", page_data=None):
    page_data = page_data if page_data is not None else data
    return '''<meta charset="utf-8">
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
''' + FLOOR_BTNS + '''
''' + bar_extra + '''
  </div>

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
'''

VIEWER_TOOLS = '''      <div class="card" id="toolcard" style="border-color:rgba(232,135,58,.45)">
        <h3>防守装修 <span class="mono">SETUP</span></h3>
        <div class="armrow" id="armrow"><span>🛡 强化板（点墙板/天窗）</span><span class="armn-wrap">剩 <b id="armn">10</b>/10</span></div>
        <div class="gsec" style="margin-top:6px">打洞（选类型后点橙色墙板）</div>
        <div class="gpal" id="hpal"></div>
        <div class="gpal" id="gpal"></div>
        <p class="note2f">选中道具后<b>点地图放置</b>；点已放的图标=移除；数量为各干员自带配额。</p>
        <button class="saveimg" id="saveImg">📸 保存成图（当前楼层）</button>
        <button class="resetall" id="armClear">清空全部装修</button>
      </div>
'''

# ---------- 正式版 ----------
viewer_html = page(
    title="彩虹六号 · 会所全楼层示意图（彩色格子·放大不糊）",
    ey="R6S · CLUBHOUSE SCHEMATIC · GRID",
    h1="会所 · 全楼层示意图",
    small="现役官方俯视图 · 高亮可破坏墙/天窗/软地板/摄像头 · 滚轮缩放",
    headright='<span class="verchip">实地校准 · <b>Y11S2</b></span>',
    bar_extra='''    <span class="sitegrp">包点
      <button class="sbtn on" data-site="all">全部</button>
      <button class="sbtn" data-site="1">①卧室健身</button>
      <button class="sbtn" data-site="2">②金库监控</button>
      <button class="sbtn" data-site="3">③酒吧贮藏</button>
      <button class="sbtn" data-site="4">④教堂军械</button>
    </span>
    <button class="tog on" id="tBase"><span class="dot"></span>原图底图</button>
    <button class="tog on" id="tMarks"><span class="dot"></span>破坏/摄像头标注</button>
    <button class="tog" id="tFills"><span class="dot"></span>房间色块</button>
    <button class="tog on" id="tLabels"><span class="dot"></span>房间名</button>''',
    side_pre=VIEWER_TOOLS, side_post="",
    disc='<b>说明：</b>底图=<b>现役版本官方俯视图</b>；高亮标注取自 r6calls.com 现役数据，可破坏墙已按游戏拆成<b>单块板</b>。<b>自定义装修：点橙墙板/绿天窗放强化板（共10块）；选洞型给软墙打洞（过人/对枪/修脚/翻越）；选道具点地图摆位</b>。所有摆放自动保存在本机。纯白墙=不可破坏；条纹=窗、缺口=门。板块数按长度推算，不对随时说。' ,
    foot1="会所全楼层地图 · 现役官方俯视图 + 可破坏墙/天窗/摄像头标注",
    foot2="LIVE MAP · DESTRUCTIBLES HIGHLIGHTED",
    tail='''<div id="expmodal"><div class="ebox">
  <div class="eh"><b>📸 装修图已生成</b><button class="x" id="eclose">×</button></div>
  <img id="eimg" alt="导出图">
  <div class="ebtns"><a id="edl" class="saveimg" download>⬇ 下载 PNG</a></div>
  <p class="mnote">下载没反应的话，直接右键 / 长按上面的图片「另存为」即可。</p>
</div></div>''',
    js=view_js,
    ref_js=REF_JS,
)

# ---------- 校准工具 ----------
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
    ey="R6S · CLUBHOUSE · 校准工具",
    h1="会所 · 校准工具",
    small="拖标注挪房名 · 画格子改房间形状 → 点右上「复制校准结果」→ 粘贴发给 Claude",
    headright='<button class="exportbtn" id="exportBtn">✅ 完成 · 复制校准结果</button>',
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
    tail=editor_tail,
    js=edit_js,
    ref_js=REF_JS,
    page_data=edit_data,
)

for name, html in [("index.html", viewer_html), ("校准工具.html", editor_html)]:
    p = BASE + name
    if os.path.exists(p):
        bk = BASE + name.replace(".html", "") + "_彩色底图_备份.html"
        if not os.path.exists(bk): shutil.copyfile(p, bk)
    io.open(p, "w", encoding="utf-8").write(html)
    print("->", p, len(html) // 1024, "KB")
