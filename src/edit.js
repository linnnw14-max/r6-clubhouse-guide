(function(){
"use strict";
var CELL=DATA.cell,GW=DATA.gw,GH=DATA.gh,MAPW=1374,MAPH=1048,S=3;
var ALPHA={gold:.82,room:.72,corr:.55,ext:.40};
var CH="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
var NEWC=["#E85D5D","#5DD3E8","#E8C25D","#9AE85D","#D77BE8","#5D8AE8","#E88A5D","#7BE8B2"];
var FNAME={"R":"屋顶","2":"二楼","1":"一楼","B":"地下室"};
var floor="2",mode="label",refOn=false;
var viewer=document.getElementById("viewer"),canvas=document.getElementById("canvas"),
    cv=document.getElementById("mapcv"),ctx=cv.getContext("2d"),refimg=document.getElementById("refimg"),
    ov=document.getElementById("ov"),zlvl=document.getElementById("zlvl"),fnote=document.getElementById("fnote");
var mini=document.getElementById("mini"),modal=document.getElementById("modal"),
    mtext=document.getElementById("mtext"),mstatus=document.getElementById("mstatus");
var scale=1,tx=0,ty=0,fitScale=1,minScale=.2,maxScale=8;
var showLabels=true;
var marks=[],draggingMark=false;
/* 存档 key 绑数据版本：DATAVER 由 gen_pages.py 按 data.json 内容哈希自动注入，永不忘换 */
var DATAVER="__DATAVER__";
var STORE="r6club_calib_"+DATAVER;
var NONCE=Math.random().toString(36).slice(2);
cv.width=MAPW*S;cv.height=MAPH*S;
function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;");}
function hexA(hex,a){var n=parseInt(hex.slice(1),16);return"rgba("+(n>>16&255)+","+(n>>8&255)+","+(n&255)+","+a+")";}

/* ---------- 工作数据(v2：含格子和调色板) ---------- */
function freshW(){
  var w={floors:{}};
  Object.keys(DATA.floors).forEach(function(f){
    var F=DATA.floors[f];
    w.floors[f]={
      labels:F.labels.map(function(l){return{cn:l.cn,ocn:l.cn,en:l.en||"",kind:l.kind||"",k:l.k||"room",x:l.x,y:l.y,ox:l.x,oy:l.y,moved:false,renamed:false,deleted:false,added:false};}),
      bombs:F.bombs.map(function(b){return{t:b.t,x:b.x,y:b.y,ox:b.x,oy:b.y,moved:false};}),
      rooms:F.rooms.map(function(r){return{ch:r.ch,cn:r.cn,c:r.c,t:r.t,added:false};}),
      grid:F.grid.slice()
    };
  });
  return w;
}
function shapeOK(w){
  try{
    if(!w||!w.floors)return false;
    var ok=true;
    Object.keys(DATA.floors).forEach(function(f){
      var F=w.floors[f];
      if(!F||!Array.isArray(F.labels)||!Array.isArray(F.bombs)||!Array.isArray(F.rooms)||!Array.isArray(F.grid)||F.grid.length!==GH){ok=false;return;}
      F.grid.forEach(function(r){if(typeof r!=="string"||r.length!==GW)ok=false;});
    });
    return ok;
  }catch(e){return false;}
}
var W=null;
try{var raw=localStorage.getItem(STORE);if(raw){var p=JSON.parse(raw);if(p&&p.v===2&&p.dataver===DATAVER&&shapeOK(p.w))W=p.w;}}catch(e){}
if(!W)W=freshW();
/* 无痕/受限模式下 localStorage 不可用：显式警告，别让用户白干 */
var storageOK=false;
try{localStorage.setItem(STORE+"_t","1");storageOK=localStorage.getItem(STORE+"_t")==="1";localStorage.removeItem(STORE+"_t");}catch(e){}
if(!storageOK){
  var warn=document.createElement("div");warn.id="savewarn";
  warn.textContent="⚠️ 这个窗口没法自动保存进度（可能是无痕/隐私模式）。请一次弄完并点右上「✅ 完成 · 复制校准结果」，或换普通窗口重新打开。";
  document.body.insertBefore(warn,document.body.firstChild);
}
function save(){try{localStorage.setItem(STORE,JSON.stringify({v:2,dataver:DATAVER,nonce:NONCE,ts:Date.now(),w:W}));}catch(e){}}
window.addEventListener("storage",function(e){
  if(e.key!==STORE||!e.newValue)return;
  try{
    var p=JSON.parse(e.newValue);
    if(p&&p.v===2&&p.dataver===DATAVER&&p.nonce!==NONCE&&shapeOK(p.w)){
      W=p.w;undoStack.length=0;lastCell=null;validateBrush();
      drawFloor(floor);buildMarks();buildPal();
    }
  }catch(err){}
});
function gridDiff(f){
  var a=DATA.floors[f].grid,b=W.floors[f].grid,n=0;
  for(var y=0;y<GH;y++){if(a[y]===b[y])continue;for(var x=0;x<GW;x++)if(a[y].charAt(x)!==b[y].charAt(x))n++;}
  return n;
}
function isChanged(it){return !!(it.moved||it.renamed||it.added);}
function countChanges(){
  var n=0;
  Object.keys(W.floors).forEach(function(f){
    W.floors[f].labels.forEach(function(l){if(l.deleted){n++;return;}if(isChanged(l))n++;});
    W.floors[f].bombs.forEach(function(b){if(b.moved)n++;});
    W.floors[f].rooms.forEach(function(r){if(r.added)n++;});
    n+=gridDiff(f)>0?1:0;
  });
  return n;
}
function updateCount(){
  var cells=0;Object.keys(W.floors).forEach(function(f){cells+=gridDiff(f);});
  document.getElementById("chgn").textContent=countChanges()+(cells?"处 · 涂改"+cells+"格":"处");
}

/* ---------- 渲染 ---------- */
function gridLines(color){
  ctx.strokeStyle=color;ctx.lineWidth=1;ctx.beginPath();
  for(var gx=0;gx<=GW;gx++){ctx.moveTo(gx*CELL*S+.5,0);ctx.lineTo(gx*CELL*S+.5,GH*CELL*S);}
  for(var gy=0;gy<=GH;gy++){ctx.moveTo(0,gy*CELL*S+.5);ctx.lineTo(GW*CELL*S,gy*CELL*S+.5);}
  ctx.stroke();
}
/* 底图对照(描图)时色块减淡，能透见官方蓝图 */
function cellAlpha(t){return (ALPHA[t]||.7)*(refOn?0.42:1);}
function roomColor(f,ch){
  var r=null;W.floors[f].rooms.forEach(function(x){if(x.ch===ch)r=x;});
  return r?hexA(r.c,cellAlpha(r.t)):"rgba(120,120,120,"+(refOn?.22:.5)+")";
}
function drawFloor(f){
  var Fw=W.floors[f];
  if(refOn)ctx.clearRect(0,0,cv.width,cv.height);
  else{ctx.fillStyle="#0b0f14";ctx.fillRect(0,0,cv.width,cv.height);}
  gridLines(refOn?"rgba(198,216,234,0.10)":"rgba(198,216,234,0.06)");
  var col={};Fw.rooms.forEach(function(r){col[r.ch]=hexA(r.c,cellAlpha(r.t));});
  var fallback="rgba(120,120,120,"+(refOn?.22:.5)+")";
  for(var gy=0;gy<GH;gy++){
    var row=Fw.grid[gy];
    for(var gx=0;gx<GW;gx++){
      var ch=row.charAt(gx);if(ch===".")continue;
      ctx.fillStyle=col[ch]||fallback;
      ctx.fillRect(gx*CELL*S,gy*CELL*S,CELL*S,CELL*S);
    }
  }
  gridLines("rgba(9,12,17,0.32)");
}
function paintCellPx(gx,gy){
  var ch=W.floors[floor].grid[gy].charAt(gx);
  ctx.clearRect(gx*CELL*S,gy*CELL*S,CELL*S,CELL*S);
  if(!refOn){ctx.fillStyle="#0b0f14";ctx.fillRect(gx*CELL*S,gy*CELL*S,CELL*S,CELL*S);}
  if(ch!=="."){ctx.fillStyle=roomColor(floor,ch);ctx.fillRect(gx*CELL*S,gy*CELL*S,CELL*S,CELL*S);}
  ctx.strokeStyle="rgba(9,12,17,0.32)";ctx.lineWidth=1;
  ctx.strokeRect(gx*CELL*S+.5,gy*CELL*S+.5,CELL*S,CELL*S);
}

/* ---------- 标注（可拖，画格子模式下禁用） ---------- */
function positionMark(m){m.el.style.left=(tx+m.it.x*scale)+"px";m.el.style.top=(ty+m.it.y*scale)+"px";}
function buildMarks(){
  ov.innerHTML="";marks=[];hideMini();
  var Fw=W.floors[floor];
  if(showLabels)Fw.labels.forEach(function(l){
    if(l.deleted)return;
    var e=document.createElement("div");e.className="m ed"+(isChanged(l)?" chg":"");
    var lb=document.createElement("div");lb.className="lbl "+(l.k==="obj"?"obj":l.k==="ext"?"ext":"");
    var h='<span class="cn">'+esc(l.cn)+'</span>';if(l.en)h+='<span class="en">'+esc(l.en)+'</span>';if(l.kind)h+='<span class="kd">'+esc(l.kind)+'</span>';
    lb.innerHTML=h;e.appendChild(lb);ov.appendChild(e);
    var m={el:e,it:l,type:"label"};marks.push(m);attachDrag(m);
  });
  Fw.bombs.forEach(function(b){
    var e=document.createElement("div");e.className="m ed"+(b.moved?" chg":"");
    var d=document.createElement("div");d.className="bomb";d.textContent=b.t;e.appendChild(d);ov.appendChild(e);
    var m={el:e,it:b,type:"bomb"};marks.push(m);attachDrag(m);
  });
  apply();updateCount();updateDelCard();
}
function attachDrag(m){
  m.el.addEventListener("pointerdown",function(ev){
    if(mode!=="label")return;
    if(ev.pointerType==="mouse"&&ev.button!==0)return;
    ev.stopPropagation();ev.preventDefault();hideMini();
    var sx=ev.clientX,sy=ev.clientY,ix=m.it.x,iy=m.it.y,drag=false;
    try{m.el.setPointerCapture(ev.pointerId);}catch(e){}
    function mv(e2){
      if(!drag&&Math.hypot(e2.clientX-sx,e2.clientY-sy)>3){drag=true;draggingMark=true;m.el.style.zIndex=9;}
      if(!drag)return;
      m.it.x=clamp(ix+(e2.clientX-sx)/scale,0,MAPW);
      m.it.y=clamp(iy+(e2.clientY-sy)/scale,0,MAPH);
      positionMark(m);
    }
    function up(e2){
      m.el.removeEventListener("pointermove",mv);m.el.removeEventListener("pointerup",up);m.el.removeEventListener("pointercancel",up);
      m.el.style.zIndex="";draggingMark=false;
      try{m.el.releasePointerCapture(ev.pointerId);}catch(e){}
      if(drag){m.it.moved=true;m.el.classList.add("chg");save();updateCount();}
      else if(e2.type==="pointerup")showMini(m,e2.clientX,e2.clientY);
    }
    m.el.addEventListener("pointermove",mv);m.el.addEventListener("pointerup",up);m.el.addEventListener("pointercancel",up);
  });
}
function showMini(m,cx,cy){
  var it=m.it,btns='<button data-a="reset">↩ 恢复原位</button>';
  if(m.type==="label")btns+='<button data-a="rename">✎ 改名</button><button data-a="del" class="danger">🗑 删除</button>';
  btns+='<button data-a="close">×</button>';
  mini.innerHTML='<div class="mt">'+esc(m.type==="bomb"?("下包点 "+it.t):(it.cn||it.t))+'</div><div class="mb">'+btns+'</div>';
  mini.style.display="block";
  var mw=mini.offsetWidth,mh=mini.offsetHeight;
  mini.style.left=Math.min(Math.max(cx-mw/2,8),window.innerWidth-mw-8)+"px";
  mini.style.top=Math.min(Math.max(cy-mh-16,8),window.innerHeight-mh-8)+"px";
  mini.querySelectorAll("button").forEach(function(b){
    b.addEventListener("click",function(ev){ev.stopPropagation();act(b.getAttribute("data-a"),m);});
  });
}
function act(a,m){
  var it=m.it;
  if(a==="reset"){it.x=it.ox;it.y=it.oy;it.moved=false;}
  else if(a==="rename"){var nn=prompt("这个房间叫什么？",it.cn);if(nn&&nn.trim()&&nn.trim()!==it.cn){it.cn=nn.trim();it.renamed=(it.cn!==it.ocn);}}
  else if(a==="del"){
    if(it.added){var arr=W.floors[floor].labels;var i=arr.indexOf(it);if(i>-1)arr.splice(i,1);}
    else it.deleted=true;
  }
  hideMini();save();buildMarks();
}
function hideMini(){mini.style.display="none";mini.innerHTML="";}
document.addEventListener("pointerdown",function(e){
  if(mini.style.display!=="none"&&!mini.contains(e.target)&&!e.target.closest(".m"))hideMini();
});
function updateDelCard(){
  var card=document.getElementById("delcard"),list=document.getElementById("dellist");
  var items=[];
  Object.keys(W.floors).forEach(function(f){
    W.floors[f].labels.forEach(function(l){if(l.deleted)items.push({f:f,l:l});});
  });
  if(!items.length){card.style.display="none";return;}
  card.style.display="";list.innerHTML="";
  items.forEach(function(o){
    var b=document.createElement("button");
    b.textContent=FNAME[o.f]+" · "+o.l.cn+"（点击恢复）";
    b.addEventListener("click",function(){o.l.deleted=false;save();buildMarks();});
    list.appendChild(b);
  });
}
document.getElementById("addLbl").addEventListener("click",function(){
  var nn=prompt("新房名叫什么？（会先放在画面正中，之后在「✋ 拖标注」模式下按住拖到对的位置）");
  if(!nn||!nn.trim())return;
  var r=viewer.getBoundingClientRect();
  var x=clamp((r.width/2-tx)/scale,0,MAPW),y=clamp((r.height/2-ty)/scale,0,MAPH);
  W.floors[floor].labels.push({cn:nn.trim(),ocn:nn.trim(),en:"",kind:"",k:"room",x:x,y:y,ox:x,oy:y,moved:true,renamed:false,deleted:false,added:true});
  save();
  if(mode!=="label")setMode("label");
  buildMarks();
});
document.getElementById("resetAll").addEventListener("click",function(){
  if(!confirm("确定把所有楼层的房名、下包点、涂改过的格子全部恢复到本版初始状态？\n（你改过的都会丢，此操作不可撤销）"))return;
  W=freshW();undoStack.length=0;lastCell=null;validateBrush();
  save();drawFloor(floor);buildMarks();buildPal();updateCount();
});

/* ---------- 画格子模式 ---------- */
var brush=null,bsize=1,painting=false,lastCell=null,undoStack=[],pendingSnap=null,paintPan=null;
function validateBrush(){
  if(brush===null||brush===".")return;
  var ok=false;W.floors[floor].rooms.forEach(function(r){if(r.ch===brush)ok=true;});
  if(!ok)brush=null;
}
function setMode(m){
  mode=m;hideMini();
  document.body.classList.toggle("painting",m==="paint");
  document.getElementById("mLabel").classList.toggle("on",m==="label");
  document.getElementById("mPaint").classList.toggle("on",m==="paint");
  var pc=document.getElementById("palcard");
  pc.style.display=(m==="paint")?"":"none";
  pc.style.order=(m==="paint")?"-1":"";
  document.getElementById("modehint").textContent=(m==="paint")
    ?"画格子：先在右边选颜色 → 左键单击/拖动=涂色 · 右键按住拖=移动地图 · 双指滚动=移动 · 捏合或⌃+滚轮=缩放"
    :"按住房名拖=挪位置 · 点一下房名=改名/删除/恢复 · 空白处拖=平移 · 滚轮=缩放";
}
function flashPal(){
  var pc=document.getElementById("palcard");
  pc.classList.add("flash");
  document.getElementById("modehint").textContent="← 先在右边「画格子调色板」里点一个房间颜色（或橡皮擦），再来涂";
  setTimeout(function(){pc.classList.remove("flash");},1200);
}
function buildPal(){
  var box=document.getElementById("pal");box.innerHTML="";
  var Fw=W.floors[floor];
  var eb=document.createElement("button");eb.className="pbtn"+(brush==="."?" on":"");
  eb.innerHTML='<span class="chip" style="background:#0b0f14;border:1px dashed #63707f"></span>橡皮擦（清除格子）';
  eb.addEventListener("click",function(){brush=".";buildPal();});
  box.appendChild(eb);
  Fw.rooms.forEach(function(r){
    var b=document.createElement("button");b.className="pbtn"+(brush===r.ch?" on":"");
    b.innerHTML='<span class="chip" style="background:'+r.c+'"></span>'+esc(r.cn);
    b.addEventListener("click",function(){brush=r.ch;buildPal();});
    box.appendChild(b);
  });
  document.getElementById("b1").classList.toggle("on",bsize===1);
  document.getElementById("b3").classList.toggle("on",bsize===3);
}
document.getElementById("b1").addEventListener("click",function(){bsize=1;buildPal();});
document.getElementById("b3").addEventListener("click",function(){bsize=3;buildPal();});
document.getElementById("addRoom").addEventListener("click",function(){
  var nn=prompt("新色块叫什么名字？（之后用它涂格子；房名标签需另用「＋新增房名」加）");
  if(!nn||!nn.trim())return;
  var Fw=W.floors[floor];
  var used={};Fw.rooms.forEach(function(r){used[r.ch]=1;});
  var ch=null;for(var i=0;i<CH.length;i++){if(!used[CH[i]]){ch=CH[i];break;}}
  if(!ch){alert("这层色块已达上限");return;}
  var usedC={};Fw.rooms.forEach(function(r){usedC[r.c]=1;});
  var c=null;for(var j=0;j<NEWC.length;j++){if(!usedC[NEWC[j]]){c=NEWC[j];break;}}
  if(!c)c=NEWC[Fw.rooms.length%NEWC.length];
  Fw.rooms.push({ch:ch,cn:nn.trim(),c:c,t:"room",added:true});
  brush=ch;save();buildPal();updateCount();
});
document.getElementById("undoBtn").addEventListener("click",function(){
  var u=undoStack.pop();
  if(!u){document.getElementById("modehint").textContent="没有可撤销的笔画了";return;}
  if(u.f!==floor)switchFloor(u.f);
  W.floors[u.f].grid=u.grid;
  save();drawFloor(floor);updateCount();
});
document.getElementById("resetGrid").addEventListener("click",function(){
  if(!confirm("把「"+FNAME[floor]+"」这一层的格子恢复到本版初始状态？\n（只还原格子颜色，房名/下包点不受影响）"))return;
  undoStack.push({f:floor,grid:W.floors[floor].grid.slice()});
  W.floors[floor].grid=DATA.floors[floor].grid.slice();
  save();drawFloor(floor);updateCount();
});
function cellAt(cx,cy){
  var r=viewer.getBoundingClientRect();
  var mx=(cx-r.left-tx)/scale,my=(cy-r.top-ty)/scale;
  return{gx:Math.floor(mx/CELL),gy:Math.floor(my/CELL)};
}
function setCell(gx,gy){
  if(gx<0||gy<0||gx>=GW||gy>=GH)return;
  if(brush===null)return;
  if(brush!=="."){var ok=false;W.floors[floor].rooms.forEach(function(r){if(r.ch===brush)ok=true;});if(!ok)return;}
  var g=W.floors[floor].grid;
  if(g[gy].charAt(gx)===brush)return;
  /* 第一次真改动才把快照压进撤销栈（空笔不占坑） */
  if(pendingSnap){undoStack.push(pendingSnap);pendingSnap=null;if(undoStack.length>100)undoStack.shift();}
  g[gy]=g[gy].slice(0,gx)+brush+g[gy].slice(gx+1);
  paintCellPx(gx,gy);
}
function paintAt(cx,cy){
  var c=cellAt(cx,cy);
  var off=Math.floor(bsize/2);
  for(var dy=0;dy<bsize;dy++)for(var dx=0;dx<bsize;dx++)setCell(c.gx-off+dx,c.gy-off+dy);
  if(lastCell&&(Math.abs(c.gx-lastCell.gx)>1||Math.abs(c.gy-lastCell.gy)>1)){
    var steps=Math.max(Math.abs(c.gx-lastCell.gx),Math.abs(c.gy-lastCell.gy));
    for(var s=1;s<steps;s++){
      var ix=Math.round(lastCell.gx+(c.gx-lastCell.gx)*s/steps),iy=Math.round(lastCell.gy+(c.gy-lastCell.gy)*s/steps);
      for(var dy2=0;dy2<bsize;dy2++)for(var dx2=0;dx2<bsize;dx2++)setCell(ix-off+dx2,iy-off+dy2);
    }
  }
  lastCell=c;
}
viewer.addEventListener("contextmenu",function(ev){if(mode==="paint")ev.preventDefault();});
viewer.addEventListener("pointerdown",function(ev){
  if(mode!=="paint")return;
  if(ev.target.closest(".zc"))return;
  if(ev.pointerType==="mouse"&&ev.button===2){ /* 右键拖=平移（鼠标用户在画格子模式的移动手段） */
    ev.preventDefault();
    paintPan={x:ev.clientX,y:ev.clientY,tx:tx,ty:ty};
    try{viewer.setPointerCapture(ev.pointerId);}catch(e){}
    return;
  }
  if(ev.pointerType==="mouse"&&ev.button!==0)return;
  ev.preventDefault();
  if(brush===null){flashPal();return;}
  pendingSnap={f:floor,grid:W.floors[floor].grid.slice()};
  painting=true;lastCell=null;
  try{viewer.setPointerCapture(ev.pointerId);}catch(e){}
  paintAt(ev.clientX,ev.clientY);
});
viewer.addEventListener("pointermove",function(ev){
  if(mode!=="paint")return;
  if(paintPan){
    if(ev.pointerType==="mouse"&&!(ev.buttons&2)){paintPan=null;return;}
    tx=paintPan.tx+(ev.clientX-paintPan.x);ty=paintPan.ty+(ev.clientY-paintPan.y);apply();return;
  }
  if(!painting)return;
  if(ev.pointerType==="mouse"&&!(ev.buttons&1)){endPaint();return;}
  paintAt(ev.clientX,ev.clientY);
});
function endPaint(){
  paintPan=null;
  if(painting){
    painting=false;lastCell=null;pendingSnap=null;
    drawFloor(floor); /* 一笔结束全量重绘，消除局部重绘的格线叠深/丢浅线 */
    save();updateCount();
  }
}
viewer.addEventListener("pointerup",endPaint);viewer.addEventListener("pointercancel",endPaint);
document.getElementById("mLabel").addEventListener("click",function(){setMode("label");});
document.getElementById("mPaint").addEventListener("click",function(){setMode("paint");});

/* ---------- 导出 ---------- */
function buildExport(){
  var FN={"R":"屋顶Roof","2":"二楼2F","1":"一楼1F","B":"地下室B"};
  var out={version:"r6club-calib-v2",map:"Clubhouse 网格坐标 1374x1048 / 格子10px "+GW+"x"+GH,changes:countChanges(),floors:{}};
  Object.keys(W.floors).forEach(function(f){
    var Fw=W.floors[f],o={labels:[],bombs:[],deleted:[]};
    Fw.labels.forEach(function(l){
      if(l.deleted){o.deleted.push(l.renamed?(l.ocn+"（后改名为 "+l.cn+"）"):l.cn);return;}
      var e={cn:l.cn,en:l.en,kind:l.kind,k:l.k,x:Math.round(l.x),y:Math.round(l.y)};
      var st=[];if(l.added)st.push("新增");if(l.renamed)st.push("改名");if(l.moved&&!l.added)st.push("挪过");
      if(st.length)e.chg=st.join("+");
      if(l.renamed&&!l.added)e.origCn=l.ocn;
      o.labels.push(e);
    });
    Fw.bombs.forEach(function(b){var e={t:b.t,x:Math.round(b.x),y:Math.round(b.y)};if(b.moved)e.chg="挪过";o.bombs.push(e);});
    if(!o.deleted.length)delete o.deleted;
    o.rooms=Fw.rooms.map(function(r){var e={ch:r.ch,cn:r.cn,c:r.c,t:r.t};if(r.added)e.chg="新增";return e;});
    var gd=gridDiff(f);
    if(gd>0){
      o.gridChangedCells=gd;o.grid=Fw.grid;
      var known={".":1};Fw.rooms.forEach(function(r){known[r.ch]=1;});
      var unk={};Fw.grid.forEach(function(row){for(var i=0;i<row.length;i++){var c2=row.charAt(i);if(!known[c2])unk[c2]=1;}});
      var uks=Object.keys(unk);if(uks.length)o.unknownChars=uks;
    }
    out.floors[FN[f]]=o;
  });
  return "【R6会所 校准结果 v2】把这一整段直接粘贴发给 Claude 即可。\n共调整 "+out.changes+" 处。\n\n"+JSON.stringify(out,null,1);
}
function doCopy(txt){
  function ok(){mstatus.textContent="✓ 已复制，去对话框粘贴发送";mstatus.style.color="#46B36B";}
  function fail(){mstatus.textContent="自动复制没成功，点下面「全选并复制」";mstatus.style.color="#E8873A";}
  function legacy(){try{mtext.focus();mtext.select();document.execCommand("copy")?ok():fail();}catch(e){fail();}}
  if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(txt).then(ok,legacy);
  else legacy();
}
document.getElementById("exportBtn").addEventListener("click",function(){
  mtext.value=buildExport();mstatus.textContent="";modal.style.display="flex";doCopy(mtext.value);
});
document.getElementById("mcopy").addEventListener("click",function(){doCopy(mtext.value);mtext.focus();mtext.select();});
document.getElementById("msave").addEventListener("click",function(){
  var blob=new Blob([mtext.value],{type:"text/plain;charset=utf-8"});
  var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="R6会所校准结果.txt";
  document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},400);
});
document.getElementById("mclose").addEventListener("click",function(){modal.style.display="none";});
modal.addEventListener("click",function(e){if(e.target===modal)modal.style.display="none";});

/* ---------- 视图 ---------- */
function apply(){
  canvas.style.transform="translate("+tx+"px,"+ty+"px) scale("+scale+")";
  zlvl.textContent=Math.round(scale/fitScale*100)+"%";
  /* Retina 大倍率下位图被拉伸发糊；平色格子用 pixelated 反而边缘锐利 */
  cv.style.imageRendering=(scale*(window.devicePixelRatio||1)>3.2)?"pixelated":"auto";
  for(var i=0;i<marks.length;i++)positionMark(marks[i]);
}
function fit(){
  var r=viewer.getBoundingClientRect();if(!r.width)return;
  var bb=DATA.floors[floor].bbox;
  fitScale=Math.min(r.width/bb.w,r.height/bb.h)*.95;scale=fitScale;
  minScale=fitScale*.6;maxScale=fitScale*10;
  tx=(r.width-bb.w*scale)/2-bb.x*scale;ty=(r.height-bb.h*scale)/2-bb.y*scale;apply();
}
function zoomAt(px,py,f){var ns=clamp(scale*f,minScale,maxScale);if(ns===scale)return;tx=px-(px-tx)*(ns/scale);ty=py-(py-ty)*(ns/scale);scale=ns;apply();}
function vpt(cx,cy){var r=viewer.getBoundingClientRect();return{x:cx-r.left,y:cy-r.top};}
viewer.addEventListener("wheel",function(ev){
  ev.preventDefault();
  if(draggingMark||painting)return;
  if(mode==="paint"&&!ev.ctrlKey){
    if(ev.shiftKey&&ev.deltaX===0){tx-=ev.deltaY;}else{tx-=ev.deltaX;ty-=ev.deltaY;}
    apply();return;
  }
  /* Chrome 把触控板捏合合成为 ctrl+wheel 且 delta 很小，系数要放大约9倍才有正常手感 */
  var p=vpt(ev.clientX,ev.clientY);zoomAt(p.x,p.y,Math.pow(1.0016,-ev.deltaY*(ev.ctrlKey?9:1)));
},{passive:false});
var gBase=null;
function onGesture(ev){
  ev.preventDefault();
  if(ev.type==="gesturestart"){gBase=scale;return;}
  if(ev.type==="gestureend"){gBase=null;return;}
  if(gBase==null||draggingMark||painting)return;
  var p=vpt(ev.clientX,ev.clientY);
  var ns=clamp(gBase*ev.scale,minScale,maxScale);
  if(ns!==scale)zoomAt(p.x,p.y,ns/scale);
}
["gesturestart","gesturechange","gestureend"].forEach(function(t){viewer.addEventListener(t,onGesture,{passive:false});});
document.getElementById("zin").addEventListener("click",function(){var r=viewer.getBoundingClientRect();zoomAt(r.width/2,r.height/2,1.3);});
document.getElementById("zout").addEventListener("click",function(){var r=viewer.getBoundingClientRect();zoomAt(r.width/2,r.height/2,1/1.3);});
document.getElementById("zfit").addEventListener("click",fit);
viewer.addEventListener("dblclick",function(ev){if(mode==="paint"||ev.target.closest(".m"))return;var p=vpt(ev.clientX,ev.clientY);zoomAt(p.x,p.y,1.6);});

var pointers={},panStart=null,pinchStart=null;
function pinchState(){var ids=Object.keys(pointers),a=pointers[ids[0]],b=pointers[ids[1]];return{dist:Math.hypot(a.x-b.x,a.y-b.y)||1,cx:(a.x+b.x)/2,cy:(a.y+b.y)/2,scale:scale,tx:tx,ty:ty};}
viewer.addEventListener("pointerdown",function(ev){
  if(mode==="paint")return;
  if(ev.pointerType==="mouse"&&ev.button!==0)return;
  if(ev.target.closest(".zc")||ev.target.closest(".m")||ev.target.closest("#mini"))return;
  pointers[ev.pointerId]={x:ev.clientX,y:ev.clientY};
  var ids=Object.keys(pointers);
  if(ids.length===1){panStart={x:ev.clientX,y:ev.clientY,tx:tx,ty:ty};viewer.classList.add("grabbing");}
  else if(ids.length===2){panStart=null;pinchStart=pinchState();}
  try{viewer.setPointerCapture(ev.pointerId);}catch(e){}
});
viewer.addEventListener("pointermove",function(ev){
  if(!pointers[ev.pointerId])return;
  if(ev.pointerType==="mouse"&&ev.buttons===0){endPtr(ev);return;}
  pointers[ev.pointerId]={x:ev.clientX,y:ev.clientY};
  var ids=Object.keys(pointers);
  if(ids.length>=2&&pinchStart){
    var now=pinchState(),f=now.dist/pinchStart.dist,p=vpt(now.cx,now.cy),ns=clamp(pinchStart.scale*f,minScale,maxScale);
    tx=p.x-(p.x-pinchStart.tx)*(ns/pinchStart.scale);ty=p.y-(p.y-pinchStart.ty)*(ns/pinchStart.scale);scale=ns;apply();
  }else if(panStart){tx=panStart.tx+(ev.clientX-panStart.x);ty=panStart.ty+(ev.clientY-panStart.y);apply();}
});
function endPtr(ev){delete pointers[ev.pointerId];var ids=Object.keys(pointers);if(ids.length===0){panStart=null;pinchStart=null;viewer.classList.remove("grabbing");}else if(ids.length===1){pinchStart=null;panStart={x:pointers[ids[0]].x,y:pointers[ids[0]].y,tx:tx,ty:ty};}}
viewer.addEventListener("pointerup",endPtr);viewer.addEventListener("pointercancel",endPtr);

var tLabels=document.getElementById("tLabels"),tRef=document.getElementById("tRef");
tRef.addEventListener("click",function(){
  refOn=!refOn;tRef.classList.toggle("on",refOn);
  if(refOn){refimg.src=REF[floor]||"";refimg.style.display="block";
    document.getElementById("modehint").textContent="底图=育碧官方蓝图（仅本地对照用，分享版不带）。开「画格子」照着描就行。";}
  else refimg.style.display="none";
  drawFloor(floor);
});
tLabels.addEventListener("click",function(){showLabels=!showLabels;tLabels.classList.toggle("on",showLabels);buildMarks();});
function switchFloor(f){
  floor=f;
  document.querySelectorAll(".fbtn").forEach(function(b){b.classList.toggle("on",b.getAttribute("data-f")===f);});
  fnote.textContent=DATA.floors[f].note;hideMini();
  validateBrush();lastCell=null;
  if(refOn)refimg.src=REF[f]||"";
  drawFloor(f);fit();buildMarks();buildPal();
}
document.querySelectorAll(".fbtn").forEach(function(b){b.addEventListener("click",function(){switchFloor(b.getAttribute("data-f"));});});

fnote.textContent=DATA.floors[floor].note;
window.addEventListener("resize",function(){fit();});
setMode("label");
drawFloor(floor);fit();buildMarks();buildPal();updateCount();
setTimeout(function(){fit();buildMarks();},70);
})();
