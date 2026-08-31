# 规划：LLVM 工具链升级（18.1.8 → 22.1.8）
*EN: Plan: LLVM Toolchain Upgrade (18.1.8 → 22.1.8)*

> 状态：**已实现**（2026-08-15，S1.1 完成；commit 见 git log）
> EN: Status: **Implemented** (2026-08-15, S1.1 complete; see git log for the commit)
> 本文档定义 tie 的 LLVM 工具链升级计划：**18.1.8 → 22.1.8**。
> EN: This document defines the tie LLVM toolchain upgrade plan: **18.1.8 → 22.1.8**.
> 结论：**升级到 22.1.8（最新稳定版），成本低收益明确；23 等稳定后再议。**
> EN: Conclusion: **upgrade to 22.1.8 (latest stable), low cost and clear benefit; revisit 23 only after it stabilizes.**
> 关联：toolchain.tie（opt/clang/llvm-ar/lld 驱动）、vendored LLVM（bin/llvm/）、
> EN: Related: toolchain.tie (drives opt/clang/llvm-ar/lld), vendored LLVM (bin/llvm/),
> wasm 后端规划（webui）、hw-accel.md（编译器性能）。
> EN: wasm backend plan (webui), hw-accel.md (compiler performance).

## 1. 版本现状
*EN: 1. Current Version Status*

| 版本 | 发布 | 状态 |
| --- | --- | --- |
| **18.1.8** | tie 当前使用 | 基线 |
| 19.1.0 | 2024-09 | 过时 |
| 20.1.0 | 2025-03 | 过时 |
| 21.1.0 | 2025-08 | 过时 |
| **22.1.8** | 2026-06 | **最新稳定版（GitHub Latest）** |
| 23.1.0 | RC3（2026-08-12） | 未稳定，勿生产用 |

EN: Version table: 18.1.8 is the current baseline; 22.1.8 is the latest stable release; 23.1.0 is still at RC3 and not for production.

## 2. tie 的 LLVM 依赖面（升级成本评估的关键）
*EN: 2. tie's LLVM Dependency Surface (Key to the Upgrade-Cost Assessment)*

**依赖面极薄**——tie 只通过 6 个工具函数消费 LLVM，**全走命令行文本接口**：
EN: **The dependency surface is extremely thin** — tie consumes LLVM only through 6 tool functions, **entirely via command-line text interfaces**:

| 工具函数 | 调用 | 说明 |
| --- | --- | --- |
| find_tool | TIE_LLVM_HOME/PATH/固定目录 | 工具发现 |
| opt | `opt -O{0..3} -S in.ll -o out.opt.ll` | 中间优化（文本 IR 进出） |
| clang | `clang in.opt.ll -o out.exe [--target]` | 链接可执行文件 |
| llvm-ar | `llvm-ar rcs out.a out.o` | 静态库归档 |
| link_exe / compile_object / archive | 组合上述 | 链接/编译/归档 |

EN: The table lists the six tool functions and how each invokes an external LLVM binary purely over the CLI (find_tool, opt, clang, llvm-ar, and the three composites).

**关键事实**：不依赖 LLVM C++ API/库——只有命令行文本接口。
EN: **Key fact**: tie does not depend on the LLVM C++ API/libraries — only on the command-line text interface.
这是升级风险最低的形态：命令行接口稳定，升级 = IR 语法适配 + 回归测试。
EN: This is the lowest-risk upgrade shape: the CLI is stable, so upgrading = IR-syntax adaptation + regression testing.

## 3. 各版本核心变化（对 tie 的影响面）
*EN: 3. Core Changes Per Version (Impact Surface on tie)*

### 3.1 IR/语法破坏性变更（tie 生成文本 IR，需关注）
*EN: 3.1 Breaking IR/Syntax Changes (tie emits text IR, so must be watched)*

| 版本 | 变更 | tie 影响 |
| --- | --- | --- |
| 19 | 常量表达式 icmp/fcmp/shl 移除；debug intrinsics→records；intrinsic 改名 | 低（tie 不生成这些） |
| 20 | 递归类型禁止；x86_mmx 移除；NVVM intrinsics 移除 | 低（tie 不用） |
| 21 | 常量表达式 mul 移除；nocapture→captures(none)；inline asm label 参数移除 | 低 |
| **22** | **SwitchInst case 值不再作 operand**；ptrtoaddr；masked intrinsic 对齐参数变更 | **需验证**（见 §5） |
| 23(预览) | convert intrinsics 移除、denormal attrs 替换、BranchInst 拆分、wasm ref 类型重做 | 大——等稳定 |

EN: The table lists breaking IR/syntax changes per version and their impact on tie; 18→21 are rated low (tie does not emit those constructs), while 22 needs verification and 23 is large enough to wait for stability.

### 3.2 opt pass（tie 零影响）
*EN: 3.2 opt Passes (Zero Impact on tie)*

- 无 `-O0..-O3` 改名；新增 IRNormalizer(20)/AllocToken(22) 等
  EN: No `-O0..-O3` renames; additions like IRNormalizer(20)/AllocToken(22).
- tie 只用 `opt -O{0..3} -S`，零自定义 pass——**不受影响**
  EN: tie only uses `opt -O{0..3} -S` with zero custom passes — **unaffected**.

### 3.3 clang 默认行为
*EN: 3.3 clang Default Behavior*

| 版本 | 变更 | tie 影响 |
| --- | --- | --- |
| 19 | triple 归一化；GCC_INSTALL_PREFIX 报错 | 低（tie 主要 Windows msvc） |
| 20 | pointer-TBAA/pointer overflow 默认 | 低（影响优化语义，需回归） |
| 22 | MSVC ABI 变更 | **Windows 相关，需回归验证** |

EN: clang default-behavior changes by version; the MSVC ABI change in 22 is Windows-relevant and needs regression verification.

### 3.4 lld
*EN: 3.4 lld*

| 版本 | 变更 | tie 影响 |
| --- | --- | --- |
| 21 | 可读可执行段默认合并 | 低 |
| **22** | **Wasm --stack-first 默认；wasm32-wasi→wasm32-wasip1** | wasm 目标启用时需适配 |

EN: lld changes: 21 is low impact; 22 changes wasm defaults and renames the wasm32-wasi triple, requiring adaptation when the wasm target is enabled.

### 3.5 wasm（tie 未来 webui 后端）
*EN: 3.5 wasm (tie's Future webui Backend)*

- 19/21：无变化；20：bulk-memory/nontrapping/Lime1/EH 支持
  EN: 19/21: no change; 20: bulk-memory/nontrapping/Lime1/EH support.
- **22**：half soft-float；wasi 改名——wasm 支持成熟
  EN: **22**: half soft-float; wasi rename — wasm support matures.
- 23(预览)：wasm ref 类型表示法大改（target ext）——**升级 22 正好避开**
  EN: 23 (preview): major redesign of wasm ref-type representation (target ext) — **upgrading to 22 neatly sidesteps this**.

## 4. 升级决策
*EN: 4. Upgrade Decision*

### 4.1 升级到 22.1.8（推荐）
*EN: 4.1 Upgrade to 22.1.8 (Recommended)*

1. **依赖面薄**：命令行接口 + 文本 IR，升级风险最低
   EN: **Thin dependency surface**: CLI + text IR, so upgrade risk is the lowest.
2. **稳定**：22.1.8 发布 2 个月 + 8 个补丁；23 还在 RC3
   EN: **Stable**: 22.1.8 has been released 2 months with 8 patches; 23 is still at RC3.
3. **wasm 红利**：22 的 wasm 支持成熟；23 的 ref 类型大改会破坏——现在上车 22 正好
   EN: **wasm dividend**: 22's wasm support is mature; 23's ref-type overhaul would break things — boarding 22 now is timely.
4. **性能与安全**：4 个版本的优化器改进 + 安全补丁
   EN: **Performance & security**: four versions of optimizer improvements plus security patches.

### 4.2 不升级 23（等稳定）
*EN: 4.2 Do Not Upgrade to 23 (Wait for Stability)*

- 23 的 IR 破坏性变更明显更多（BranchInst 拆分、wasm ref 类型重做、convert intrinsics 移除）
  EN: 23 has significantly more breaking IR changes (BranchInst split, wasm ref-type redo, convert-intrinsics removal).
- 等 23.1 稳定 + tie 升级 22 验证后再评估
  EN: Re-evaluate only after 23.1 stabilizes and tie has validated on 22.

## 5. 升级步骤
*EN: 5. Upgrade Steps*

### 5.1 前置验证（回归重点）
*EN: 5.1 Pre-Verification (Regression Focus)*

- [ ] 跑 compiler/tests（词法/语法/语义回归）
  EN: [ ] Run compiler/tests (lexer/parser/semantic regression).
- [ ] 跑行为等价回归（_driver_test，与 Rust 参考对比）
  EN: [ ] Run behavioral-equivalence regression (_driver_test, compared against the Rust reference).
- [ ] **重点：IR 语法错误**（opt/clang 解析 22 的文本 IR）
  EN: [ ] **Focus: IR syntax errors** (opt/clang parsing 22's text IR).
- [ ] **SwitchInst 验证**：tie 当前用线性比较链生成 switch（非 LLVM switch 指令），
      22 的 SwitchInst operand 变更大概率无影响——实测确认
  EN: [ ] **SwitchInst verification**: tie currently generates switch via a linear comparison chain (not an LLVM switch instruction), so 22's SwitchInst operand change likely has no impact — confirm by test.
- [ ] clang 22 MSVC ABI 回归（Windows 链接行为）
  EN: [ ] clang 22 MSVC ABI regression (Windows linking behavior).
- [ ] opt -O2 优化结果对比（数值/输出一致性）
  EN: [ ] Compare opt -O2 optimization results (numerical/output consistency).

### 5.2 升级操作
*EN: 5.2 Upgrade Operation*

1. 替换 vendored LLVM 二进制（bin/llvm/ → 22.1.8）
   EN: Replace the vendored LLVM binaries (bin/llvm/ → 22.1.8).
2. 若 TIE_LLVM_HOME 指向外部安装：更新到 22.1.8
   EN: If TIE_LLVM_HOME points to an external install: update it to 22.1.8.
3. 回归测试全绿后提交
   EN: Commit after all regression tests pass.
4. 更新 README 中的 LLVM 版本说明
   EN: Update the LLVM version note in the README.

### 5.2a 实现记录（2026-08-15，S1.1 完成）
*EN: 5.2a Implementation Record (2026-08-15, S1.1 Complete)*

- **二进制**：官方 GitHub releases `LLVM-22.1.8-win64.exe`（安装器需管理员）/
  `clang+llvm-22.1.8-x86_64-pc-windows-msvc.tar.xz`（归档包，解压即用，本机采用）
  EN: **Binaries**: official GitHub releases `LLVM-22.1.8-win64.exe` (installer requires admin) / `clang+llvm-22.1.8-x86_64-pc-windows-msvc.tar.xz` (archive, extract-and-use; this machine uses it).
- **本机切换**：D:\LLVM 升级为 22.1.8；18.1.8 备份至 D:\LLVM18（便于回退）；
  PATH/TIE_LLVM_HOME 均无需改（路径不变）
  EN: **Local switch**: D:\LLVM upgraded to 22.1.8; 18.1.8 backed up to D:\LLVM18 (for easy rollback); neither PATH nor TIE_LLVM_HOME needs changing (paths unchanged).
- **关键适配**：clang 22 起 Windows 默认链接器从 link.exe 改为 lld-link（实测 -v 确认），
  lld-link 解析 Rust staticlib（tie_interp.lib）CRT 符号缺陷（printf undefined）导致
  interp 桥程序链接失败 → `compiler/backend/toolchain.tie` `link_exe` 非 vendored 场景
  显式 `-fuse-ld=link`；vendored（TIE_LLVM_HOME）场景保持 `-fuse-ld=lld`
  EN: **Key adaptation**: from clang 22 the Windows default linker changes from link.exe to lld-link (confirmed via `-v`); lld-link's flawed resolution of Rust staticlib (`tie_interp.lib`) CRT symbols (printf undefined) broke the interp-bridge program link → in `compiler/backend/toolchain.tie` `link_exe`, the non-vendored case explicitly uses `-fuse-ld=link`; the vendored (TIE_LLVM_HOME) case keeps `-fuse-ld=lld`.
- **回归结果**：interp 11/11 + _driver_test PASS + tests/language 24 PASS（零新增失败）+
  自举闭环 tiec2==tiec3 sha 一致 + G4 闸门 PASS（ratio 1.458）+ vendored hello/库编译链正常
  EN: **Regression results**: interp 11/11 + _driver_test PASS + tests/language 24 PASS (no new failures) + bootstrap closed-loop tiec2==tiec3 with matching sha + G4 gate PASS (ratio 1.458) + vendored hello/library compile chain working.
- **SwitchInst**：tie switch 走 icmp 比较链（非 LLVM switch 指令）——22 变更零影响（实测确认）
  EN: **SwitchInst**: tie switch uses an icmp comparison chain (not an LLVM switch instruction) — 22's change has zero impact (confirmed by test).

### 5.3 wasm 目标适配（webui 启用时）
*EN: 5.3 wasm Target Adaptation (When webui Is Enabled)*

- 三元组：`wasm32-wasi` → **`wasm32-wasip1`**（22 改名）
  EN: Triple: `wasm32-wasi` → **`wasm32-wasip1`** (22's rename).
- lld：关注 `--stack-first` 默认值变化
  EN: lld: watch the `--stack-first` default-value change.
- 与 hw-accel/包模型（wasm 分发）衔接
  EN: Coordinate with hw-accel / the package model (wasm distribution).

## 6. 决策记录
*EN: 6. Decision Record*

| 决策点 | 结论 | 理由 |
| --- | --- | --- |
| 是否升级 | **升级到 22.1.8** | 依赖面薄 + 稳定 + wasm 红利 |
| 升级目标 | 22.1.8（最新稳定） | 23 未稳定（RC3） |
| 23 评估 | 等 23.1 稳定后再议 | IR 破坏性变更多 |
| 回归重点 | IR 语法 / SwitchInst / MSVC ABI | 22 的主要破坏点 |

EN: Decisions: upgrade to 22.1.8; do not target 23 until it stabilizes; regression focus is IR syntax / SwitchInst / MSVC ABI.

## 7. 未决问题
*EN: 7. Open Questions*

1. **vendored 分发**：22.1.8 二进制从哪里获取（LLVM 官方预编译 vs 自编译——
   tie 发行版随包分发的形态，参考 tie-llvm-vendored-dist 先例）
   EN: **Vendored distribution**: where to obtain the 22.1.8 binaries (LLVM official prebuilt vs self-built — the form tie ships in its distribution; reference the tie-llvm-vendored-dist precedent).
2. **升级时机**：与里程碑的关系（M0 unsafe 扩展前还是后——建议独立小里程碑
   先做，隔离风险）
   EN: **Upgrade timing**: its relation to milestones (before or after the M0 unsafe extension — a standalone small milestone is recommended first to isolate risk).
3. **行为等价基准**：升级后 G4 基准（ratio 1.09）是否重跑验证性能
   EN: **Behavioral-equivalence baseline**: whether to re-run the G4 baseline (ratio 1.09) after upgrading to verify performance.