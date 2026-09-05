# ROAD — tie 开发计划

*EN: ROAD — tie Development Plan*

> **定位**：2026.1 采用「预发布 → 正式版」两段式开发。
>
> - **预发布段（preview\.6）**：全部新功能在 p.6.x 开发模块完成，开发号 **P.x.y.z**
>   （即 CHANGELOG 中的 p.x.y.z；模块 p.6.1=正确性 / p.6.2=功能 / p.6.3=性能 /
>   p.6.4=原语tie化 / p.6.5=trm-lite完善 / p.6.6=库补全 / p.6.7=trm-lite并行 /
>   p.6.8=Skia图形 / p.6.9=LSP重写）。
>
> - **正式版段（2026.1）**：preview\.6 发布后启动，**基于 preview\.6** 开发——**不引入
>   任何新功能**，只做优化与稳定性；开发号 **R.x.y.z**。正式版与预发布是**双轨**
>   （两个独立轨道）：预发布轨 **P.x.y.z** 做新功能，正式版轨 **R.x.y.z** 只做优化与
>   稳定性，两轨共用 x.y.z 格式但**各自独立编号、不互相延续**。

EN: Positioning — 2026.1 follows a two-stage "preview → stable" development model. The
preview stage (preview\.6) does all new features under p.6.x modules, numbered P.x.y.z
(p.x.y.z in the CHANGELOG). The stable stage (2026.1) starts after preview\.6 ships, is
based on preview\.6, introduces NO new features — only optimization and stability — and
numbers its work R.x.y.z. The stable and preview are **dual-track** (two independent
tracks): the preview track (P.x.y.z) does new features, the stable track (R.x.y.z) only
does optimization/stability; both share the x.y.z format but **number independently and
neither continues the other**.

### 开发计划（按优先级；开发模块 p.6.1=正确性 / p.6.2=功能 / p.6.3=性能 / p.6.4=原语tie化 / p.6.5=trm-lite完善 / p.6.6=库补全 / p.6.7=trm-lite并行 / p.6.8=Skia图形 / p.6.9=LSP重写）

**正确性（p.6.1，必查）**

- [x] p.6.1.1 import 文件不存在 → tiec 段错误 0xC0000005，改为报错退出（已修复 4095ee1，回归 err\_066–068）

- [x] p.6.1.2 smove.check\_fn\_walk 对 extern 越界隐患（TIE\_MOVE\_CHECK=1 门控，评估结论：越界读为真实缺陷，已修复）

- [x] p.6.1.3 lld 解析 tie\_interp.lib CRT printf 缺陷（评估结论：当前 clang 22.1.8 + lld-link 未复现，规避保留）

- [x] p.6.1.4 大函数寄存器分配缺陷（跨模块全局访问器 + 交错多表 push / 循环内字符串累加内存无界增长）：
  根治完成（2026-09-01）——根因定位为 str\_cat 每次 `+` 全新分配、旧中间串永不释放（tie 无 GC），
  `out = out + seg` 循环累加 = 时间/内存双 O(n²)；跨模块 struct 扩字段后 encode 型大函数 4 s 内 3–26 GB
  落地三件套：① ir.add\_operand 交错检测断言 + 修复 4 处潜伏交错点（操作数段错位）；② 循环内字符串自加
  自动 StringBuilder 提升（s21\_sb\_\*：循环入口预扫 AST 装载+注入循环前值、体内原地 append、出口 build 回写，
  安全核对=局部 string/引用纯净/无 goto；不满足保持原语义）——报告同源用例 n=20000 由 95 s 崩溃降至 656 ms、
  n=100000 784 ms 线性、输出逐字节一致；③ 回归探针 tests/hoist\_probe/（encode 复现 + 边界 31 断言）。
  此前"过渡规避（断言+4 处交错）"并入。
  字节表同族根治（跟进 dpcodec/jcc-pack 实机闭环）：`t = byte_concat(t, seg)` 循环累积每迭代新建整表且
  旧表永不释放 → 同构 O(n²) 无名分配（jcc-pack encode\_pack→build\_champ\_seg 实测修复前 3.7s 冲 4.5GB+）。
  irgen 循环入口 cbs\_scan 预扫 AST，对安全形态（首参=局部表槽名/引用纯净/无 goto）自动提升：循环前拷贝到
  私有累积表 acc（唯一引用），体内 tbl\_ensure+memcpy+set\_len 就地追加（摊销 O(1)），循环出口写回 t 槽；
  `zd.concat`（byte\_concat 薄包装）也纳入识别。实机验证：同一 jcc-pack + official-s19，修复前 4579MB 护栏
  终止 → 修复后 232MB 完整通过（65 棋子/35 羁绊/157 装备）；最小复现探针 tests/hoist\_probe/cbs\_encode\_repro.tie
  （跨模块 7 字段 struct + 数百字符中文文本合成 4000 条，修复前 2.5GB+ 终止→修复后 PASS）+
  cbs\_edge.tie 边界探针（单循环/多循环链/break/非纯净引用/空表入口）全绿；自举不动点 tiec2==tiec3 通过。

- [x] p.6.1.5 config 深合并边合并边 push 全局扁平表：复核结论——规避纪律安全（parse\_map\_body/
  parse\_array\_body/build\_defaults/merge\_maps/concat\_arrays 均先局部收集后统一登记或自我 append 全局末尾，
  map\_set 原地覆盖；新增 tests/s31/config\_merge\_stress.tie 四层链式深合并+嵌套/数组 concat/重置/交错访问
  31 断言全绿，config\_smoke 48/48）

- [x] p.6.1.6 str\_char 越界读（多字节 UTF-8 串 + len(s) 字节数上界 → 0xC0000005，jcc-pack extract 崩溃根因）：
  根治完成（2026-09-01）——根因定位 irgen 内联 str\_char(s,i) 的码点定位循环仅以 `k < i` 终止、无 pos 边界
  检查：调用方以 `i < len(s)`（len 读头 O(1) 返回**字节数**）为上界遍历含中文等多字节 UTF-8 的串时，
  i 会超过实际码点数，pos 越过串尾继续 s21\_utf8\_seq\_len/s21\_str\_byte 越界 GEP+load（拆分/不拆分 extract 均
  触发，此前"拆小函数规避"对含中文束方数据无效）。修复：cond 增补 `pos < blen` 终止 + 越界返回空串
  （res 槽 + after/ok/bad/merge CFG，与 s21\_codepoint\_to\_str 非法码点空串语义一致）。验证：
  极简探针（循环内 qs\_clean(skill\_desc) 中文 148 字节）修复前 AV → 修复后 A6 total=7414 全过；
  main\_unsplit 未拆分 extract official-s19 518 文件完整通过（65 棋子/35 羁绊/157 装备/258 符文）；
  自举 tiec\_s1→s2→s3 --emit-ir 逐字节一致（不动点）；tests/language 全量 PASS=96 与基线零差。

- [x] p.6.2.3 语句级宏 / 方法参数默认值 / ns\_call\_full\_name 的 using 支持（落地 2026-09-01）：
  ① **语句级宏**（块式准引用 `/` 展开为多条语句）探针全绿（tests/s33\_probe/b10\_stmt\_macro、
  \_probe62/s\_stmt\_macro\*：多语句展开 + 插值 + 宏内循环控制结构）；② **命名空间路径调用
  前缀丢失**：`ns::add(5)` 被 lexer/parser 拆成 N\_CALL(name=最后段) 丢弃 `ns::` 前缀 →
  报「未定义的函数 'add'」（自举编译链失效、显式路径调用不可用）。修复：
  pexpr 路径调用拼接全名（join\_path\_segs：`a::b::c` → N\_CALL name=完整路径，含泛型
  `ns::max<i64>()` 路径）；③ **默认值参数 LLVM 路径补齐缺失**：语义层已校验可选参数
  （sg\_required），但 irgen 调用点不生成缺省实参——`add(5)`（b 默认 10）运行时 b 取
  0/垃圾返回 5；struct 方法转发（tig\_struct\_method\_call）同样缺。修复：irgen\_call
  实参求值后按 sp\_defs 补齐函数定义参数节点的默认值字面量（含 u8/f64 等窄/宽类型
  tig\_coerce 转换，变参位保持打包逻辑）。验证：\_probe62/s\_default2/s\_method\_default/
  s\_default3 探针（普通函数/:: 路径调用/struct 方法/泛型多可选/u8 窄默认值）输出全符
  预期；自举 tiec2→tiec3 --emit-ir 逐字节一致（不动点）；tests/language PASS=56 与
  基线零差（3 项失败均为既有基线：db-vector-unsafe 工具链未实现 / filetype\_ir.ir 纯
  IR 不产 exe / extern\_decl 语义漂移）。

- [x] p.6.2.4 闭包参数 ref / 变参（落地 2026-09-01）：
  ① **闭包 ref 参数**（`ref table<T>`）：参数节点按 `s_vals` 记录引用标志；类型登记
  携带 ref 元数据（fn\_param\_refs + fn\_of2 查重，避免同签名多次登记拆开元数据段）；
  语义校验值调用时 ref 形参的实参必须是可寻址的表变量（字面量/下标/调用结果报错，
  类型须为表）；IR 生成直接绑定实参槽地址（不 alloca、不 store），体内读写即作用于
  调用方表；② **闭包变参**（`...T`，仅末位；parser 已拦非末尾，语义层兜底校验）：
  签名登记为 `table<T>`（与普通函数变参登记一致，保证 fn\_of2 查重命中同一签名）；
  调用点实参求值后按 `fixed_n = nparams-1` 切分，多余实参 `tig_variadic_table`
  打包为动态表（无多余实参也传空表），ref 实参传全局槽地址（kind 3 对齐普通函数
  by\_ref）；③ **函数值调用语义检查**按 `fn_has_var` 放行个数区间（必选 n-1 起，
  非变参仍严格等数），并校验 ref 实参可寻址。验证：\_probe62/s\_closure\_check /
  s\_closure2 探针（基础闭包 / 变参求和 / ref 写表 / 固定+变参混合 / ref+变参组合 /
  表元素间接调用 `funcs[0](...)` / 捕获+变参）输出全符预期；负例探针 s\_closure\_neg\*
  （非末尾变参 / ref 字面量实参 / 固定闭包缺参）均按预期报错；回归 tests/language
  variadic / byref\_table / table\_fn\_elem 与 p2b 函数值 p2d\_hof / p2d\_map / p1\_arrow
  全绿；自举 tiec2→tiec3 --emit-ir 逐字节一致（不动点）。

**功能限制（p.6.2，评估是否在正式版放开）**

- [x] p.6.2.1 枚举 payload 白名单（放开 f64/table/map；struct/嵌套 enum 仍限制——2026-09-01 落地，见已落地修复）

- [x] p.6.2.2 import result.tie 对 import assert.tie 的扫描顺序依赖（已修复——2026-09-01 落地，见已落地修复）

- [x] p.6.2.3 语句级宏 / 方法参数默认值 / ns\_call\_full\_name 的 using 支持（落地 2026-09-01，见已落地修复）

- [x] p.6.2.4 闭包参数 ref / 变参（落地 2026-09-01，见已落地修复）

- [x] p.6.2.5 driver 中 data/ui/db/port/zd 工具链「尚未实现」提示文本清理（--compress-data 已可用，data 分支改指 --compress-data、zd 分支改指 tiedb；文件头注释同步。探针验证 + 自举 tiec→tiec2→tiec3 不动点）

**性能（p.6.3，O(n²) 根治）**

- [x] p.6.3.1 config.parse\_string 循环逐字符 `out = out + c` → 改 StringBuilder（每日路径；实测 O(n²) 大输入 OOM → 线性，探针 800000 规模 sub-ms）

- [x] p.6.3.2 std/encoding base64 逐块拼接 → 大 payload 内存爆炸，改 StringBuilder（base64 编解码 + hex/url 编解码全覆盖）

- [x] p.6.3.3 std 哈希 hex 输出逐字节拼接（热度低，随 p.6.3.2 一并改；md5/sha1/sha256/sha512/sha3/blake2/blake3/siphash/shake/ascon\_mac/poly1305/hmac/hkdf/pbkdf2 全部 StringBuilder 化）

- [x] p.6.3.4 std/args 逐字符 + str\_char 双重平方（slice\_from 改 StringBuilder）

- [x] p.6.3.5 driver 残余逐字符拼接点（slice/trim/dir\_of 改 StringBuilder）

**原语tie化（p.6.4，消除 Rust 桥原语）**

- [x] p.6.4.1 UTF-16 宽字符共享桥 + 基础原语（args/cwd/set\_env/print\_err/rand\_range 内联 Win32/CRT + tig\_wide16/tig\_from\_wide16；path\_\* 留 p.6.4.10 后批次）

- [x] p.6.4.2 文件系统基础（file\_read/write/append/exists/delete/size/is\_dir/is\_file、mkdir\_all 内联 UTF-16 安全 \*W API）

- [x] p.6.4.3 文件系统扩展（copy\_dir/file\_copy/file\_move/remove\_dir\_all/list\_dir/walk\_dir 内联）

- [x] p.6.4.4 数值/字符串（parse\_float 内联十进制解析 + to\_string\_f64 内联 _gcvt，去 tie_\* 桥）

- [x] p.6.4.5 网络（net\_\*：Winsock2 内联直调 + 新增字节版 net\_tcp\_recv\_bytes/send\_bytes 供 TLS；g\_used\_wsock 链接）

- [x] p.6.4.6 进程捕获（exec\_output：CreatePipe+CreateProcessW+ReadFile 内联）

- [x] p.6.4.7 消息系统（msg\_\* 内联运行期全局消息表；msg\_t\_lang 未命中空串语义对齐 log 回退链）

- [x] p.6.4.8 正则（regex\_\* 纯 tie 最小引擎：字面量 pattern 内联回溯 VM；运行期 pattern 回退桥）

- [x] p.6.4.9 归档/HTTP（untar\_gz/unzip 内联 DEFLATE inflate 底座 + tar/zip 容器；http\_get/http\_get\_file Winsock 内联）

- [x] p.6.4.10 脚本通道+收尾（read\_line 内联；rand\_range 修 RAND\_MAX 上限改 64 位 LCG；eval/eval\_call 降级去桥；全量零 tie\_interp.lib 链接验证——path\_*、regex 运行期 pattern、alloc/free 三组残留桥记录。**残留桥已全清**：alloc/free 假 interp 标移除、path\_* 纯 tie 内联（tig\_path\_\*）、regex 运行期 pattern 改 std 纯 tie 引擎——综合程序零 tie\_interp 依赖）

**trm-lite 完善（p.6.5，复杂形态完整实现）**

- [x] p.6.5.1 复杂形态静态链接外壳：import trm-lite → tiec 静态链接复杂 runtime
  （落地 2026-09-02：独立命名空间 trm\_lite\_ws/trm\_lite\_tgc/tl\_runtime\_ctx 骨架 +
  协作 FIFO 函数值任务队列 + GC 登记占位；内置 spawn/yield/collect 混用检测扩展
  到复杂形态汇总库；ctx\_shell\_demo 验收 exit 0 + 负例 ctx\_mix\_neg 编译期报错）

- [x] p.6.5.2 work-stealing 调度器：多 OS 线程池 + 双端队列 + 任务窃取 + 抢占 + M:N 承托
  （落地 2026-09-02：sched\_ws 重写——每 worker 段式双端队列（P×段容量预分配，
  固定不重叠）+ 段尾 LIFO 自取 / 段头 FIFO 窃取 / 段满溢出全局队列；真 OS 线程池
  按轮创建/回收；CRITICAL\_SECTION + CONDITION\_VARIABLE 同步；终止协议
  pending/active 原子视图无最后-worker 竞态；ctx\_ws\_demo 验收：dist\_tid4=4（真实
  并行）、数值全对、子任务 16、溢出窃取 stolen>0、P=4 快于 P=1）

- [x] p.6.5.3 并发三色 GC：标记栈/写屏障 + 后台回收器 + 精确根扫描（无栈图降级保守根）
  （落地 2026-09-02：gc\_tri 重写——扁平托管对象图（对象/边/根表）+ 三色标记栈 +
  Dijkstra 写屏障（set\_ref 黑→白 置灰压栈）+ 根写屏障（cycle 中 add\_root 置灰）；
  后台回收器线程与 worker 真并发推进（bg\_step 轮次状态机）；sweep 仅无任务窗口
  执行；同步收集 gc\_collect\_sync 供断言；ctx\_gc\_demo 验收：liveA=16/freedA=8 精确、
  steps=16（后台推进）、sync\_freedB=0（写屏障交错零误回收）、exit 0）

- [x] p.6.5.4 分代 + 整理：新生代/老年代 + mark-compact（老年代）
  （落地 2026-09-02：gc\_tri 分代——年龄表 + 晋升阈值（存活 minor ≥2 → 老年代）；
  minor 只收 young（老年代预黑保护）+ 记忆集（写屏障老→新 + 晋升屏障）+ rs 持久
  累积；major = 全量三色 + mark-compact（存活重排前段 + 边/根重写 + remapped 查询）；
  **修复标记栈缺陷**（tie table 只追加，旧 g\_stack\[g\_sp-1] pop 重复取出旧根 → 改
  队式头游标，多点 gray 停滞问题根治）；gc\_gen\_demo 验收：晋升 10/10、rs 隔离存活、
  老垃圾免疫 minor、major 回收 21 + compact 60 重映射边正确）

- [x] p.6.5.5 可迁移栈：任务任意 worker 执行（无固定栈绑定）+ 迁移计数
  （落地 2026-09-02：tie 任务为 fn() 原子执行体——「可迁移栈」语义落位 = 任务与
  创建 worker 解耦（任意 worker 可执行）；spawn 登记 g\_orig\_w、执行时登记 g\_exec\_w；
  迁移计数 g\_migrated（worker≠创建者即迁移）；ctx\_migrated/ctx\_task\_exec\_w 观察量；
  mig\_demo 验收：24 任务分布 4 worker + migrated>0）

- [x] p.6.5.6 精确根拍板（设计 §9 待决项 3）：任务 env 即根
  （2026-09-02 定案：tie 闭包 env 为编译期静态捕获——精确根 = 任务闭包 env 引用根
  集合（add\_root + 写屏障维护），sweep 仅在无任务窗口执行；root\_protect\_demo：
  运行中（active>0）对象不回收、任务结束后收敛 0 无泄漏；拍板写入任务书 §5）

- [x] p.6.5.7 channel 语言原语：ch\_open/ch\_send/ch\_recv/ch\_close
  （落地 2026-09-02：core/chan/tl\_chan.tie 环形缓冲 mailbox（互斥 + 条件变量）；
  tiec 三处注册内置 + codegen 静态链接 trm\_lite\_chan$\* + import 冲突检测；chan\_demo
  验收：FIFO/空/关闭/满容量 PASS；自举字节一致）

- [x] p.6.5.8 actor × 复杂形态咬合：actor 消息经 trm-lite mailbox；#\[unsafe.trm]
  （落地 2026-09-02：actor\_task 经 per-actor channel ch\_recv 取 method\_id（record\@56
  存通道句柄）；发送方 ch\_send 入队 + spawn；单消息槽串行护栏保留（async FIFO 精确）；
  \#\[unsafe.trm] actor 级标注接受；actor\_trm\_demo：async 多参 FIFO total=96）

- [x] p.6.5.9 多执行体分配/回收 + 消息传收 demo（两形态验收载体）
  （落地 2026-09-02：combo\_demo 复杂——mailbox 8 消息取回 + 16 任务分配 96 槽/32 活/
  64 垃圾后台并发回收；combo\_simple\_demo 简单——actor mailbox + 内置 channel +
  spawn 闭包 + collect；均 exit 0 计数精确）

- [x] p.6.5.10 回归与对比验收：m6\_actor 零回归、简单 vs 复杂行为一致
  （落地 2026-09-02：m6\_actor 15 正向探针零回归 + 10 负例编译期拒绝；parity\_chan
  （内置 ch 求和 804）与 combo\_demo（ctx\_ch 求和 804）行为一致）

- [x] p.6.5.11 收尾：trm-lite preview\.2、README/CHANGELOG、已知限制清单
  （落地 2026-09-02：README 全景更新 + 已知限制清单；chan 构件 tl\_chan\_lib.tie
  独立切片并入 trm\_lite.a 构建约定；自举核验 tiec2 字节一致）

**库补全（p.6.6，一库一子项；前置 p.6.4 原语全面 tie 化完成后启动；设计见 docs/superpowers/specs/2026-09-01-p66-library-completion-design.md）**

- [x] p.6.6.1 ext/tls：TLS 1.3 + 1.2 客户端（纯 tie）、X.509 解析与完整链校验、字节级网络 IO（p.6.4.5 承接）

- [x] p.6.6.2 std/http 升级：完整 HTTP 客户端（https/POST/headers/cookies/重定向），命名空间 httpc，旧 http.get 保留兼容

- [x] p.6.6.3 std/sse：SSE 流式解码（event/data/id/retry；LLM/WebSocket/Web 框架前置件）

- [x] p.6.6.4 ext/html：HTML 分词 + DOM 树 + 选择器抽取 + 链接提取 + HTML→纯文本

- [x] p.6.6.5 ext/xml：XML 分词 + 解析（与 html 共用标记语言分词底座；供 svg/配置消费）

- [x] p.6.6.6 ext/spidey：爬虫治理（robots.txt + 限速 + URL 去重 + 编排，依赖 p.6.6.4）

- [x] p.6.6.7 std/ws：WebSocket 客户端（握手 + 帧编解码 + 掩码，依赖 p.6.6.2）

- [x] p.6.6.8 std/smtp：SMTP 发信（EHLO/AUTH/MAIL/RCPT/DATA，可配 STARTTLS，依赖 p.6.6.1）

- [x] p.6.6.9 std/dns：DNS 解析（A/AAAA/TXT/MX 查询，依赖 std/net UDP）

- [x] p.6.6.10 std/yaml：YAML 解析（块缩进/流式/标量类型 → 平行表）

- [x] p.6.6.11 ext/config：TOML 支持提升（表/数组表/内联表，与 INI/KV 统一入口）

- [x] p.6.6.12 std/markdown：markdown 解析（块级元素/行内标记 → 结构表）

- [x] p.6.6.13 ext/png：PNG 编解码（chunk 遍历 + 滤波 + 位深/色彩类型）

- [x] p.6.6.14 ext/qr：QR 码生成（RS 纠错 + 矩阵布局 + 版本/掩码）

- [x] p.6.6.15 ext/svg：SVG 解析（元素树 + 路径/形状结构，依赖 p.6.6.5）

- [x] p.6.6.16 std/tpl：模板引擎（`{{expr}}` 求值 + 渲染字符串/文件）

- [x] p.6.6.17 std/diff：文本 diff（LCS → 行级增删改 + 统一格式输出）

- [x] p.6.6.18 std/cron：cron 调度（5 字段表达式 → 下次触发时间/到期判断）

- [x] p.6.6.19 std/jwt：JWT（HS256/RS256 签发验证，供 p.6.6.21 会话）

- [x] p.6.6.20 std/sqlite：SQLite 驱动（C ABI 桥，参考 ext/ecdsa extern 范式）

- [x] p.6.6.21 Web 服务框架：std/http\_server 升级（路由表 / keep-alive / 静态文件 / SSE 推送 / JWT 会话）

- [x] p.6.6.22 LLM 调用库：OpenAI 兼容客户端（POST + JSON + SSE 流式，依赖 p.6.6.2/p.6.6.3）

- [x] p.6.6.23 sys/win32：平台专用层首期（命名空间 sys\_win32；注册表/系统信息/剪贴板/环境强化/用户目录/窗口消息 + 进程枚举/服务控制/网络接口/硬件信息）
  - 依赖方向（单向）：tls → httpc → sse；html → xml → svg；httpc → ws；tls → smtp/jwt；httpc+sse → llm

  - 平台层：sys/win32 之后 linux/mac 同名层（sys\_linux / sys\_mac）

  - 计划文档：docs/superpowers/plans/2026-09-01-p661-tls-client.md（p.6.6.1 实施计划）

**trm-lite 并行（p.6.7，双形态真并行 + 运行时全量并发安全；详细见 docs/superpowers/specs/2026-09-03-trm-lite-p67-parallel-design.md）**

| 子项           | 内容                                                                     | 验收                              |
| ------------ | ---------------------------------------------------------------------- | ------------------------------- |
| \[x] p.6.7.1 | 分配器与 SSO 池并发安全：进程级短串池加锁或 per-thread 池；长串走线程安全 CRT malloc；str\_cat 并发正确 | N 线程并发 str\_cat/字符串构建：逐字节正确、无越界 |
| \[x] p.6.7.2 | 共享表并发安全：tie\_table\_new/push/len 桥符号并发保护；realloc 扩表与并发写一致性             | 并发 push 计数精确、无老数据覆盖             |
| \[x] p.6.7.3 | 全局读写原子化：跨线程共享计数用 atomic/独立槽位；race 指南（安全/不安全模式文档化）                      | fetch\_add 并发求和探针 = N×M         |
| \[x] p.6.7.4 | 输出与运行时余项：println/to\_string 加锁；intern/静态池等余项审查并锁                       | 并发 println 行不撕裂                 |
| \[x] p.6.7.5 | 生命周期确定性：字符串/表分配改引用计数或 arena 回收（消除 str\_cat 泄漏），多线程下确定性释放               | 长跑并发探针内存有界                      |

| 子项           | 内容                                                                               | 验收                              |
| ------------ | -------------------------------------------------------------------------------- | ------------------------------- |
| \[x] p.6.7.6 | 简单形态常驻池（S-pool）：内置 spawn 投递到简单 runtime 自己的常驻线程池（与复杂形态物理隔离）；yield 重定义 = 同步点并兼容旧程序 | spawn\_demo 类程序真实多线程，tid 去重 ≥ 2 |
| \[x] p.6.7.7 | 简单形态窃取队列（S-deque）：per-worker 双端队列 + 窃取 + 溢出（复刻 sched\_ws 算法、独立实现）；协作让出点          | 不平衡负载 stolen>0、结果全对             |
| \[x] p.6.7.8 | 复杂形态常驻池（C-pool）：sched\_ws 去每轮 drain 重建；池起于首次 drain、止于 shutdown                   | 多轮 drain 复用同一组线程句柄              |
| \[x] p.6.7.9 | 复杂形态 per-P 细锁（C-deque）：每 worker 段独立锁 + 全局溢出队列细锁，去全局单 CS；窃取窗口缩小                   | ms4 < ms1 可复现（修复 78>47）         |

| 子项            | 内容                                                                | 验收             |
| ------------- | ----------------------------------------------------------------- | -------------- |
| \[x] p.6.7.10 | 协作抢占统一：yield/gosched 显式点 + 时间片计数器检查插桩；两形态统一抢占机制                   | 长任务可让出，调度公平性探针 |
| \[x] p.6.7.11 | 结构化并发 WaitGroup：spawn 分组句柄 + 等全部完成（Go sync.WaitGroup）；内置与 ctx 双入口 | wg 并发求和多组精确    |

| 子项            | 内容                                                  | 验收                                           |
| ------------- | --------------------------------------------------- | -------------------------------------------- |
| \[x] p.6.7.12 | channel Go 语义：tl\_chan 增加 close 广播唤醒、双向、select 多路收发 | select/close 广播探针 PASS；parity\_chan 对比仍逐字节一致 |

| 子项            | 内容                                            | 验收            |
| ------------- | --------------------------------------------- | ------------- |
| \[x] p.6.7.13 | 双形态并行验收矩阵：两形态各自真并行探针 + 行为一致对比 + m6\_actor 零回归 | 全 PASS、exit 0 |
| \[x] p.6.7.14 | 收尾：preview\.6、README/CHANGELOG、已知限制清单、双语文档    | 自举核验 + 零回归    |

**Skia 图形（p.6.8，全栈图形：精简自建子集 + unsafe 直绑；详细见 docs/superpowers/specs/2026-09-03-tie-p68-skia-design.md）**

| 子项           | 内容                                                                                    | 验收                                           |
| ------------ | ------------------------------------------------------------------------------------- | -------------------------------------------- |
| \[x] p.6.8.1 | `ptr` 指针类型：T2 类型化指针 + addr\_of/deref/指针算术 + U3 语法（unsafe 块/函数，文件级逃生舱）；安全代码触碰指针 = 编译错误 | 指针探针（取址/解引用/算术/比较）PASS；unsafe 边界外使用 ptr 编译拒绝 |
| \[x] p.6.8.2 | `repr(C)` 结构体：R1 显式 ABI 布局（字段偏移精确对齐，对照 C 编译输出）；可整体按引用传 extern；与窄整数模型咬合                | repr(C) 布局探针对照 C 的 offsetof 全等；按引用传结构体 PASS  |
| \[x] p.6.8.3 | extern 扩展：E3 extern 强制 unsafe + ptr 参数/返回值 + 结构体按引用 + string↔char\*                   | 双向 ptr 探针；extern\_move\_check 零回归            |

| 子项           | 内容                                                                                                                                                                               | 验收                                   |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| \[x] p.6.8.4 | 源码裁剪与构建：收窄到 SkSurface/SkCanvas/SkPaint/SkPath/SkTextBlob/SkFont/SkImage/SkCodec(PNG/BMP) + Raster 软件光栅 + 离屏位图 Surface；构建脚本 tie 写（GN/ninja 或最小 CMake 裁剪，脚本逻辑全 tie）；产物静态库（.a/.lib） | 最小 C++ 冒烟：画矩形/文本/图像到离屏位图 → 导出 PNG 成功 |
| \[ ] p.6.8.5 | 模块清单与依赖收窄：源文件/编译宏/第三方依赖清单（zlib 等收窄或系统库）；裁剪后体积基线记录                                                                                                                                | 清单文档化；构建可复现（同一 commit 同一产物字节）        |

| 子项           | 内容                                                                                                             | 验收                                   |
| ------------ | -------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| \[ ] p.6.8.6 | extern "C" thunk：Skia 类方法 → C 入口（最小手写 + tie 写生成器脚本）；对象 = 不透明 ptr；SkPaint/SkImageInfo 等映射 repr(C) 结构            | thunk 冒烟：tie 程序经 extern 画线到离屏表面并导出校验 |
| \[ ] p.6.8.7 | trm.ui.gfx 句柄层：repr(C) 句柄 struct（SkCanvas/SkPaint/SkPath/...）+ 方法绑定（obj.method() 转发）+ 生命周期（显式 release / arena） | 句柄探针（创建/使用/释放）；move 语义零回归            |
| \[ ] p.6.8.8 | 命令列表翻译器：D2 Paint Commands → Skia 调用（rect/text/path/image）+ font\_measure 文本度量桥                                 | 命令列表离屏渲染逐像素/哈希校验一致                   |

| 子项            | 内容                                                                             | 验收                            |
| ------------- | ------------------------------------------------------------------------------ | ----------------------------- |
| \[ ] p.6.8.9  | 窗口嵌入层（Win32 起步）：CreateWindow + 消息泵 + 后备缓冲 Surface（离屏位图）+ 呈现（blit 上屏）           | 窗口显示 + 后备缓冲绘制正确               |
| \[ ] p.6.8.10 | 事件系统 E3：事件队列（鼠标/键盘，含位置/键码/时间戳）+ 信号标志（WM\_PAINT→重绘、WM\_TIMER→定时）                | 事件驱动探针（移动/点击/按键 → 队列）         |
| \[ ] p.6.8.11 | 主循环与呈现：主循环整合 + 脏矩形重绘 + 帧节流/vsync；trm.ui port 抽象面接线（Window/Painter/EventSource） | 帧率/脏矩形正确；port 双实现（Skia/离屏）可切换 |
| \[ ] p.6.8.12 | 全栈演示：窗口 + 命令列表绘制（矩形/文本/路径/图像）+ 事件响应 + 组合式布局雏形（row/column 嵌套）                   | 演示程序运行交互正常                    |

| 子项            | 内容                                                                 | 验收                 |
| ------------- | ------------------------------------------------------------------ | ------------------ |
| \[ ] p.6.8.13 | 验收矩阵：无窗口离屏渲染探针（CI 可跑，逐像素/哈希）+ 窗口演示 + 自举/回归 + 软件光栅性能基线（vs GDI）      | 全 PASS、exit 0、基线记录 |
| \[ ] p.6.8.14 | 收尾：preview\.6、README/CHANGELOG、已知限制清单（GPU/X11/SkParagraph 后置）、双语文档 | 自举核验 + 零回归         |

**LSP 重写（p.6.9，tsp 落地：0-Rust 收官；详细见 docs/superpowers/specs/2026-09-03-tie-p69-lsp-rewrite-design.md）**

| 子项           | 内容                                                                                                                               | 验收                                                 |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| \[ ] p.6.9.1 | `std/stdio` 字节原语：stdin/stdout 字节级 read/write + read\_line + 缓冲；与 std/fs 对称；LSP 与 tink 桥共用                                        | 回显探针（stdin 字节 → stdout 字节逐字节一致）；read\_line 探针      |
| \[ ] p.6.9.2 | protocol.tie：JSON-RPC over stdio（Content-Length 帧 + 编解码，复用 std/json）；消息类型 Initialize/Initialized/Shutdown/Exit + textDocument/\* | 与 vscode-languageclient 握手（initialize 往返）；py 客户端回环 |

| 子项           | 内容                                                                          | 验收                      |
| ------------ | --------------------------------------------------------------------------- | ----------------------- |
| \[ ] p.6.9.3 | analyze.tie：文档 → 编译流水线（lex/parse/semantic）→ AST + 符号 + 诊断；单文件错误隔离（坏文档不崩服务）  | 错误文档返回诊断不崩溃；正常文档符号齐备    |
| \[ ] p.6.9.4 | index.tie：复用 ir\_meta sym\_table + import 图（正/反向）；工作区按需加载（打开文件 + import 可达） | 跨文件符号索引正确；import 变更级联正确 |
| \[ ] p.6.9.5 | diagnostics.tie：semantic 错误 → LSP 诊断（range 映射）+ 增量（文件级缓存，import 变更才级联）      | 增量编辑诊断正确；缓存命中无重复分析      |

| 子项           | 内容                                                                 | 验收                        |
| ------------ | ------------------------------------------------------------------ | ------------------------- |
| \[ ] p.6.9.6 | completion.tie + hover.tie：符号表补全（关键字/符号/参数/泛型实参）+ 文档注释 hover       | 补全/hover 探针（含 "." 触发）PASS |
| \[ ] p.6.9.7 | definition.tie + reference.tie：跳转定义（跨文件，import 图）+ 引用查找（反向索引）      | 跨文件跳转/引用探针 PASS           |
| \[ ] p.6.9.8 | signature.tie + symbol.tie：签名帮助（参数提示，复用签名元数据）+ 文档/工作区符号（大纲，复用 AST） | 签名/大纲探针 PASS              |

| 子项            | 内容                                                                                                        | 验收               |
| ------------- | --------------------------------------------------------------------------------------------------------- | ---------------- |
| \[ ] p.6.9.9  | semantic\_tokens.tie + folding.tie：语义令牌（映射 VSCode 标准类型 keyword/type/variable/function/...）+ 折叠范围（AST 块结构） | 语义令牌/折叠探针 PASS   |
| \[ ] p.6.9.10 | rename.tie + documentHighlight + quickfix：跨文件重命名（import 图）+ 符号出现高亮 + 修复建议（缺分号/未定义变量）                      | 重命名/高亮/修复探针 PASS |
| \[ ] p.6.9.11 | format.tie：格式化（对齐 prep/indent 转换器思路）                                                                      | 格式化前后一致探针 PASS   |

| 子项            | 内容                                                                                           | 验收                            |
| ------------- | -------------------------------------------------------------------------------------------- | ----------------------------- |
| \[ ] p.6.9.12 | server.tie：服务端主循环（stdio 循环 + 请求分发 + 增量缓存补偿）+ 生命周期（initialize/shutdown/exit）；`tie --lsp` 入口保留 | initialize/shutdown 往返；错误请求不崩 |
| \[ ] p.6.9.13 | VSCode 客户端接线：现有 TS 客户端（vscode-languageclient）指向 tsp；16 项能力矩阵联调                               | 编辑器实测：诊断/补全/跳转/引用/重命名/语义高亮全通  |
| \[ ] p.6.9.14 | 验收与发布：大项目（编译器自身 8 模块）编辑流畅 + 16 能力矩阵 + 零回归 + preview\.6 收尾（README/CHANGELOG/双语文档/已知限制）        | 全 PASS、exit 0、编辑不卡顿           |

**内存治理（p.6.10，库层去分配 + 运行时自动回收；tsha1 基准内存爆炸 RCA 后立项）**

| 子项            | 内容                                                                                                                                      | 验收                                       |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| \[x] p.6.10.1 | tsha1 通用 compress 去每块表分配：lanes/Pw 提升为 digest 级 scratch 复用（absorb 加 W 参数、fin\_synth 复用 lanes/Pw 作 zrc、compress48 透传）                     | 四模型 KAT 探针逐字一致（n=144 通用路径覆盖）；基准不再无界涨     |
| \[x] p.6.10.2 | trm-lite 表内存自动回收 / 编译器插桩：tl\_tbl 引用计数 API（tbl\_retain/tbl\_release + 空句柄守卫）+ irgen 表赋值 retain/release 配对 + 表变量零初始化兜底；自举新不动点收敛（rc2==rc3） | 表赋值插桩探针 PASS；config\_smoke 48/48；语言探针零回归 |
| \[x] p.6.10.3 | 作用域出口析构（entry 级局部表 release）+ 返回表 retain 接管 + VarDecl 表引用 retain + RHS 新构造免 retain + 参数目标不 release（循环/分支内 var 与嵌套表留 p.6.10.4） | 生命周期探针 PASS；2000 万次临时表循环峰值 3MB（内存有界）；自举 rc2==rc3 |
| \[x] p.6.10.4 | 表元素/嵌套表 retain（push/下标写表值）与循环内/分支内 var 遮蔽回收（零值全局哨兵 + select 归零首轮）\| 嵌套表长跑探针 PASS + 2000 万次临时表循环峰值 4.2MB（内存有界）；自举 rc2==rc3 |

