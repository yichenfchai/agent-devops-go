# -*- coding: utf-8 -*-
"""统一文献库（开题报告与文献综述共用）。

设计要点
--------
1. **按键引用，编号自动生成**：正文写 ``[[key]]``，填充脚本按 GB/T 7714 顺序编码制
   （按正文首次出现顺序编号）自动替换为 ``[n]``，并生成对应顺序的参考文献表。
   这样增删文献不会引起编号错乱 —— 此前人工编号曾把 Beller 的 DOI 写错一位
   （10.1109/MSR.2017.61 实为另一篇论文），此类错误由自动编号杜绝。

2. **著录文本直接复用 review_refs.REFS**（那份文件里每条都带核实来源注释），
   不重新抄写，避免转录错误。

3. 核实纪律：每条文献的作者、题名、出处、卷期、页码、年份均已核对至权威来源
   （Crossref API / researchr / ACM DL / IEEE Xplore / SpringerLink /
   TU Delft Research Portal / jos.org.cn / NRC 官网 / arXiv abs 页）。
   未能核实原始出处的数据一律不引用；二手转述互相矛盾者一律不采用
   （如 Kerzazi 的工时数字有 336.18 与 904.64–2034.92 两说，故不引）。
"""
from review_refs import REFS as _R31

# ── 已有 31 条的键名（顺序与 review_refs.REFS 严格一致）──
KEYS31 = [
    "beck1999",          # [1]  Extreme Programming Explained
    "humble2010",        # [2]  Continuous Delivery
    "fitzgerald2017",    # [3]  Continuous software engineering: roadmap
    "kim2016",           # [4]  The DevOps Handbook
    "leite2019",         # [5]  A survey of DevOps concepts and challenges
    "ccallo2024",        # [6]  CI/CD in very small entities (SLR)
    "vassallo2017",      # [7]  A tale of CI build failures
    "beller2017",        # [8]  Oops, my tests broke the build
    "seo2014",           # [9]  Programmers' build errors (Google)
    "xu2025",            # [10] LogSage
    "wang2024",          # [11] RCAgent
    "hilton2016",        # [12] Usage, costs, benefits of CI
    "gallaba2018",       # [13] Noise and heterogeneity in build data
    "hassan2018",        # [14] CI failures in TravisTorrent (技术报告)
    "vassallo2018",      # [15] Un-break my build (Bart)
    "zhang2025",         # [16] AIOps survey in LLM era
    "merkel2014",        # [17] Docker
    "moriconi2024",      # [18] 博士学位论文（EURECOM）
    "kerzazi2014",       # [19] Why do automated builds break?
    "vasilescu2014",     # [20] CI in a social-coding world
    "zampetti2020",      # [21] CI bad practices
    "vassallo2016",      # [22] CD practices in a large financial organization
    "stahl2014",         # [23] Modeling CI practice differences
    "chen2015",          # [24] CD: huge benefits, but challenges too
    "martensson2017",    # [25] CI impediments in large-scale industry
    "ghaleb2019",        # [26] Long duration of CI builds
    "soares2022",        # [27] Effects of CI: SLR
    "roy2024",           # [28] LLM-based agents for RCA
    "astekin2024",       # [29] LLMs for log parsing
    "kang2026",          # [30] 康俊驰等，软件学报（中文）
    "mcintosh2014",      # [31] Mining co-change information
]
assert len(KEYS31) == len(_R31) == 31, (len(KEYS31), len(_R31))
assert len(set(KEYS31)) == 31, "键名重复"

REFDB = dict(zip(KEYS31, _R31))

# ── 新增：人机协作自动化级别（LOA）理论与实证 ──
NEW = {
# 四类自动化功能模型（信息获取/信息分析/决策选择/行动执行）——本课题 LOA 策略引擎的理论基础
# 核实：Crossref 10.1109/3468.844354 → IEEE T-SMC-A, 2000, 30(3): 286-297，
#       作者 R. Parasuraman / T.B. Sheridan / C.D. Wickens ✓
"parasuraman2000":
    "PARASURAMAN R, SHERIDAN T B, WICKENS C D. A model for types and levels of human "
    "interaction with automation[J]. IEEE Transactions on Systems, Man, and Cybernetics — "
    "Part A: Systems and Humans, 2000, 30(3): 286-297.",

# 自动化十级量表的原始出处
# 核实：Crossref/DTIC 10.21236/ADA057655 → report, 1978, Sheridan & Verplank ✓
"sheridan1978":
    "SHERIDAN T B, VERPLANK W L. Human and computer control of undersea teleoperators[R]. "
    "Cambridge: MIT Man-Machine Systems Laboratory, 1978.",

# Sheridan 十级表的细化转述 + Endsley & Kaber 模型 + adaptive automation 讨论
# 核实：正确编号为 BNL-91017-2010（O'Hara & Higgins, 2010），经 GovInfo NUREG-CR-7264
#       参考文献条目与 SAGE 期刊引用格式两个独立来源确认。
# ★ 注意：初稿曾误标为 NUREG/CR-6635，而 NRC 官网显示该编号实为《Soft Controls》
#   (Stubler & O'Hara, 2000)，已更正。
"ohara2010":
    "O'HARA J M, HIGGINS J. Human-system interfaces to automatic systems: Review guidance "
    "and technical basis[R]. Upton: Brookhaven National Laboratory, BNL-91017-2010, 2010.",

# ★ 本课题「人为主导」设计选择的核心实证依据
# 核实：Crossref 10.1145/3744916.3773104 → ICSE '26（IEEE/ACM 第 48 届），pp.2440-2452，
#       6 位作者 Zhou/Saghi/Sabouri/Pandita/McGuire/Chattopadhyay ✓
#       数字（48.8% / 56.4% / 29.46% (238/808) / 90 种偏差·15 类 / 14 观察+22 问卷）
#       已从 arXiv:2601.08045 abs 页核对。
# ★ 第一作者是 Zhou，Sabouri 仅为 arXiv 提交者，勿误署。
"zhou2026":
    "ZHOU X, SAGHI Z, SABOURI S, et al. Cognitive biases in LLM-assisted software "
    "development[C]//Proceedings of the 2026 IEEE/ACM 48th International Conference on "
    "Software Engineering (ICSE '26). New York: ACM, 2026: 2440-2452.",

# 自动化偏差（automation bias）综述 —— 支撑「证据链强制绑定」的设计动机
# 核实：Crossref 10.1007/s00146-025-02422-7 → AI & Society, vol.41, pp.259-278，
#       在线首发 2025（MDPI 二手引用标 2026 卷期，著录以 Crossref 为准）✓
"romeo2025":
    "ROMEO G, CONTI D. Exploring automation bias in human–AI collaboration: A review and "
    "implications for explainable AI[J]. AI & Society, 2025, 41: 259-278.",
}

# ── 新增：开源工具（软件/电子资源类引用）──
# 若学院要求参考文献全为学术出版物，可将这三条改为脚注或在正文中描述而不列条目。
SOFTWARE = {
# analyzer 机制的借鉴来源：SRE 经验固化为 analyzer，AI 只在 analyzer 划定范围内解释
# 核实：项目 README 官方表述 "SRE experience codified into its analyzers"；
#       Apache-2.0；内置 pod/pvc/event/log 等十余个 analyzer，支持自写
"k8sgpt":
    "k8sgpt-ai. k8sgpt: Giving Kubernetes superpowers to everyone[EB/OL]. "
    "[2026-09-17]. https://github.com/k8sgpt-ai/k8sgpt.",

# toolset 抽象的借鉴来源：以声明式配置定义可用数据源与命令
# 核实：GitHub README —— CNCF Sandbox 项目，Robusta 创建、微软参与贡献；
#       agentic loop 查询实时可观测数据；toolset 以 YAML 声明工具（含 prerequisites 检查）
"holmesgpt":
    "HolmesGPT. HolmesGPT: The CNCF SRE agent for investigating production incidents "
    "and finding root causes[EB/OL]. [2026-09-17]. https://github.com/HolmesGPT/holmesgpt.",

# ask / architect / code 三档交互模式的借鉴来源
# 核实：官方文档 aider.chat/docs/usage/modes.html —— ask 模式「never make changes」，
#       architect 模式用两个模型（一个提方案、一个转成文件编辑）
"aider":
    "Aider-AI. Aider chat modes: ask / architect / code[EB/OL]. [2026-09-17]. "
    "https://aider.chat/docs/usage/modes.html.",

# 横向对比实验的轻量 CI 基线（同为 Go + SQLite 形态）
# 核实：官方 README 原文 "runs with SQLite as database by default. It requires around
#       100 MB of RAM (Server) and 30 MB (Agent) at runtime in idle mode."；Apache-2.0；
#       Codeberg 的主 CI/CD 引擎
"woodpecker":
    "woodpecker-ci. Woodpecker CI: A simple, yet powerful CI/CD engine with great "
    "extensibility[EB/OL]. [2026-09-17]. https://github.com/woodpecker-ci/woodpecker.",
}

REFDB.update(NEW)
REFDB.update(SOFTWARE)

TOTAL = len(REFDB)


def render(text, order=None):
    """把正文中的 ``[[key]]`` 替换为 ``[n]``。

    编号规则：GB/T 7714 顺序编码制 —— 按 key 在 ``order`` 中的首次出现顺序编号；
    未给定 order 时按 text 自身的首次出现顺序。
    返回 (替换后的文本, {key: 编号}, [按编号排序的 key 列表])。
    """
    import re
    scan = order if order is not None else text
    seen, num = [], {}
    for m in re.finditer(r"\[\[([A-Za-z0-9_]+)\]\]", scan):
        k = m.group(1)
        if k not in num:
            num[k] = len(num) + 1
            seen.append(k)

    missing = [k for k in re.findall(r"\[\[([A-Za-z0-9_]+)\]\]", text) if k not in REFDB]
    if missing:
        raise KeyError("未登记的文献键: %s" % sorted(set(missing)))

    def sub(m):
        return "[%d]" % num[m.group(1)]

    return re.sub(r"\[\[([A-Za-z0-9_]+)\]\]", sub, text), num, seen
