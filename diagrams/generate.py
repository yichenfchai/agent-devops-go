# -*- coding: utf-8 -*-
"""生成毕设论文用架构图（独立 SVG + 汇总 HTML 预览页）。"""
import os

OUT = os.path.dirname(os.path.abspath(__file__))

FONT = '"Microsoft YaHei","PingFang SC","Hiragino Sans GB","Source Han Sans SC","Noto Sans CJK SC",sans-serif'

GRAY    = "#64748b"
DARK    = "#0f172a"
MUTED   = "#64748b"
BLUE    = "#1d4ed8"
BLUE_F  = "#eff6ff"
GREEN   = "#047857"
GREEN_F = "#ecfdf5"
AMBER   = "#b45309"
AMBER_F = "#fffbeb"
RED     = "#b91c1c"
RED_F   = "#fef2f2"
SLATE   = "#475569"
SLATE_F = "#f1f5f9"
PURPLE  = "#6d28d9"
PURPLE_F= "#f5f3ff"
WHITE   = "#ffffff"

MK = [GRAY, BLUE, GREEN, AMBER, RED, SLATE, PURPLE]


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class D:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = []

    def raw(self, s):
        self.p.append(s)

    def box(self, x, y, w, h, fill=WHITE, stroke=SLATE, rx=8, sw=1.6, dash=None):
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        self.raw('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="%g"%s/>'
                 % (x, y, w, h, rx, fill, stroke, sw, da))

    def text(self, x, y, s, size=13, anchor="middle", weight="400", fill=DARK, op=None):
        o = ' opacity="%g"' % op if op else ""
        self.raw('<text x="%g" y="%g" font-size="%g" text-anchor="%s" font-weight="%s" fill="%s"%s>%s</text>'
                 % (x, y, size, anchor, weight, fill, o, _esc(s)))

    def line(self, x1, y1, x2, y2, stroke=GRAY, sw=1.6, dash=None):
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        self.raw('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"%s/>'
                 % (x1, y1, x2, y2, stroke, sw, da))

    def arrow(self, x1, y1, x2, y2, stroke=GRAY, sw=1.8, dash=None):
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        i = MK.index(stroke) if stroke in MK else 6
        self.raw('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g" marker-end="url(#a%d)"%s/>'
                 % (x1, y1, x2, y2, stroke, sw, i, da))

    def path(self, d, stroke=GRAY, sw=1.6, dash=None, arrow=True, fill="none"):
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        i = MK.index(stroke) if stroke in MK else 6
        m = ' marker-end="url(#a%d)"' % i if arrow else ""
        self.raw('<path d="%s" fill="%s" stroke="%s" stroke-width="%g"%s%s/>' % (d, fill, stroke, sw, da, m))

    def title(self, s, y=36, size=20):
        self.text(self.w / 2, y, s, size, weight="700", fill=DARK)

    def render(self):
        out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %g %g" width="%g" height="%g">' % (self.w, self.h, self.w, self.h)]
        out.append('<defs>')
        for i, c in enumerate(MK):
            out.append('<marker id="a%d" viewBox="0 0 10 10" refX="9.5" refY="5" markerWidth="6" markerHeight="6" '
                       'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker>' % (i, c))
        out.append('</defs>')
        out.append('<style>text{font-family:%s;}</style>' % FONT)
        out.append('<rect width="%g" height="%g" fill="#ffffff"/>' % (self.w, self.h))
        out.extend(self.p)
        out.append('</svg>')
        return "".join(out)


# ─────────────────────────────────────────────────────────────
# 图 3-1  系统总体架构图
# ─────────────────────────────────────────────────────────────
def d1():
    d = D(1240, 960)
    d.title("图 3-1  智能项目部署与运维工具 — 系统总体架构")

    d.box(110, 60, 220, 58, SLATE_F, SLATE)
    d.text(220, 86, "GitHub / GitLab", 14, weight="600")
    d.text(220, 105, "push · PR · tag 事件", 11.5, fill=MUTED)

    d.box(360, 60, 520, 58, SLATE_F, SLATE)
    d.text(620, 86, "Web UI（SPA）", 14, weight="600")
    d.text(620, 105, "项目列表 · 构建详情 · 实时日志 · 配置管理", 11.5, fill=MUTED)

    d.arrow(220, 118, 220, 170, BLUE)
    d.text(232, 148, "Webhook", 11.5, anchor="start", fill=MUTED)
    d.arrow(560, 118, 560, 170, GRAY)
    d.text(550, 148, "REST", 11.5, anchor="end", fill=MUTED)
    d.arrow(680, 170, 680, 118, GRAY, dash="5,4")
    d.text(692, 148, "SSE 实时日志", 11.5, anchor="start", fill=MUTED)

    # Access 层
    d.box(40, 170, 1160, 112, BLUE_F, BLUE, rx=10)
    d.text(62, 194, "Access 层 · 接入与鉴权", 13.5, anchor="start", weight="700", fill=BLUE)
    d.box(70, 205, 300, 60, WHITE, BLUE)
    d.text(220, 230, "Webhook Handler", 13.5, weight="600")
    d.text(220, 250, "HMAC 验签 · 幂等去重 · 立即入队", 11, fill=MUTED)
    d.box(470, 205, 300, 60, WHITE, BLUE)
    d.text(620, 230, "REST API Handler", 13.5, weight="600")
    d.text(620, 250, "项目 / 构建 / 日志 / 密钥", 11, fill=MUTED)
    d.box(870, 205, 300, 60, WHITE, BLUE)
    d.text(1020, 230, "认证 · 鉴权（RBAC）", 13.5, weight="600")
    d.text(1020, 250, "用户 · 角色 · 会话", 11, fill=MUTED)

    d.arrow(220, 282, 220, 352, BLUE)
    d.text(232, 322, "入队", 11.5, anchor="start", fill=MUTED)
    d.arrow(620, 282, 620, 352, GRAY)
    d.text(632, 322, "触发 / 查询", 11.5, anchor="start", fill=MUTED)

    # Core 层
    d.box(40, 350, 1160, 430, GREEN_F, GREEN, rx=10)
    d.text(62, 374, "Core 层 · 调度与执行（Go 并发核心）", 13.5, anchor="start", weight="700", fill=GREEN)
    d.box(70, 385, 300, 64, WHITE, GREEN)
    d.text(220, 410, "Scheduler", 13.5, weight="600")
    d.text(220, 431, "持久化队列 · 任务分发 · 同项目串行化", 11, fill=MUTED)
    d.box(470, 385, 300, 64, WHITE, GREEN)
    d.text(620, 410, "State Machine", 13.5, weight="600")
    d.text(620, 431, "状态迁移校验 · 事件审计", 11, fill=MUTED)
    d.box(870, 385, 300, 64, WHITE, GREEN)
    d.text(1020, 410, "Reconciler", 13.5, weight="600")
    d.text(1020, 431, "孤儿任务恢复 · 超时清理", 11, fill=MUTED)

    d.box(70, 478, 1100, 176, WHITE, GREEN, rx=10)
    d.text(92, 502, "Worker Pool —— 信号量限流（最大并发 N）", 12.5, anchor="start", weight="700", fill=GREEN)
    d.box(100, 512, 320, 94, GREEN_F, GREEN)
    d.text(260, 540, "Builder", 13.5, weight="600")
    d.text(260, 561, "Docker 容器隔离构建", 11.5)
    d.text(260, 583, "clone → install → test → build", 11, fill=MUTED)
    d.box(460, 512, 320, 94, GREEN_F, GREEN)
    d.text(620, 540, "Deployer", 13.5, weight="600")
    d.text(620, 561, "SSH 部署 / docker-compose", 11.5)
    d.text(620, 583, "健康检查 · 失败自动回滚", 11, fill=MUTED)
    d.box(820, 512, 320, 94, GREEN_F, GREEN)
    d.text(980, 540, "Diagnoser", 13.5, weight="600")
    d.text(980, 561, "LLM 智能诊断（异步）", 11.5)
    d.text(980, 583, "日志裁剪 · 脱敏 · 超时重试", 11, fill=MUTED)

    d.box(70, 676, 1100, 64, WHITE, PURPLE)
    d.text(620, 701, "Log Pipe（channel 广播）", 13.5, weight="600")
    d.text(620, 723, "容器日志 → ring buffer → 批量落库 → fan-out → SSE 实时推送", 11, fill=MUTED)

    d.arrow(320, 780, 320, 820, AMBER)
    d.text(332, 806, "状态 · 日志落库", 11.5, anchor="start", fill=MUTED)
    d.arrow(920, 780, 920, 820, RED)
    d.text(908, 806, "调用外部系统", 11.5, anchor="end", fill=MUTED)

    d.box(40, 820, 560, 110, AMBER_F, AMBER, rx=10)
    d.text(62, 844, "Storage 层", 13, anchor="start", weight="700", fill=AMBER)
    d.text(64, 868, "SQLite / PostgreSQL —— 项目 · 构建 · 部署 · 事件审计", 11.5, anchor="start")
    d.text(64, 891, "对象存储 —— 构建产物 / 镜像 tar · 日志分块（压缩）", 11.5, anchor="start")
    d.text(64, 914, "AES-GCM 密钥库 —— secrets / SSH 私钥", 11.5, anchor="start")

    d.box(640, 820, 560, 110, RED_F, RED, rx=10)
    d.text(662, 844, "External（全部接口抽象，可打桩单测）", 13, anchor="start", weight="700", fill=RED)
    d.text(664, 868, "Docker daemon —— 本机构建容器生命周期管理", 11.5, anchor="start")
    d.text(664, 891, "目标主机（SSH）—— docker-compose · 应用 · 反向代理", 11.5, anchor="start")
    d.text(664, 914, "LLM API —— OpenAI 兼容（云端 / vLLM / Ollama）", 11.5, anchor="start")
    return d


# ─────────────────────────────────────────────────────────────
# 图 3-2  构建全流程时序图
# ─────────────────────────────────────────────────────────────
def d2():
    d = D(1240, 900)
    d.title("图 3-2  构建与部署全流程时序图")

    lanes = [
        (130,  "GitHub/GitLab", "代码仓库"),
        (285,  "Access 层",     "Webhook / API"),
        (440,  "Scheduler",     "队列 · 状态机"),
        (595,  "Worker",        "构建/部署编排"),
        (750,  "Docker",        "本机构建容器"),
        (905,  "目标主机",      "Docker + 应用"),
        (1060, "LLM API",       "OpenAI 兼容"),
    ]
    for x, a, b in lanes:
        d.box(x - 72, 60, 144, 52, SLATE_F, SLATE)
        d.text(x, 82, a, 12.5, weight="600")
        d.text(x, 100, b, 10.5, fill=MUTED)
        d.line(x, 112, x, 800, GRAY, 1.2, dash="4,5")

    X = {n: x for x, n, _ in lanes}

    def msg(y, a, b, label, dash=None, color=GRAY):
        d.arrow(X[a], y, X[b], y, color, dash=dash)
        d.text((X[a] + X[b]) / 2, y - 8, label, 11.5, fill=DARK)

    msg(160, "GitHub/GitLab", "Access 层", "① push webhook 事件")
    msg(208, "Access 层", "Scheduler", "② HMAC 验签通过 → 生成 BuildRequest 入队", color=BLUE)
    msg(256, "Access 层", "GitHub/GitLab", "③ 202 Accepted（立即返回，不阻塞）", dash="5,4")
    msg(312, "Scheduler", "Worker", "④ 原子认领任务，获取信号量槽位", color=GREEN)

    # 自消息
    d.path("M 595 340 L 655 340 L 655 366 L 595 366", stroke=GREEN)
    d.text(640, 332, "⑤ 检测项目类型 → 生成 Pipeline 快照", 11.5, fill=DARK)

    msg(410, "Worker", "Docker", "⑥ 创建容器并执行构建步骤", color=GRAY)
    msg(458, "Docker", "Worker", "⑦ 日志流 stdout / stderr", dash="5,4")
    msg(506, "Worker", "LLM API", "⑧ 构建失败：提交日志尾部（已脱敏）", dash="5,4", color=AMBER)
    msg(554, "LLM API", "Worker", "⑨ 诊断建议（异步，不阻塞状态流转）", dash="5,4", color=AMBER)
    msg(602, "Worker", "目标主机", "⑩ SSH: docker-compose up -d 新镜像", color=RED)
    msg(650, "目标主机", "Worker", "⑪ 健康检查结果", dash="5,4", color=RED)
    msg(698, "Worker", "目标主机", "⑫ 健康检查失败 → 回滚上一版本", dash="5,4", color=RED)
    msg(746, "Worker", "Scheduler", "⑬ 状态落地 → DB（deployed / rolled_back）", color=GREEN)

    d.box(60, 820, 1120, 62, SLATE_F, SLATE, rx=8)
    d.text(80, 845, "实线：请求 / 指令流　　虚线：响应 / 条件分支流", 11.5, anchor="start", fill=DARK)
    d.text(80, 868, "③ 立即返回 202 是设计关键：webhook 不做构建，避免超时引发平台重试风暴　·　"
                    "⑤ Pipeline 以快照写入 builds.pipeline_json，保证历史构建可复现", 11, anchor="start", fill=MUTED)
    return d


# ─────────────────────────────────────────────────────────────
# 图 3-3  构建状态机
# ─────────────────────────────────────────────────────────────
def d3():
    d = D(1240, 540)
    d.title("图 3-3  构建与部署状态机")

    bw, bh = 140, 58
    top = 110
    bot = 300

    def st(x, y, name, fill, stroke, dash=None):
        d.box(x, y, bw, bh, fill, stroke, dash=dash)
        d.text(x + bw / 2, y + 35, name, 13, weight="600")

    st(60,   top, "queued",      WHITE, SLATE)
    st(300,  top, "running",     BLUE_F, BLUE)
    st(540,  top, "succeeded",   GREEN_F, GREEN)
    st(780,  top, "deploying",   BLUE_F, BLUE)
    st(1020, top, "deployed",    GREEN_F, GREEN)
    st(300,  bot, "failed",      RED_F, RED)
    st(780,  bot, "deploy_failed", RED_F, RED)
    st(1020, bot, "rolled_back", AMBER_F, AMBER)
    st(60,   bot, "diagnosed",   PURPLE_F, PURPLE, dash="5,4")

    def lbl(x, y, s):
        d.text(x, y, s, 11, fill=MUTED)

    d.arrow(200, 139, 300, 139, SLATE);  lbl(250, 130, "认领")
    d.arrow(440, 139, 540, 139, BLUE);   lbl(490, 130, "构建成功")
    d.arrow(680, 139, 780, 139, GREEN);  lbl(730, 130, "触发部署")
    d.arrow(920, 139, 1020, 139, GREEN); lbl(970, 130, "健康检查通过")

    d.arrow(370, 168, 370, 300, RED)
    lbl(380, 240, "构建失败")
    d.arrow(850, 168, 850, 300, RED)
    lbl(860, 240, "部署失败")

    d.arrow(920, 329, 1020, 329, AMBER); lbl(970, 320, "自动回滚")
    d.arrow(1090, 168, 1090, 300, AMBER)
    d.text(1078, 240, "手动回滚", 11, anchor="end", fill=MUTED)

    d.path("M 300 329 L 200 329", stroke=PURPLE, dash="4,4")
    lbl(250, 314, "异步诊断")

    d.box(40, 410, 1160, 100, SLATE_F, SLATE, rx=8)
    d.text(60, 436, "■ 主干流：queued → running → succeeded → deploying → deployed；失败分支：failed、deploy_failed → rolled_back", 11.5, anchor="start")
    d.text(60, 460, "■ 状态迁移逐条校验，非法迁移直接拒绝；每次迁移写入 build_events，支持构建时序回放与审计", 11.5, anchor="start")
    d.text(60, 484, "■ diagnosed 为异步标记位，不参与主干状态机；LLM 诊断失败不影响构建结果", 11.5, anchor="start", fill=MUTED)
    return d


# ─────────────────────────────────────────────────────────────
# 图 3-4  Go 并发模型拓扑
# ─────────────────────────────────────────────────────────────
def d4():
    d = D(1240, 660)
    d.title("图 3-4  Go 并发模型与 goroutine 拓扑")

    d.box(520, 50, 200, 54, PURPLE_F, PURPLE)
    d.text(620, 74, "main", 15, weight="700")
    d.text(620, 93, "装配依赖 · 启动 · 优雅关闭", 10.5, fill=MUTED)

    band = [
        (70,   180, "Scheduler",   "× 1"),
        (300,  260, "Worker Pool", "信号量限流 × N"),
        (610,  200, "HTTP Server", "每请求一个"),
        (860,  170, "Reconciler",  "× 1"),
        (1080, 140, "Signal",      "SIGTERM"),
    ]
    for x, w, a, b in band:
        d.arrow(620, 104, x + w / 2, 150, SLATE, 1.4)
        d.box(x, 150, w, 56, WHITE, SLATE)
        d.text(x + w / 2, 174, a, 13, weight="600")
        d.text(x + w / 2, 193, b, 10.5, fill=MUTED)

    d.arrow(430, 206, 430, 250, GREEN, 1.4, dash="5,4")
    d.arrow(710, 206, 1015, 250, BLUE, 1.4, dash="5,4")

    # Worker Pool 展开
    d.box(60, 250, 740, 260, GREEN_F, GREEN, rx=10)
    d.text(82, 274, "Worker Pool 展开 —— 每个构建一组 goroutine", 12.5, anchor="start", weight="700", fill=GREEN)
    d.box(80, 290, 700, 200, WHITE, GREEN, dash="5,4")
    d.text(96, 310, "per-build goroutine", 11.5, anchor="start", fill=GREEN)
    cells = [
        (95,  "Builder",    ["Docker 构建", "容器隔离执行", "ctx 超时取消"]),
        (265, "Log Reader", ["读取容器日志", "→ LogPipe", "逐行打时间戳"]),
        (435, "Log Writer", ["批量落库", "ring buffer", "慢订阅者丢弃"]),
        (605, "Diagnoser",  ["失败时异步", "调 LLM API", "脱敏 + 重试"]),
    ]
    for x, name, lines in cells:
        d.box(x, 325, 155, 145, GREEN_F, GREEN)
        cx = x + 77.5
        d.text(cx, 352, name, 12.5, weight="600")
        for i, t in enumerate(lines):
            d.text(cx, 378 + i * 26, t, 11, fill=MUTED)

    # HTTP 展开
    d.box(830, 250, 370, 260, BLUE_F, BLUE, rx=10)
    d.text(852, 274, "HTTP Server 展开", 12.5, anchor="start", weight="700", fill=BLUE)
    d.box(850, 295, 330, 95, WHITE, BLUE)
    d.text(1015, 322, "API / Webhook goroutine", 12.5, weight="600")
    d.text(1015, 344, "ctx 贯穿下游 · 客户端断开即取消", 11, fill=MUTED)
    d.text(1015, 366, "webhook 只入队，立即返回 202", 11, fill=MUTED)
    d.box(850, 405, 330, 90, WHITE, BLUE)
    d.text(1015, 432, "SSE 订阅 goroutine", 12.5, weight="600")
    d.text(1015, 454, "订阅 LogPipe 写入响应", 11, fill=MUTED)
    d.text(1015, 476, "慢客户端丢弃，绝不阻塞管道", 11, fill=MUTED)

    d.box(60, 540, 1140, 96, SLATE_F, SLATE, rx=8)
    d.text(80, 566, "■ 每个 goroutine 必须有明确退出路径（channel 关闭或 ctx 取消）—— 泄漏 goroutine 即内存泄漏", 11.5, anchor="start")
    d.text(80, 590, "■ 限流用 chan struct{} 信号量实现；背压天然形成：队列满 → webhook 503 → 平台自动重试", 11.5, anchor="start")
    d.text(80, 614, "■ 清理逻辑必须用 context.WithoutCancel，否则 ctx 取消后容器 / SSH 连接会泄漏", 11.5, anchor="start", fill=MUTED)
    return d


# ─────────────────────────────────────────────────────────────
# 图 3-5  部署拓扑图
# ─────────────────────────────────────────────────────────────
def d5():
    d = D(1240, 620)
    d.title("图 3-5  系统部署拓扑图")

    d.box(20, 120, 180, 76, SLATE_F, SLATE)
    d.text(110, 150, "开发者", 13.5, weight="600")
    d.text(110, 172, "git push", 11.5, fill=MUTED)

    d.box(240, 120, 190, 76, SLATE_F, SLATE)
    d.text(335, 150, "GitHub / GitLab", 12.5, weight="600")
    d.text(335, 172, "Webhook 事件", 11.5, fill=MUTED)

    d.arrow(200, 158, 240, 158, SLATE, 1.6)
    d.text(220, 148, "①", 11, fill=MUTED)
    d.arrow(430, 158, 470, 158, SLATE, 1.6)
    d.text(450, 148, "②", 11, fill=MUTED)

    d.box(470, 60, 330, 520, GREEN_F, GREEN, rx=10)
    d.text(492, 88, "CI 服务器（单二进制）", 13.5, anchor="start", weight="700", fill=GREEN)
    inner = [
        (100, 62, "Access 层",            ["Webhook · REST · Auth"]),
        (178, 84, "Core 层",              ["Scheduler · 状态机", "Worker Pool（并发构建）"]),
        (278, 58, "Log Pipe",             ["实时日志 → SSE"]),
        (352, 58, "Diagnoser",            ["LLM 诊断（HTTP）"]),
        (426, 100,"Storage",              ["SQLite / PostgreSQL", "对象存储 · 密钥库"]),
    ]
    for y, h, name, lines in inner:
        d.box(495, y, 280, h, WHITE, GREEN)
        d.text(635, y + 26, name, 12.5, weight="600")
        for i, t in enumerate(lines):
            d.text(635, y + 48 + i * 21, t, 11, fill=MUTED)

    d.box(880, 110, 320, 90, RED_F, RED)
    d.text(1040, 140, "本机 Docker daemon", 12.5, weight="600")
    d.text(1040, 162, "构建容器（隔离）", 11, fill=MUTED)
    d.text(1040, 183, "产物镜像 / tar 包", 11, fill=MUTED)

    d.box(880, 260, 320, 170, AMBER_F, AMBER)
    d.text(1040, 290, "目标主机（VPS）", 12.5, weight="600")
    d.text(1040, 314, "Docker + docker-compose", 11, fill=MUTED)
    d.text(1040, 336, "应用容器（新版本）", 11, fill=MUTED)
    d.text(1040, 358, "反向代理 / HTTPS", 11, fill=MUTED)
    d.text(1040, 380, "健康检查端点", 11, fill=MUTED)
    d.text(1040, 404, "保留最近 K 个版本（回滚）", 11, fill=MUTED)

    d.box(880, 490, 320, 90, PURPLE_F, PURPLE)
    d.text(1040, 520, "LLM API", 12.5, weight="600")
    d.text(1040, 542, "OpenAI 兼容协议", 11, fill=MUTED)
    d.text(1040, 563, "云端 / vLLM / Ollama", 11, fill=MUTED)

    d.arrow(800, 150, 880, 150, GRAY);  d.text(840, 142, "③ docker build", 10.5, fill=MUTED)
    d.arrow(800, 300, 880, 300, RED);   d.text(840, 292, "④ SSH 部署", 10.5, fill=MUTED)
    d.arrow(880, 350, 800, 350, RED, dash="5,4"); d.text(840, 342, "⑤ 健康检查", 10.5, fill=MUTED)
    d.arrow(800, 505, 880, 505, AMBER, dash="5,4"); d.text(840, 497, "⑥ 诊断请求", 10.5, fill=MUTED)
    d.arrow(880, 550, 800, 550, AMBER, dash="5,4"); d.text(840, 542, "⑦ 诊断建议", 10.5, fill=MUTED)
    return d


# ─────────────────────────────────────────────────────────────
# 图 3-6  数据模型 ER 图
# ─────────────────────────────────────────────────────────────
def d6():
    d = D(1240, 810)
    d.title("图 3-6  系统数据模型（ER 图）")

    def ent(x, y, w, name, fields, fill=WHITE, stroke=SLATE):
        h = 34 + len(fields) * 17 + 8
        d.box(x, y, w, h, fill, stroke, rx=6)
        d.raw('<path d="M %g %g h %g a 6 6 0 0 1 6 6 v 22 a 6 6 0 0 1 -6 6 h %g z" fill="%s" opacity="0.55"/>'
              % (x, y, w - 6, -(w), stroke))
        d.text(x + 12, y + 23, name, 13, anchor="start", weight="700", fill=WHITE)
        for i, f in enumerate(fields):
            d.text(x + 12, y + 51 + i * 17, f, 10.5, anchor="start", fill=DARK)
        return h

    ent(80, 90, 200, "users", ["id  PK", "email  UQ", "password_hash", "role", "created_at"], BLUE_F, BLUE)
    ent(330, 90, 230, "deploy_hosts", ["id  PK", "name / addr", "ssh_user", "ssh_key_enc  BLOB",
                                      "ssh_host_key", "work_dir", "health_check_url", "keep_versions"], BLUE_F, BLUE)
    ent(610, 90, 250, "projects", ["id  PK", "owner_id  FK → users", "repo_provider", "repo_full_name  UQ",
                                   "webhook_secret_enc", "detected_type", "pipeline_yaml",
                                   "deploy_host_id  FK", "build_timeout_s", "auto_rollback"], GREEN_F, GREEN)
    ent(910, 90, 200, "secrets", ["id  PK", "project_id  FK", "key", "value_enc  BLOB"], GREEN_F, GREEN)
    ent(610, 340, 250, "builds", ["id  PK", "project_id  FK", "number", "state", "trigger / ref",
                                  "commit_sha", "image_tag", "started_at / finished_at",
                                  "diagnosis", "diagnosis_state"], AMBER_F, AMBER)
    ent(290, 600, 220, "build_events", ["id  PK", "build_id  FK", "from_state", "to_state", "reason",
                                        "created_at"], PURPLE_F, PURPLE)
    ent(610, 600, 260, "deployments", ["id  PK", "build_id  FK", "project_id  FK", "state", "image_tag",
                                       "previous_deployment_id", "started_at", "finished_at"], AMBER_F, AMBER)
    ent(920, 600, 200, "log_chunks", ["id  PK", "build_id  FK", "seq  UQ", "content  BLOB", "byte_size"], PURPLE_F, PURPLE)

    def rel(x1, y1, x2, y2, label, lx=None, ly=None, anchor="middle"):
        d.arrow(x1, y1, x2, y2, GRAY, 1.4)
        d.text(lx if lx else (x1 + x2) / 2, ly if ly else (y1 + y2) / 2 - 6, label, 10.5, fill=MUTED, anchor=anchor)

    rel(280, 140, 610, 140, "1 : N", 445, 132)
    rel(560, 160, 610, 160, "1 : N", 585, 150)
    rel(860, 130, 910, 130, "1 : N", 885, 122)
    rel(735, 282, 735, 340, "1 : N", 745, 312, anchor="start")

    d.path("M 610 440 L 510 440 L 510 600", stroke=GRAY, sw=1.4)
    d.text(505, 530, "1 : N", 10.5, anchor="end", fill=MUTED)
    rel(700, 548, 700, 600, "1 : N", 710, 578, anchor="start")
    d.path("M 860 440 L 1000 440 L 1000 600", stroke=GRAY, sw=1.4)
    d.text(1008, 520, "1 : N", 10.5, anchor="start", fill=MUTED)

    d.path("M 870 660 L 900 660 L 900 692 L 870 692", stroke=AMBER, sw=1.4)
    d.text(905, 680, "回滚链", 10.5, anchor="start", fill=MUTED)

    d.text(620, 780, "虚线框外所有 BLOB 字段均为 AES-GCM 加密存储；主密钥经环境变量注入，不落库",
           11, fill=MUTED)
    return d


FIGS = [
    ("f1", "图 3-1  智能项目部署与运维工具 — 系统总体架构", d1, "3-1-系统总体架构图"),
    ("f2", "图 3-2  构建与部署全流程时序图", d2, "3-2-构建部署时序图"),
    ("f3", "图 3-3  构建与部署状态机", d3, "3-3-构建状态机"),
    ("f4", "图 3-4  Go 并发模型与 goroutine 拓扑", d4, "3-4-Go并发模型拓扑"),
    ("f5", "图 3-5  系统部署拓扑图", d5, "3-5-部署拓扑图"),
    ("f6", "图 3-6  系统数据模型（ER 图）", d6, "3-6-数据模型ER图"),
]

svgs = []
for fid, cap, fn, fname in FIGS:
    s = fn().render()
    with open(os.path.join(OUT, fname + ".svg"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n' + s)
    svgs.append((fid, cap, s))
    print("wrote", fname + ".svg")

html = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
        '<title>毕业设计插图 · 智能 CI/CD 系统</title>',
        '<style>',
        '@page{size:A4 landscape;margin:10mm}',
        'body{margin:0;padding:28px 32px;background:#fff;color:#0f172a;',
        'font-family:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif}',
        'h1{font-size:20px;margin:0 0 4px}',
        '.sub{font-size:13px;color:#64748b;margin-bottom:26px}',
        'figure{margin:0 0 40px}',
        'svg{width:100%;height:auto;display:block;border:1px solid #e2e8f0;border-radius:6px}',
        'figcaption{font-size:13px;color:#475569;margin-top:8px;text-align:center}',
        '@media print{svg{border:none}figure{page-break-inside:avoid}}',
        '</style></head><body>',
        '<h1>毕业设计插图 · 面向小型团队的智能项目部署与运维工具</h1>',
        '<div class="sub">共 6 张矢量图，可直接插入 Word / LaTeX；本页 Ctrl+P 可导出 A4 横向 PDF</div>']

for fid, cap, s in svgs:
    html.append('<figure id="%s">%s<figcaption>%s</figcaption></figure>' % (fid, s, cap))

html.append('</body></html>')

with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(html))
print("wrote index.html")
