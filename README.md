# R6 会所防守装修规划器（Clubhouse Setup Planner）

彩虹六号：围攻 **会所（Clubhouse）** 四层交互地图 + 防守方装修规划工具。单个 HTML 文件，打开即用。

**在线使用：** https://linnnw14-max.github.io/r6-clubhouse-guide/

## 功能

- **现役版本官方俯视图**为底图，四层切换（屋顶 / 二楼 / 一楼 / 地下室），滚轮缩放、拖动平移
- **可破坏结构高亮**：可破坏墙（按游戏拆成 56 块单板）、地板/天花板天窗、软地板区（可垂直打穿）、摄像头、无人机洞
- **强化装甲板**：点橙色墙板 / 绿框天窗放置，防守方配额 10 块
- **打洞**：四种洞型——过人洞（蹲洞）/ 对枪洞 / 修脚洞 / 翻越洞，选类型后点软墙板；已强化的墙不能打洞
- **31 种防守道具摆放**：通用装备（铁丝网/部署盾/防弹摄像头/视线遮断器）+ 全部干员专属道具（Bandit 电箱、Mira 黑镜、Kapkan 门雷……），数量按各干员配额
- 所有摆放**自动保存**在本机浏览器（localStorage），刷新不丢；「清空全部装修」连点两次一键重来

## 文件

| 文件 | 说明 |
|---|---|
| `index.html` | 主页面（规划器），自包含单文件，双击即用 |
| `calib.html` | 校准工具：拖房名/画格子修正地图数据，导出结果 |
| `src/` | 生成器源码：`data.json`（唯一数据源）→ `gen_pages.py` 生成两个页面 |

### 改数据 / 重新生成

```bash
cd src
python3 gen_pages.py        # 由 data.json 重新生成 index.html 和校准工具
python3 split_bw.py         # 墙板块数不对时改 OVERRIDES 后重跑（先跑 apply_marks.py 还原）
```

## 数据来源与致谢

- 楼层俯视图与结构标注数据来自 [r6calls.com](https://www.r6calls.com/)
- 地图与游戏素材版权归 Ubisoft Entertainment 所有
- 本项目为个人非商业粉丝作品，与 Ubisoft 无关

Rainbow Six Siege © Ubisoft Entertainment. This is a non-commercial fan project.
