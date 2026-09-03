# trm-lite 设计——Go 式静态内置 runtime（简单原语 + 复杂 runtime 分级）

- **日期**：2026-08-26
- **状态**：设计定稿（待 review 后进入实现规划）
- **范围**：为 tie 引入 **Go 式静态内置 runtime** 形态；分两小级——简单 M:N/GC 作 **tiec 内置原语**（供 actor/常规），复杂 M:N/GC 作 **trm-lite runtime 库**（`import` 静态链接进单一二进制）。**与 trm（路线 B，字节码 VM）并行开发、互不干扰。**
- **依据**：`docs/language-comparison.md`（Go 缺口）、`docs/designs/concurrency-model.md`（actor §7.1 C 组接入运行时的语法门）、`docs/designs/trm-final-design.md`（trm 定稿，本设计为其静态形态的旁支、非取代）。

## 1. 背景与现状

tie 现有两条运行路径：

| 路径 | 形态 | 运行时 | 依据 |
| --- | --- | --- | --- |
| 路线 A（现状默认） | `tiec ─▶ LLVM ─▶ 原生可执行` | 无 GC，表作用域确定性释放，零依赖 | 语言核心 |
| 路线 B（trm，定稿） | `tiec ─▶ tieir ─▶ trm 引擎（interp + ORC JIT）` | 引擎级 GC + 可迁移栈 M:N，对标 JVM | trm-final-design |

`concurrency-model.md` 把 actor 定为原生语法 + 纯编译（路线 A，1:1 OS 线程 + mailbox 就地 codegen），并预留接入运行时的语法门 `#[unsafe.trm]`（C 组）。其实现顺序 A→B→C，C 依赖 trm 引擎。

本设计回答一个此前只探方向、未定形态的问题：**海量 M:N 并发与 GC 以 Go 式静态内置形态落到 tie**，而非依赖字节码 VM。

## 2. 定位与总体思路

一句话：**trm-lite = 给 tie 补上「goroutine 式语言级执行体 + 静态内置运行时库」这一级，对标 Go 把调度器/GC 以库形式焊进单一零依赖二进制。**

借鉴 Go 的分层（goroutine 是语言级、调度器是 runtime 库），tie 拆成两小级：

| 层级 | 归属 | 对标 Go | 形态 | 触发方式 |
| --- | --- | --- | --- | --- |
| 简单 M:N + GC | **tiec 内置原语**（语言级） | goroutine / channel | 轻量执行体 `spawn`/`yield` + 简单 stop-the-world mark-sweep GC + mailbox | 原生语法，零配置 |
| 复杂 M:N + GC | **trm-lite**（runtime 库） | 完整 Go runtime | work-stealing 调度 + 并发三色 GC + 可迁移栈 | `import trm-lite` → 静态链接 |
| 既有 trm（路线 B） | 字节码 VM | JVM | interp + JIT | 保持并行，不碰 |

**边界线（分级依据，非模糊区）**：

| 维度 | 简单（内置原语） | 复杂（trm-lite） |
| --- | --- | --- |
| 回收 | stop-the-world mark-sweep | 并发三色标记 + 分代/整理 |
| 调度 | 协作式 1:1/N 基础 | work-stealing、抢占、可迁移栈 |
| 栈 | 普通栈（不迁移） | 可迁移/GC 管栈 |
| 适用 | actor 消息处理、常规并发 | 海量/长时间并发、强实时 |

**同源原则**：两小级共用同一套 tie 源码语义，走「import 即选择」——与 trm 路线 A/B、actor 纯编译的既有哲学一致。

**并行边界（硬约束）**：本设计不修改 trm 定稿路线 B，不 gate 于任何 trm 引擎能力；trm-lite 独立成路径、独立里程碑、独立验收，二者互不 block。

## 3. 架构分层

```
tie 应用层
│
L4  业务并发模式（actor / worker pool）          ← spawn/yield 承托；actor 消息即 mailbox
L3  语言级原语（轻量执行体、channel mailbox）      ← tiec 内置，纯编译 codegen
L2  runtime 接口（import trm-lite 触发）          ← 「import 即选择」静态链接开关
L1  执行层（调度器 + GC + 栈管理）                ← 简单=tiec codegen；复杂=trm-lite 库
│
实施两个执行体：
  简单形态 ──▶ tiec 就地 codegen（stop-the-world GC + 协作调度 + mailbox）→ 原生
  复杂形态 ──▶ import trm-lite ──▶ 静态链接（work-stealing + 并发 GC + 可迁移栈）→ 单一二进制
```

**依赖方向（硬约束）**：应用 → 库 → runtime 接口 → 执行层。执行层不依赖库层；语言级原语（简单形态）不依赖 trm-lite 库，trm-lite 库不依赖 trm 引擎。

## 4. 组件设计

### 4.1 简单形态——tiec 内置原语（语言级，纯编译）

| 组件 | 职责 | 实现归属 |
| --- | --- | --- |
| `spawn(…执行体…)` | 创建轻量执行体（对标 goroutine） | tiec codegen（OS 原语：线程 + 队列） |
| `yield` | 协作式让出 | tiec codegen（调度让步） |
| channel / mailbox | 消息传递，消除数据竞争 | tiec codegen（互斥 + 条件变量 + 队列） |
| 简单 GC | stop-the-world mark-sweep，管堆对象 | tiec 植入 + 回收器代码生成 |

- 仅限可确定根扫描的子集；栈普通、不迁移。
- **默认承载 actor**：actor 消息处理**默认**由简单执行体承载（替换当前 1:1 线程默认），不强制显式声明。
- 零配置：不 import，不上 trm，纯编译零依赖，产物与路线 A 同级。

### 4.2 复杂形态——trm-lite runtime 库（`import trm-lite`）

| 组件 | 职责 |
| --- | --- |
| 调度器 | work-stealing 任务窃取 + 抢占 + M:N 承托轻量执行体 |
| GC | 并发三色标记 + 分代/整理 + 精确根扫描（可迁移栈是根来源）。对标 Go 三色回收 |
| 栈管理 | 可迁移栈，GC 与调度共同承载 |
| 静态链接外壳 | `import trm-lite` 时 tiec 将之作为库静态链接进单一二进制，产出零依赖可执行 |

- 复杂形态以库形式存在，靠链接进产物（对标 Go 的 runtime 静态内置），**非**外部独立进程，也**非**字节码 VM。

## 5. 数据流（首个里程碑验证闭环）

```
spawn(A)；spawn(B)         原生原语或 import trm-lite 触发
   │
   ▼
A/B 分配对象 → 简单: stop-the-world 回收器扫根/标记/清扫
              │          复杂: 并发三色标记，后台回收器推进
              ▼
A→B 经 channel/mailbox 传消息（无共享可变，消除竞争）
   │
   ▼
全部执行体结束 → 回收 → main 返回 → 单一二进制退出，exit 0
```

## 6. 错误处理

| 情形 | 处理 |
| --- | --- |
| `spawn` 执行体运行期 `panic` | 由宿主（actor/调用方）按既有失败传播规则处理（答失败 + 调用方 raise） |
| GC 根扫描无法确定（复杂精确扫描） | 需语言栈图；该能力不足时降级 stop-the-world / 保守根，里程碑语义明示 |
| `import trm-lite` 但不满足复杂形态前提（如无精确栈图） | 编译期报错，指明需先具备前提 |
| 多执行体交错资源边界 | 语言层消除（actor 串行消费）+ 调度的 M:N 上界约束 |

## 7. 测试

- **probe/单测**：`spawn`/`yield` 行为；简单 GC 分配→回收无泄漏/无双重释放；channel 消息顺序。
- **回归**：既有 actor 纯编译路径（m6_actor）零回归；路线 A/B 不受影响。
- **regress 脚本**：参照 `trm/impl/impl-win32/regress-platform.ps1` 风格，跑通含多协程分配/回收 + 消息传收的 demo，断言 exit 0 与内存平衡。
- **对比验收**：同一程序的简单形态（tiec 原语）与复杂形态（import trm-lite）行为一致（输出/退出码）。

## 8. 首个里程碑范围（唯一定稿）

只做「简单 + 复杂一起」的验证闭环：

1. tiec 内置原语：`spawn`/`yield` + 简单 stop-the-world mark-sweep GC + channel mailbox，actor 可选用。
2. trm-lite 骨架：静态链接外壳跑通——`import trm-lite` 时 tiec 将复杂 runtime（work-stealing 调度 + 并发三色 GC 的**最小可靠子集** + 可迁移栈）静态链接进单一二进制。
3. 一个同时含多执行体分配/回收 + 消息传收的 demo，作为两形态的验收载体。

**非目标（不在本里程碑）**：反射、热更、动态加载、跨平台完整矩阵、与 trm 路线 B 抢占能力对齐。

## 9. 相关文档与待决

- 相关：`docs/designs/concurrency-model.md`（actor、C 组接入门）、`docs/designs/trm-final-design.md`（trm 定稿）、`docs/language-comparison.md`（Go 缺口）。
- 与 trm 关系：**并行开发、互不干扰**；本设计上文不 gate 于 trm 引擎，trm 亦不被本设计牵制。落地位置遵循独立路径原则，与 trm-final-design 正交。
- **已定（2026-08-26）**：
  1. actor **以「简单执行体默认承载」替换当前 1:1 线程默认**（见 §4.1）。
  4. trm-lite 物理落地为**独立仓库**；当前 GitHub 不可达，**先在本地创建仓库**（推送后置）。
- 待决（后续再定）：
  2. 复杂形态的最小可靠 GC 子集边界（先并发标记，分代/整理后置）。
  3. 精确栈图（复杂精确根扫描前提）的落地归属与顺序。