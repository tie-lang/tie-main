# tie 全平台插件化——实施计划（设计：docs/superpowers/specs/2026-08-29-plugin-kernel-design.md）
*EN: tie All-Platform Plugin Architecture — Implementation Plan (Design: docs/superpowers/specs/2026-08-29-plugin-kernel-design.md)*

> 状态：**S1 待实施**（2026-08-29 设计已定稿并提交 98d9db9）
> EN: Status: **S1 pending implementation** (design finalized 2026-08-29 and committed as 98d9db9)
> 纪律：每个小任务独立验证（一/二阶自举 + regress-s21 零回归 + 提交一次）
> EN: Discipline: each small task is independently verified (first/second-order bootstrap + regress-s21 zero regression + a single commit)
> 回退：任何一步违反"自举 hash 不变/回归基线"，立即停下回查，不贸然前进
> EN: Rollback: if any step violates "unchanged bootstrap hash / regression baseline", stop immediately to investigate rather than forge ahead
> 位置：tie-main（junction 于工作树 feat-tiec-modular-QhKVeM）
> EN: Location: tie-main (junctioned at worktree feat-tiec-modular-QhKVeM)

---

## 0. 验收基线（每步复用）
*EN: 0. Acceptance Baseline (Reused at Every Step)*

- 一阶自举：`tiec.exe driver.tie`（compiler 目录内）exit 0 且 tiec 重新编译成功
  EN: First-order bootstrap: `tiec.exe driver.tie` (inside compiler/) exits 0 and tiec recompiles successfully.
- 二阶自举：新 tiec 再编自身，产出与一阶 byte-identical（自举不动点）
  EN: Second-order bootstrap: the new tiec compiles itself again, producing byte-identical output to the first order (bootstrap fixed point).
- 回归：`scripts/regress-s21.ps1` 全量 PASS=79、FAIL=2/SKIP=2（既定基线）零新增
  EN: Regression: `scripts/regress-s21.ps1` full run PASS=79, FAIL=2/SKIP=2 (established baseline), zero new failures.
- 正负例探针各步专属（tests/ 下新增）
  EN: Each step has its own positive/negative probes (added under tests/).

---

## S1 核心微内核化第一步（pipeline 槽 → 注册表执行骨架 + 内建引导集）
*EN: S1 First Step of Core Micro-Kernel-ification (pipeline slots → registry execution skeleton + built-in bootstrap set)*

**目标**：消除 W1 双轨（pipeline 5 硬编码槽 ↔ middle/pass 注册表未接入），
核心获得"注册表执行骨架"雏形；pipeline、passmanager 第一次接通。
EN: **Goal**: eliminate the W1 dual-track (the 5 hard-coded pipeline slots ↔ the disconnected middle/pass registry) so the core gains a "registry execution skeleton"; pipeline and passmanager are wired up for the first time.

| 小任务 | 内容 | 验收 |
|---|---|---|
| S1.1 | 新增 `compiler/lib/registry.tie`（通用注册表：按名按 kind 登记 fn 实现 + 惰性二分查表，对齐 lib/dispatch.tie 先例） | 单测探针 register/find 幂等 |
| S1.2 | passmanager 接入：把 `irgen` 阶段拆为若干细粒度分析/转换 pass，经 registry 注册；pipeline 槽实现变为"执行注册表中的 pass 链" | 编译产物 IR 不变（一/二阶自举 hash 不变） |
| S1.3 | 内建引导集 `compiler/boot.tie`：默认管线定义（front→irgen→tieir→emit→link）作为注册项数据，boot 最先注册 | `tiec` 无外部插件时行为与现状等价 |
| S1.4 | 回归全量 + 提交（S1 验收：自举 hash 不变、regress-s21 零回归） | 提交一次 |

EN: S1.1 adds the generic `compiler/lib/registry.tie`; S1.2 rewires passmanager to run a registry-registered pass chain; S1.3 provides the built-in bootstrap set in `compiler/boot.tie`; S1.4 runs the full regression and commits. Acceptance for all: unchanged bootstrap hash and zero regress-s21 regression.

**风险**：S1.2 若细粒度 pass 拆解导致 IR 顺序变化，先保留"整阶段 pass"粒度（每个槽位
= 一个 pass）保证 hash 不变，细粒度拆解延后到 S2。
EN: **Risk**: if S1.2's fine-grained pass split changes IR order, keep the "whole-stage pass" granularity first (each slot = one pass) to preserve the hash, deferring fine-grained splitting to S2.

---

## S2 id+version 注册项 schema
*EN: S2 id+version Registration-Item Schema*

**目标**：注册项统一携带 id/version/kind/deps；同 id 异 version 仲裁。
EN: **Goal**: registration items uniformly carry id/version/kind/deps; items with the same id but different versions are arbitrated.

| 小任务 | 内容 | 验收 |
|---|---|---|
| S2.1 | registry 注册项 schema 表驱动（并行表：id/kind/version/tie/deps/meta），id 命名白名单校验 | 非法 id 负例拦截 |
| S2.2 | 同 id 同 version 幂等忽略；同 id 异 version 按优先级（内建<config<项目<依赖包）+ 显式依赖约束仲裁 | 冲突负例（priority_neg）正确拦截 |
| S2.3 | 语言版本门禁（tie 约束 vs tiec 版本） | 版本不满足负例拦截 |
| S2.4 | 回归 + 提交 | 提交一次 |

EN: S2.1 makes the registration-item schema table-driven with id whitelist validation; S2.2 makes same-id/same-version idempotent and arbitrates same-id/different-version by priority plus explicit dependency constraints; S2.3 gates on language version; S2.4 runs regression and commits.

---

## S3 tieir 消费入口（import tieir 包，消费方免前端）
*EN: S3 tieir Consumption Entry (import tieir packages; consumers skip the frontend)*

| 小任务 | 内容 | 验收 |
|---|---|---|
| S3.1 | IR 格式版本号冻结：tieir 头写版本，reader 校验不匹配拒绝 | 异版本 tieir 负例拦截 |
| S3.2 | `import "pkg:x.tieir"` 语法 + 加载器：读 tieir → 语义检查 → 并入当前编译单元（复用 tieir_ser.deserialize + ir_meta 导出表） | 包 .tieir 编译运行通过 |
| S3.3 | 依赖解析：tie.pkg dependencies 驱动加载顺序（复用 pkg/deps.fetch） | 依赖包自动加载 |
| S3.4 | 回归 + 提交 | 提交一次 |

EN: S3.1 freezes the IR format version; S3.2 adds the `import "pkg:x.tieir"` syntax and loader; S3.3 drives load order from tie.pkg dependencies; S3.4 runs regression and commits.

---

## S4 data→zd 发布转换
*EN: S4 data→zd Publishing Conversion*

| 小任务 | 内容 | 验收 |
|---|---|---|
| S4.1 | `tie publish` zd 转换：data 配置 → zstd/lz4 压缩变体（复用 ext/codec），输出 `*.zd.tie` | 压缩/解压往返一致 |
| S4.2 | 加载器 zd 读取路径：识别 `.zd.tie` → 解压 → 走 data 相同审计 | zd 包加载运行与 data 等价 |
| S4.3 | 回归 + 提交 | 提交一次 |

EN: S4.1 converts data configs to zstd/lz4-compressed `.zd.tie` variants under `tie publish`; S4.2 adds the loader's zd read path; S4.3 runs regression and commits.

---

## S5 TSHA1 审计链底座 + 凭证/指纹审计链
*EN: S5 TSHA1 Audit-Chain Foundation + Credential/Fingerprint Audit Chain*

| 小任务 | 内容 | 验收 |
|---|---|---|
| S5.1 | 核心 TSHA1 底座定位：tsha1f（文件指纹）+ tsha1x（包树根）随 `std/tsha1.tie` 交付（f/b/x/r 四档已落库）；核实审计链第①道归属（核心单向依赖约束下在 lib/ 或 std 的取舍记录在案） | TSHA1 官方向量探针绿（empty/abc/边界/48 进制往返） |
| S5.2 | 指纹计算：publish 侧递归 **tsha1f per-file → tsha1x tree root**，写入 `tie.pkg hash` + lock | 篡改单文件 → 指纹不匹配定位 |
| S5.3 | 凭证：包内 pubkey + package.sig（**Ed25519 纯 tie 已落库**，std/ed25519.tie，RFC 8032 向量绿） | 冒名包负例拦截 |
| S5.4 | TOFU：首次 fp 确认 → 固化 tie.lock；同 id 异 fp 拦截 | 冒名重放负例拦截 |
| S5.5 | 审计链全序接入（①指纹②验签③fp④IR 版本⑤id/version⑥字段⑦依赖⑧仲裁） | 恶意包样例（tests/custom_role 扩展）全拦截 |
| S5.6 | 回归 + 提交 | 提交一次 |

EN: S5.1 delivers the tsha1f/tsha1x core under `std/tsha1.tie`; S5.2 computes per-file fingerprints → tree root into `tie.pkg hash` + lock; S5.3 uses Ed25519 pure-tie credentials; S5.4 implements TOFU with tie.lock pinning; S5.5 wires up the full audit chain; S5.6 runs regression and commits.

---

## S6 CLI 子命令注册化 + 库树收敛
*EN: S6 CLI Subcommand Registration + Library-Tree Consolidation*

| 小任务 | 内容 | 验收 |
|---|---|---|
| S6.1 | CLI 子命令注册项化（`cli:test`/`cli:bench`/...由注册表分派；未注册报未知命令） | 全命令行按注册项分派 |
| S6.2 | 库树定位：明确 lib_v1 为 std/ext/rdu 唯一演进目标，tie-main 旧树标遗留 | 文档更新 + 双端推送 |
| S6.3 | 回归 + 提交 | 提交一次 |

EN: S6.1 turns CLI subcommands into registration items; S6.2 consolidates the library tree around lib_v1; S6.3 runs regression and commits.

---

## 推送到双端
*EN: Push to Both Remotes*

- tie-main（git.franj2.top origin / github，按 memory：若有 401/TLS 噪音直接重试一次）
  EN: tie-main (git.franj2.top origin / github; per memory: on 401/TLS noise, retry once directly).
- 每步本地提交后立即推送，避免积压；github token 过期则仅推 franj2 并记录
  EN: Push immediately after each local commit to avoid backlog; if the github token expires, push only to franj2 and record it.

---

## 验收通过标准（全部 S1–S6 完成）
*EN: Acceptance-Criteria (all of S1–S6 complete)*

1. `tiec` 无外部插件自举照常（核心独立性）
   EN: `tiec` bootstraps normally with no external plugins (core independence).
2. 外部插件经 tieir 包注册 pass/pipeline/CLI/角色并生效（插件可扩展性）
   EN: External plugins register passes/pipelines/CLI/roles via tieir packages and take effect (plugin extensibility).
3. 恶意/篡改/冒名包全部被审计链拦截（核心不可被修改）
   EN: Malicious/tampered/impersonated packages are all blocked by the audit chain (the core cannot be modified).
4. regress-s21 全程零新增回归
   EN: regress-s21 has zero new regressions throughout.