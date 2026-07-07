(function(){
"use strict";
var CELL=DATA.cell,GW=DATA.gw,GH=DATA.gh,MAPW=1374,MAPH=1048,S=3;
var FLOORS=DATA.floors;
var ALPHA={gold:.82,room:.72,corr:.55,ext:.40};
var floor="2",baseOn=true,fillsOn=false,marksOn=true;
/* 包点选择：all=全显 1-4=只显该点并跳楼层 */
var selSite="all";
var SITES={"1":{f:"2",n:"卧室 · 健身房"},"2":{f:"2",n:"金库 · 监控室"},"3":{f:"1",n:"酒吧 · 大贮藏室"},"4":{f:"B",n:"教堂 · 军械库"}};
/* 原图底(2x) 预加载 */
var REFIMGS={};
if(typeof REF!=="undefined"){
  Object.keys(REF).forEach(function(f){
    var im=new Image();
    im.onload=function(){if(f===floor)drawFloor(floor);};
    im.src=REF[f];REFIMGS[f]=im;
  });
}
var MARKSTYLE={
  losf:{fill:"rgba(255,60,255,0.10)",stroke:"rgba(255,80,255,0.85)",lw:2,dash:[8,6]},
  bw:{fill:"rgba(255,179,0,0.85)",stroke:"rgba(40,25,0,0.9)",lw:2},
  fh:{fill:"rgba(110,230,110,0.45)",stroke:"rgba(30,160,60,0.95)",lw:3},
  ch:{fill:"rgba(255,105,105,0.40)",stroke:"rgba(220,50,50,0.95)",lw:3},
  dt:{fill:"rgba(190,110,255,0.75)",stroke:"rgba(80,20,120,0.9)",lw:2},
  cam:{}
};
var MARKORDER=["losf","bw","fh","ch","dt","cam"];
/* ---------- 自定义装修：强化板(点墙板/天窗) + 防守道具(选中后点地图放置) ---------- */
var ARMOR_MAX=10;
var GADGETS=[
 {sec:"通用装备"},
 {id:"wire",n:"铁丝网",i:"⛓",max:6,c:"#5a6570"},
 {id:"shield",n:"部署盾",i:"🛑",max:2,c:"#2a5a8a"},
 {id:"bpcam",n:"防弹摄像头",i:"📷",max:2,c:"#1a6a80"},
 {id:"obsblock",n:"视线遮断器",i:"🙈",max:3,c:"#3a4a5a"},
 {sec:"电子 / 拒破"},
 {id:"bandit",n:"Bandit 电箱",i:"🔋",max:4,c:"#8a6d1a"},
 {id:"kaid",n:"Kaid 电爪",i:"⚡",max:3,c:"#8a5a1a"},
 {id:"mute",n:"Mute 干扰器",i:"📵",max:4,c:"#5b4390"},
 {id:"jager",n:"Jäger ADS",i:"🎯",max:3,c:"#8a3a5e"},
 {id:"wamai",n:"Wamai 磁盘",i:"🧲",max:5,c:"#2a6a6a"},
 {sec:"情报 / 监控"},
 {id:"evileye",n:"Maestro 邪眼",i:"👁",max:2,c:"#8a2a2e"},
 {id:"blackeye",n:"Valk 黑眼",i:"📹",max:3,c:"#2a7a4a"},
 {id:"echo",n:"Echo 无人机",i:"🛸",max:2,c:"#4a4a7a"},
 {id:"mozzie",n:"Mozzie 铁蒺藜",i:"🕷",max:3,c:"#6a5a2a"},
 {id:"alibi",n:"Alibi 全息",i:"👤",max:3,c:"#7a3a3a"},
 {id:"skopos",n:"Skopós 傀儡",i:"🤖",max:2,c:"#3a5a7a"},
 {sec:"陷阱"},
 {id:"kapkan",n:"Kapkan 门雷",i:"🧨",max:5,c:"#7a2a2a"},
 {id:"frost",n:"Frost 冰垫",i:"🪤",max:3,c:"#3a6a8a"},
 {id:"lesion",n:"Lesion 毒针",i:"💉",max:9,c:"#5a7a2a"},
 {id:"ela",n:"Ela 震爆雷",i:"💥",max:3,c:"#6a3a7a"},
 {id:"thorn",n:"Thorn 荆棘雷",i:"🌵",max:3,c:"#4a6a3a"},
 {id:"fenrir",n:"Fenrir 恐惧雷",i:"💀",max:4,c:"#3a3a4a"},
 {id:"melusi",n:"Melusi 女妖",i:"📢",max:4,c:"#2a5a4a"},
 {id:"goyo",n:"Goyo 火山罐",i:"🔥",max:4,c:"#8a4a1a"},
 {id:"tubarao",n:"Tubarão 冰冻",i:"❄️",max:3,c:"#2a6a8a"},
 {id:"smoke",n:"Smoke 毒气罐",i:"☣️",max:3,c:"#5a6a2a"},
 {sec:"阵地 / 支援"},
 {id:"mira",n:"Mira 黑镜",i:"🪞",max:2,c:"#2a4a6a"},
 {id:"castle",n:"Castle 挡板",i:"🚧",max:3,c:"#6a5a1a"},
 {id:"aruni",n:"Aruni 激光门",i:"🔶",max:3,c:"#8a5a2a"},
 {id:"azami",n:"Azami 屏障",i:"🧱",max:5,c:"#5a4a6a"},
 {id:"tbird",n:"雷鸟 治疗站",i:"💚",max:3,c:"#2a7a5a"},
 {id:"rook",n:"Rook 装甲包",i:"🎒",max:1,c:"#4a5a2a"}
];
var GMAP={};GADGETS.forEach(function(g){if(g.id)GMAP[g.id]=g;});
/* 旧存档兼容：ads -> jager */
var GALIAS={ads:"jager"};
/* 打洞类型（软墙板专用，无数量限制） */
var HOLES=[
 {id:"crouch",n:"过人洞（蹲洞）",ch:"蹲",c:"#46B36B"},
 {id:"gun",n:"对枪洞",ch:"枪",c:"#4C9BE8"},
 {id:"feet",n:"修脚洞",ch:"脚",c:"#E5484D"},
 {id:"vault",n:"翻越洞",ch:"翻",c:"#B07FD8"}
];
var HMAP={};HOLES.forEach(function(h){HMAP[h.id]=h;});
var reinforced={},holes={},gads=[],selGad=null,selHole=null;
try{var _rs=localStorage.getItem("r6club_setup_v1");if(_rs){var _pp=JSON.parse(_rs);
  if(_pp&&_pp.ids)_pp.ids.forEach(function(id){reinforced[id]=true;});
  if(_pp&&_pp.holes)Object.keys(_pp.holes).forEach(function(k){if(HMAP[_pp.holes[k]])holes[k]=_pp.holes[k];});
  if(_pp&&_pp.gads)gads=_pp.gads.map(function(g){if(GALIAS[g.g])g.g=GALIAS[g.g];return g;}).filter(function(g){return GMAP[g.g]&&FLOORS[g.f];});
}}catch(e){}
function saveSetup(){try{localStorage.setItem("r6club_setup_v1",JSON.stringify({ids:Object.keys(reinforced),holes:holes,gads:gads}));}catch(e){}}
function armUsed(){return Object.keys(reinforced).length;}
function gadUsed(id){var n=0;gads.forEach(function(g){if(g.g===id)n++;});return n;}
function updateTools(flashArm){
  document.getElementById("armn").textContent=(ARMOR_MAX-armUsed());
  var row=document.getElementById("armrow");
  if(flashArm){row.classList.add("nomore");setTimeout(function(){row.classList.remove("nomore");},700);}
  GADGETS.forEach(function(g){
    if(!g.id)return;
    var b=document.getElementById("gb_"+g.id);if(!b)return;
    var left=g.max-gadUsed(g.id);
    b.querySelector(".gc").textContent=left+"/"+g.max;
    b.classList.toggle("empty",left<=0&&selGad!==g.id);
    b.classList.toggle("on",selGad===g.id);
  });
  HOLES.forEach(function(hh){
    var b=document.getElementById("hb_"+hh.id);if(!b)return;
    b.classList.toggle("on",selHole===hh.id);
  });
  var h=document.getElementById("modehint");
  h.textContent=selGad?("放置模式："+GMAP[selGad].n+"（点地图放置 · 点道具图标移除 · 再点按钮退出）")
              :selHole?("打洞模式："+HMAP[selHole].n+"（点橙色墙板打洞 · 同处再点=补上 · Esc退出）")
                      :"滚轮缩放 · 拖动平移 · 点墙板=强化 · 右侧选洞型/道具";
}
function buildHpal(){
  var box=document.getElementById("hpal");box.innerHTML="";
  HOLES.forEach(function(h){
    var b=document.createElement("div");b.className="gbtn";b.id="hb_"+h.id;
    b.innerHTML='<span class="gi" style="color:'+h.c+'">●</span><span class="gn">'+h.n+'</span>';
    b.addEventListener("click",function(){
      selHole=(selHole===h.id)?null:h.id;
      if(selHole)selGad=null;
      updateTools(false);
    });
    box.appendChild(b);
  });
}
function buildGpal(){
  var box=document.getElementById("gpal");box.innerHTML="";
  GADGETS.forEach(function(g){
    if(g.sec){var h=document.createElement("div");h.className="gsec";h.textContent=g.sec;box.appendChild(h);return;}
    var b=document.createElement("div");b.className="gbtn";b.id="gb_"+g.id;
    b.innerHTML='<span class="gi">'+g.i+'</span><span class="gn">'+g.n+'</span><span class="gc"></span>';
    b.addEventListener("click",function(){
      if(selGad===g.id){selGad=null;}
      else{
        if(g.max-gadUsed(g.id)<=0){b.classList.add("flash");setTimeout(function(){b.classList.remove("flash");},600);return;}
        selGad=g.id;selHole=null;
      }
      updateTools(false);
    });
    box.appendChild(b);
  });
}
var viewer=document.getElementById("viewer"),canvas=document.getElementById("canvas"),
    cv=document.getElementById("mapcv"),ctx=cv.getContext("2d"),
    ov=document.getElementById("ov"),zlvl=document.getElementById("zlvl"),fnote=document.getElementById("fnote");
var scale=1,tx=0,ty=0,fitScale=1,minScale=.2,maxScale=8;
var showLabels=true;
var marks=[];
cv.width=MAPW*S;cv.height=MAPH*S;
function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;");}
function hexA(hex,a){var n=parseInt(hex.slice(1),16);return"rgba("+(n>>16&255)+","+(n>>8&255)+","+(n&255)+","+a+")";}

/* ---------- 网格渲染（数据画格子，放大不糊） ---------- */
function gridLines(color){
  ctx.strokeStyle=color;ctx.lineWidth=1;ctx.beginPath();
  for(var gx=0;gx<=GW;gx++){ctx.moveTo(gx*CELL*S+.5,0);ctx.lineTo(gx*CELL*S+.5,GH*CELL*S);}
  for(var gy=0;gy<=GH;gy++){ctx.moveTo(0,gy*CELL*S+.5);ctx.lineTo(GW*CELL*S,gy*CELL*S+.5);}
  ctx.stroke();
}
function drawFloor(f){
  var F=FLOORS[f];F._id=f;
  var ref=REFIMGS[f];
  var photo=baseOn&&ref&&ref.complete&&ref.naturalWidth>0;
  ctx.fillStyle="#0b0f14";ctx.fillRect(0,0,cv.width,cv.height);
  if(photo)ctx.drawImage(ref,0,0,cv.width,cv.height);
  else gridLines("rgba(198,216,234,0.06)");
  if(fillsOn){
    var fac=photo?0.55:1;
    var col={};F.rooms.forEach(function(r){col[r.ch]=hexA(r.c,(ALPHA[r.t]||.7)*fac);});
    for(var gy=0;gy<GH;gy++){
      var row=F.grid[gy];
      for(var gx=0;gx<GW;gx++){
        var ch=row.charAt(gx);if(ch===".")continue;
        ctx.fillStyle=col[ch]||"rgba(120,120,120,.5)";
        ctx.fillRect(gx*CELL*S,gy*CELL*S,CELL*S,CELL*S);
      }
    }
    if(!photo)gridLines("rgba(9,12,17,0.32)");
  }
  if(marksOn)drawMarks(F);
}
function drawMarks(F){
  var mk=F.marks||{};
  MARKORDER.forEach(function(layer){
    var quads=mk[layer];if(!quads)return;
    var st=MARKSTYLE[layer];
    quads.forEach(function(q,qi){
      var rid=null,isR=false;
      if(layer==="bw"||layer==="fh"){rid=F._id+":"+layer+":"+qi;isR=!!reinforced[rid];}
      if(layer==="cam"){
        var cx=(q[0][0]+q[2][0])/2*S,cy=(q[0][1]+q[2][1])/2*S;
        ctx.beginPath();ctx.arc(cx,cy,11*S/3,0,6.2832);
        ctx.fillStyle="rgba(0,214,255,0.95)";ctx.fill();
        ctx.lineWidth=2.5;ctx.strokeStyle="#04303a";ctx.stroke();
        ctx.beginPath();ctx.arc(cx,cy,4*S/3,0,6.2832);ctx.fillStyle="#04303a";ctx.fill();
        return;
      }
      ctx.beginPath();
      ctx.moveTo(q[0][0]*S,q[0][1]*S);
      for(var i=1;i<4;i++)ctx.lineTo(q[i][0]*S,q[i][1]*S);
      ctx.closePath();
      var hole=(layer==="bw"&&rid)?holes[rid]:null;
      if(hole){
        var hs=HMAP[hole];
        ctx.fillStyle="rgba(12,12,14,0.92)";ctx.fill();
        ctx.lineWidth=2*S/3*1.6;ctx.strokeStyle=hs.c;ctx.stroke();
        var hcx=(q[0][0]+q[2][0])/2*S,hcy=(q[0][1]+q[2][1])/2*S;
        ctx.beginPath();ctx.arc(hcx,hcy,8.5*S/3,0,6.2832);
        ctx.fillStyle=hs.c;ctx.fill();
        ctx.lineWidth=2;ctx.strokeStyle="rgba(0,0,0,.55)";ctx.stroke();
        ctx.font="bold "+(9*S/3*1.15)+"px sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";
        ctx.fillStyle="#fff";ctx.fillText(hs.ch,hcx,hcy+0.5);
      }else if(isR){
        ctx.fillStyle="rgba(178,196,214,0.96)";ctx.fill();
        ctx.lineWidth=2.2*S/3*1.6;ctx.strokeStyle="rgba(240,247,255,0.95)";ctx.stroke();
        /* 板面画个加固十字 */
        ctx.beginPath();
        ctx.moveTo(q[0][0]*S,q[0][1]*S);ctx.lineTo(q[2][0]*S,q[2][1]*S);
        ctx.moveTo(q[1][0]*S,q[1][1]*S);ctx.lineTo(q[3][0]*S,q[3][1]*S);
        ctx.lineWidth=1.4*S/3*1.6;ctx.strokeStyle="rgba(70,90,110,0.9)";ctx.stroke();
      }else{
        if(st.fill){ctx.fillStyle=st.fill;ctx.fill();}
        if(st.stroke){
          ctx.lineWidth=(st.lw||2)*S/3*1.6;
          if(st.dash)ctx.setLineDash(st.dash.map(function(v){return v*S/3;}));
          ctx.strokeStyle=st.stroke;ctx.stroke();
          ctx.setLineDash([]);
        }
      }
    });
  });
}

/* ---------- 标注 ---------- */
function buildMarks(){
  ov.innerHTML="";marks=[];
  var F=FLOORS[floor];
  if(showLabels)F.labels.forEach(function(l){
    var e=document.createElement("div");e.className="m";
    var lb=document.createElement("div");lb.className="lbl "+(l.k==="obj"?"obj":l.k==="ext"?"ext":"");
    var h='<span class="cn">'+esc(l.cn)+'</span>';if(l.en)h+='<span class="en">'+esc(l.en)+'</span>';if(l.kind)h+='<span class="kd">'+esc(l.kind)+'</span>';
    lb.innerHTML=h;e.appendChild(lb);ov.appendChild(e);marks.push({el:e,x:l.x,y:l.y});
  });
  F.bombs.forEach(function(bm){
    if(selSite!=="all"&&bm.t.charAt(0)!==selSite)return;
    var e=document.createElement("div");e.className="m";var b=document.createElement("div");b.className="bomb";b.textContent=bm.t;e.appendChild(b);ov.appendChild(e);marks.push({el:e,x:bm.x,y:bm.y});});
  gads.forEach(function(g,gi){
    if(g.f!==floor)return;
    var spec=GMAP[g.g];
    var e=document.createElement("div");e.className="m";
    var d=document.createElement("div");d.className="gad";d.textContent=spec.i;d.title=spec.n+"（点击移除）";
    d.style.background=spec.c;
    d.addEventListener("pointerdown",function(ev){ev.stopPropagation();});
    d.addEventListener("click",function(ev){
      ev.stopPropagation();
      gads.splice(gi,1);saveSetup();updateTools(false);buildMarks();
    });
    e.appendChild(d);ov.appendChild(e);marks.push({el:e,x:g.x,y:g.y});
  });
  apply();
}
function apply(){
  canvas.style.transform="translate("+tx+"px,"+ty+"px) scale("+scale+")";
  zlvl.textContent=Math.round(scale/fitScale*100)+"%";
  /* Retina 大倍率下位图被拉伸发糊；平色格子用 pixelated 反而边缘锐利 */
  cv.style.imageRendering=(scale*(window.devicePixelRatio||1)>3.2)?"pixelated":"auto";
  for(var i=0;i<marks.length;i++){var m=marks[i];m.el.style.left=(tx+m.x*scale)+"px";m.el.style.top=(ty+m.y*scale)+"px";}
}
function fit(){
  var r=viewer.getBoundingClientRect();if(!r.width)return;
  var bb=FLOORS[floor].bbox;
  fitScale=Math.min(r.width/bb.w,r.height/bb.h)*.95;scale=fitScale;
  minScale=fitScale*.6;maxScale=fitScale*10;
  tx=(r.width-bb.w*scale)/2-bb.x*scale;ty=(r.height-bb.h*scale)/2-bb.y*scale;apply();
}
function zoomAt(px,py,f){var ns=clamp(scale*f,minScale,maxScale);if(ns===scale)return;tx=px-(px-tx)*(ns/scale);ty=py-(py-ty)*(ns/scale);scale=ns;apply();}
function vpt(cx,cy){var r=viewer.getBoundingClientRect();return{x:cx-r.left,y:cy-r.top};}

/* ---------- 缩放 / 平移 / 手势 ---------- */
viewer.addEventListener("wheel",function(ev){ev.preventDefault();var p=vpt(ev.clientX,ev.clientY);zoomAt(p.x,p.y,Math.pow(1.0016,-ev.deltaY*(ev.ctrlKey?9:1)));},{passive:false});
var gBase=null;
function onGesture(ev){
  ev.preventDefault();
  if(ev.type==="gesturestart"){gBase=scale;return;}
  if(ev.type==="gestureend"){gBase=null;return;}
  if(gBase==null)return;
  var p=vpt(ev.clientX,ev.clientY);
  var ns=clamp(gBase*ev.scale,minScale,maxScale);
  if(ns!==scale)zoomAt(p.x,p.y,ns/scale);
}
["gesturestart","gesturechange","gestureend"].forEach(function(t){viewer.addEventListener(t,onGesture,{passive:false});});
document.getElementById("zin").addEventListener("click",function(){var r=viewer.getBoundingClientRect();zoomAt(r.width/2,r.height/2,1.3);});
document.getElementById("zout").addEventListener("click",function(){var r=viewer.getBoundingClientRect();zoomAt(r.width/2,r.height/2,1/1.3);});
document.getElementById("zfit").addEventListener("click",fit);
viewer.addEventListener("dblclick",function(ev){var p=vpt(ev.clientX,ev.clientY);zoomAt(p.x,p.y,1.6);});

var pointers={},panStart=null,pinchStart=null;
function pinchState(){var ids=Object.keys(pointers),a=pointers[ids[0]],b=pointers[ids[1]];return{dist:Math.hypot(a.x-b.x,a.y-b.y)||1,cx:(a.x+b.x)/2,cy:(a.y+b.y)/2,scale:scale,tx:tx,ty:ty};}
var tapStart=null;
function distSeg(px,py,ax,ay,bx,by){
  var dx=bx-ax,dy=by-ay,L2=dx*dx+dy*dy;
  var t=L2?((px-ax)*dx+(py-ay)*dy)/L2:0;t=Math.max(0,Math.min(1,t));
  return Math.hypot(px-(ax+dx*t),py-(ay+dy*t));
}
function panelHit(mx,my){
  var F=FLOORS[floor],mk=F.marks||{};
  var layers=["bw","fh"];
  for(var li=0;li<layers.length;li++){
    var quads=mk[layers[li]];if(!quads)continue;
    for(var i=0;i<quads.length;i++){
      var q=quads[i];
      var a=[(q[0][0]+q[3][0])/2,(q[0][1]+q[3][1])/2],b=[(q[1][0]+q[2][0])/2,(q[1][1]+q[2][1])/2];
      var wid=Math.hypot(q[0][0]-q[3][0],q[0][1]-q[3][1]);
      if(distSeg(mx,my,a[0],a[1],b[0],b[1])<=wid/2+7)return floor+":"+layers[li]+":"+i;
    }
  }
  return null;
}
function handleTap(cx,cy){
  var r=viewer.getBoundingClientRect();
  var mx=(cx-r.left-tx)/scale,my=(cy-r.top-ty)/scale;
  if(selGad){
    var spec=GMAP[selGad];
    if(spec.max-gadUsed(selGad)<=0){selGad=null;updateTools(false);return;}
    gads.push({g:selGad,f:floor,x:Math.round(mx),y:Math.round(my)});
    if(spec.max-gadUsed(selGad)<=0)selGad=null;
    saveSetup();updateTools(false);buildMarks();
    return;
  }
  if(!marksOn)return;
  var id=panelHit(mx,my);
  if(!id)return;
  if(selHole){
    if(id.indexOf(":bw:")<0)return;                 /* 只有软墙能打洞 */
    if(reinforced[id]){updateTools(false);flashHole(selHole);return;}  /* 已强化不能打 */
    if(holes[id]===selHole)delete holes[id];
    else holes[id]=selHole;
    saveSetup();updateTools(false);drawFloor(floor);
    return;
  }
  if(holes[id]){delete holes[id];}                  /* 有洞先补洞 */
  else if(reinforced[id])delete reinforced[id];
  else{
    if(armUsed()>=ARMOR_MAX){updateTools(true);return;}
    reinforced[id]=true;
  }
  saveSetup();updateTools(false);drawFloor(floor);
}
function flashHole(hid){
  var b=document.getElementById("hb_"+hid);if(!b)return;
  b.classList.add("flash");setTimeout(function(){b.classList.remove("flash");},600);
}
viewer.addEventListener("pointerdown",function(ev){
  if(ev.pointerType==="mouse"&&ev.button!==0)return;
  if(ev.target.closest(".zc"))return;
  tapStart=(Object.keys(pointers).length===0)?{x:ev.clientX,y:ev.clientY}:null;
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
viewer.addEventListener("pointerup",function(ev){
  if(tapStart&&Math.hypot(ev.clientX-tapStart.x,ev.clientY-tapStart.y)<6&&Object.keys(pointers).length===1)handleTap(ev.clientX,ev.clientY);
  tapStart=null;endPtr(ev);
});viewer.addEventListener("pointercancel",function(ev){tapStart=null;endPtr(ev);});

/* ---------- 开关 / 图层 / 切层 ---------- */
var tLabels=document.getElementById("tLabels"),
    tBase=document.getElementById("tBase"),tFills=document.getElementById("tFills"),tMarks=document.getElementById("tMarks");
tBase.addEventListener("click",function(){baseOn=!baseOn;tBase.classList.toggle("on",baseOn);drawFloor(floor);});
tFills.addEventListener("click",function(){fillsOn=!fillsOn;tFills.classList.toggle("on",fillsOn);drawFloor(floor);});
tMarks.addEventListener("click",function(){marksOn=!marksOn;tMarks.classList.toggle("on",marksOn);drawFloor(floor);});
tLabels.addEventListener("click",function(){showLabels=!showLabels;tLabels.classList.toggle("on",showLabels);buildMarks();});
function switchFloor(f){
  floor=f;
  document.querySelectorAll(".fbtn").forEach(function(b){b.classList.toggle("on",b.getAttribute("data-f")===f);});
  fnote.textContent=FLOORS[f].note;
  drawFloor(f);fit();buildMarks();
}
document.querySelectorAll(".fbtn").forEach(function(b){b.addEventListener("click",function(){switchFloor(b.getAttribute("data-f"));});});

fnote.textContent=FLOORS[floor].note;
var clrArm=null;
document.getElementById("armClear").addEventListener("click",function(){
  var btn=this;
  if(armUsed()===0&&gads.length===0)return;
  if(!clrArm){
    btn.classList.add("confirm");btn.textContent="再点一次确认清空";
    clrArm=setTimeout(function(){clrArm=null;btn.classList.remove("confirm");btn.textContent="清空全部装修";},3000);
    return;
  }
  clearTimeout(clrArm);clrArm=null;
  btn.classList.remove("confirm");btn.textContent="清空全部装修";
  reinforced={};holes={};gads=[];selGad=null;selHole=null;
  saveSetup();updateTools(false);drawFloor(floor);buildMarks();
});
document.querySelectorAll(".sbtn").forEach(function(b){
  b.addEventListener("click",function(){
    var v=b.getAttribute("data-site");
    selSite=v;
    document.querySelectorAll(".sbtn").forEach(function(x){x.classList.toggle("on",x===b);});
    if(v!=="all"&&SITES[v].f!==floor)switchFloor(SITES[v].f);
    else buildMarks();
  });
});
buildHpal();buildGpal();updateTools(false);
window.addEventListener("resize",function(){fit();});
document.addEventListener("keydown",function(e){if(e.key==="Escape"&&(selGad||selHole)){selGad=null;selHole=null;updateTools(false);}});
drawFloor(floor);fit();buildMarks();
setTimeout(function(){fit();buildMarks();},70);
})();
