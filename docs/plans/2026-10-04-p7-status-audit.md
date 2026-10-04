# ROAD p.7 档条目状态核验（2026-10-04）

> 核验对象：tie-main/ROAD.md 的 p.7 档（第 53–104 行）+ 关联定稿一节（第 671–682 行）
> 判据：每条都要求当前代码/实测证据，不采信原标记
> 参考：`tiec/_spec_audit/out/SUMMARY.md`（17 章规范对账，基准 `c8b45f4`）
> 核验时 tiec HEAD：`ecd3436`（p.7 分支）；tiec.exe 构建于 2026-10-04 10:07
> 探针：`F:/Projects/_tmp/roadcheck/`、`F:/Projects/tie-repo/tiec/_spec_audit/p7/`

---

## 统计

| 档 | 原 [x] | 原 [ ] | 原 [~] | 核验后 [x] | [ ] | [~] | 标记有误 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| p.7.1 编译器重构+插件化 | 8 | 0 | 0 | 6 | 0 | 2 | 2 |
| p.7.2 仓库分离+发行模型 | 7 | 0 | 0 | 4 | 0 | 3 | 3 |
| p.7.3 trm 重定位 | 3 | 0 | 0 | 2 | 0 | 1 | 1 |
| 关联定稿（修订项） | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| **合计（21 条）** | **18** | **0** | **0** | **15** | **0** | **6** | **6** |

★ p.7 档全部 18 条原标记均为 `[x]`，无 `[ ]` / `[~]`。核验后 **6 条改判 `[~]`**
（p.7.1.1 / p.7.1.6 / p.7.2.3 / p.7.2.4 / p.7.2.7 / p.7.3.2），
**0 条改判 `[ ]`**——没有「完全没做」的条目，6 条都是「能力在、但验收证据链已断裂」。
关联定稿 3 条按「文档修订」判据核验，3 条全部成立（`[x]`）。

> 关联定稿一节原文用无标记的散列列出 3 份文档，非 `[x]/[ ]` 勾选项；
> 本表按「已修订 / 未修订」赋予对应标记，计入合计。
> 派生量核对：6+4+2+3 = 15 `[x]`，2+3+1+0 = 6 `[~]`，15+6 = 21 = 表行数。

---

## 逐条核验

| ROAD 行号 | 条目 | 原标记 | 核验结论 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 69 | p.7.1.1 核心微内核化（pipeline 5 槽 → 注册表执行骨架 + 内建引导集；passmanager 接入 pipeline） | [x] | **[~]** | 机制全通：`keel_registry.tie`(15916B)/`keel_boot.tie`/`keel_executor.tie` 三文件在；`driver/pipeline.tie:502-524` 真实注册 5 pass + 2 pipeline；自写探针 `keel711.tie` 实测 boot→reg=6 / cli=13 / find=0 / kind=pass / pipeline kind=pipeline / boot 幂等=true / 重复 register 幂等=true / run default pipeline rc=0 | **验收证据两条已不成立**：①仓内 `tests/_p711_probe/keel_probe.tie` **编译失败**（`E00391 keelcli::register` 未定义，p.7.1.6 后 `keel_boot.register_cli` 依赖 `keel_cli`，探针未补 import）；②「tiecA==tiecB 不动点」未复现——完整自举二阶段（27.8MB `.ll` → exe）**30 分钟超时未完成**（rc=124），无法确认当前 HEAD 仍是二阶不动点 |
| 70 | p.7.1.2 id+version 注册方案（schema 表驱动 + 同 id 异 version 仲裁） | [x] | [x] | `keel_registry.tie:154 register_v` / `:204 set_priority` / `:220 arbitrate` / `:285 check_version` / `:59 conflict_flag`；`tests/_p712_probe/ver_probe.tie` 编译 rc=0、运行 rc=0「id+version 自检通过」 | 冲突负例正确拦截。5 断言全过属实 |
| 71 | p.7.1.3 tieir 消费入口（消费方免前端） | [x] | [x] | `keel/keel_tieir_in.tie`(11674B) 9 个 pub fn；`tests/_p713_probe/keel_tieir_in_probe.tie` **11 断言全 PASS**（load/ready/包名/包版本/函数数/IR 主体/emit_ll/.ll 含 @add/write_ll 落盘） | 「llvmgen 直连需 driver 勾挂点（后续）」的让步属实——当前是自包含后端门，非 llvmgen |
| 72 | p.7.1.4 data→zd 发布转换（publish 压缩 + 指纹计算） | [x] | [x] | `compiler/zdpub.tie:76 publish` / `:97 load` + `.zd.fp` 清单；`tests/_p714_probe/zdpub_probe.tie` **5 断言全 PASS**（publish rc=0 / load 指纹一致 / **篡改后拒绝 -1** / 重发布 / 恢复后一致） | 「篡改拒绝探针过」属实 |
| 73 | p.7.1.5 安全审计链（TSHA1 指纹 + 凭证/指纹审计链 + 去中心化信任锚） | [x] | [x] | `keel/keel_auditor.tie`：`:112 fingerprint_tree`（tsha1x 树根）/ `:155 verify_signature`（ed25519）/ `:172 anchor` / `:182 check_anchor` / `:218 audit`；`tests/_p715_probe/audit_probe.tie` **11 断言全 PASS**，含**冒名 -1 / 换钥 -1 / 篡改一字节树根变化 / verify_tree 篡改拦截** | 篡改/冒名/换钥三类负例全拦截，验收标准完全满足 |
| 74 | p.7.1.6 CLI 子命令注册化 + 库树收敛 | [x] | **[~]** | 注册机制通：`keel/keel_cli.tie:63 register` + `keel_boot.tie:121-132` 登记 **13 个 cli:xxx**；`tests/_p716_probe/cli_probe.tie` 运行 rc=0（boot 后命令数 14）；实机 `tiec help/init/add/install/build/run/publish/pack/verify/search/info/pkg` **13 条全部命中注册表分派**；库树收敛文档 `docs/plans/2026-09-11-p7116-libtree-convergence.md` 在 | **分派到桩、不分派到实现**：`driver/keelcli.tie:32 keelcli_cmd_stub` 只 `println` 描述，13 个子命令中 **12 个走 stub**（只有 `pkg` 走 `keelcli_pkg_handle`，而它也只是 println 提示）。源码注释自认「真实工具链未接入 tiec」。ROAD 写的「实机 tie pack/verify 命中」= 命中桩，非命中实现 |
| 75 | p.7.1.7 安全算法底座分类（哈希/MAC/对称/KDF/非对称/后量子，TSHA1 优先） | [x] | [x] | `docs/plans/2026-09-11-p7117-security-base-inventory.md`(141 行) 在；**逐项复核归属偏差仍成立**：`ext/chacha20.tie` 存在而 `std/chacha20.tie` 不存在、`ext/ascon_aead.tie` 存在而 `std/ascon_aead.tie` 不存在、`std/ed25519.tie` + `std/x25519.tie` 存在而 ext 版不存在、`std/rsa.tie`+`ext/rsa.tie` 均不存在（RSA 独立模块仍缺） | 本条**审计交付、零代码**（文档自述「Type: 审计交付…零代码补缺」）。ROAD 标记与交付性质一致，不判有误。但注意「6 建议迁移」清单正文只列 **5 条**（§4 编号 1–5），表头计数 6 与清单不符——文档内部小瑕疵 |
| 76 | p.7.1.8 TSHA 四档家族（f/b/x/r，位平面 trit + 24/48 基，KAT + 交叉验证） | [x] | [x] | `F:/Projects/tlib/std/tsha1.tie:1335-1347` 四个 pub fn `tsha1f/tsha1b/tsha1x/tsha1r` 齐全 + `:1353 tsha1_digest`；`tests/_p718_probe/tsha1_family_kat_probe.tie` 编译 rc=0、运行 **rc=0「PASS 总数=109」**，含 4 模型 pairwise-distinct + `f n16!=24!=32` 差分层断言 | 「补固化 24/32 KAT，109 断言全过」逐字属实 |
| 80 | p.7.2.1 多仓拆分（tie-main 变聚合/发行仓 + 组件独立仓） | [x] | [x] | `docs/release.md:120 §3.4 仓库组织与发行版位置`（组件仓表 11 行）+ `docs/plans/2026-09-11-p721-repo-split.md`（保留/迁移清单，**自述「本轮只规划不移动」**） | 本条就是**规划**条目，ROAD 括注「本轮只规划不移动」与文档一致，不判有误 |
| 81 | p.7.2.2 组件独立发行（各仓独立版本 + Release 附件，发行物出仓） | [x] | [x] | `docs/release.md:179 §3.5`（版本号策略 + artifact 命名 `tie-<component>-<version>-<platform>-<arch>.zip` + 发行清单模板）；**出仓实测**：`git ls-files dist/` 只返回 9 个 `.tie` 源文件，**零 zip 入 git** | 文档条目，无可执行门禁；出仓约定经 git 实测成立 |
| 82 | p.7.2.3 主仓聚合发行（版本集编排 + 互恰校验） | [x] | **[~]** | 资产在：`scripts/tie-versions.data.tie`（8 组件版本约束表）+ `scripts/agg-check.tie` + `docs/release.md:291 §4.5`；**自检逻辑本身通**——用 tiec 仓副本编译 rc=0，`--self-test` rc=0「良性通过 / 篡改拦截 / 缺失检出」**三断言全过** | **主仓副本已失效**：`tie-main/scripts/agg-check.tie` **编译失败** `E00483 无法读取导入文件 'compiler/config.tie'`（p.7.2.7 把 compiler/ 与 std/ 迁出 tie-main，脚本 import 未同步）。`--lib-root F:/Projects/tlib` 也救不了（相对路径 import）。且 tiec 副本与 tie-main 副本已分叉（`package.tie` 差异 1142 行） |
| 83 | p.7.2.4 发行目录 2026.2 改造（发行下设 `src/` + 另出 `tie-{版本}-src.zip`） | [x] | **[~]** | 布局已落地且有产物：`dist/tie-2026.2-win-x64.zip`(347MB) 内含 `tie-2026.2/{bin,docs,src/{compiler,editor,examples,ext,rdu,skills,std}}` + 包根 README/NEW/CHANGELOG/LICENSE；`dist/tie-2026.2-src.zip`(238MB) 独立存在；`scripts/package.tie` 编译 rc=0 | **产物早于代码，且已被超越**：①zip 时间戳 2026-09-11 11:12，早于 p.7.2.7 拆分（09-12）与 skia 剪枝提交 `acc4086`（09-12 00:23，声称 src.zip 138→73MB）——包内 `src/ext/gfx/skia` **仍有 13943 个条目**（剪枝未生效于该产物）；②`src/components/` 在包内 **0 条目**，而 `package.tie:363 s3_components` 正是为拆分后 12 个组件仓收拢而加——**该聚合路径从未随产物验证过**；③`dist/tie-2026.2/` 解压目录已不存在（只剩 zip） |
| 84 | p.7.2.5 包注册中心 registry 起步 | [x] | [x] | `keel/keel_registry_cli.tie`(10694B, namespace keelpkg) `publish/info/versions` 三操作 + `:227` 调 `zdpub.publish` + `.zd.fp`/`info.td`/`index.td` 存储布局；`tests/_p725_probe/reg_probe.tie` 编译 rc=0、运行 **rc=0，10 断言 ALL PASS**（含 zdpub.load 指纹一致 + 源文件不存在 -1 + 空包名 -1 + 未发布 info/versions -1 + 目录结构就位）；`docs/release.md:329 §4.6` 格式文档在 | 「探针 10 断言 ALL PASS」逐字属实。唯一让步已在文档写明：服务端/协议随 p.9.2.2 |
| 85 | p.7.2.6 更新 README（主仓定位 + 发行模型 + 组件索引） | [x] | [x] | `README.md:86-105 发行模型`（双语）+ `:107-122 工程结构`（tie-main 四目录树）+ `:124-143 组件索引`（11 行组件表，全部指向 `tie-lang/*` 新仓）；`git ls-files` 实测 tie-main **只剩 dist/docs/scripts/assets/.github + 仓库级文件**，tracked `.tie` 仅 12 个（9 dist + 3 scripts） | README 内容与实际仓库结构一致。ROAD 括注的「自举不动点 + 回归 104 PASS」是文档改动的附带证据，不单独判 |
| 86 | p.7.2.7 多仓拆分执行落地（六仓 subtree split + tie-main 删目录） | [x] | **[~]** | **拆分确实完成**：`git ls-files` 在 `compiler/ std/ tests/ pkg/ examples/ ext/ repl/` 下返回 **0 条**（目录只剩未跟踪的 .exe/.ll 构建残留，且已被 .gitignore 覆盖，如 `.gitignore:71-72`）；`tsp`/`tpkg`/`tdb`/`tie-dev`/`vscode-tie`/`tiec` 六仓均有独立 `.git` + `origin https://github.com/tie-lang/<name>.git`；历史保留可查（`tsp` 11 commits，最早 `8ded3f5` 即 LSP 初始提交） | **拆分把 tie-main 自己的发行脚本打断了**（见 p.7.2.3）：`scripts/agg-check.tie` 与 `dist/*.tie` 都 import `../compiler/` `../std/`，这些目录已迁出 ⇒ 主仓**当前无法构建自己的聚合校验与发行打包器**。另有 3 个组件仓（`tink`/`tlib`/`twi`）在 tie-repo 下**无 `.git`**，与 §3.4 宣称的「组件独立仓」不符（tink/tlib/twi 未完成建仓） |
| 102 | p.7.3.1 trm 定稿修订（对齐新分工） | [x] | [x] | `docs/designs/trm-final-design.md`(35242B) `:5-8` 修订声明（无语言层多线程 / 无表内存 GC / 引擎级 GC 保留 / 协程移交 trm-lite）+ `:400 §10` 里程碑改按 p.7.3.x 编号（P0–P5 已清理）+ `:227` §5 M:N 协程段落改写；`docs/release.md:114/142` tiu/trm 发行衔接 + §3.5 artifact 命名 | 双语文档齐备，「内部阶段编号清理」属实（§10 标题即「按 2026.2 ROAD p.7.3.x 落地」） |
| 103 | p.7.3.2 tieir 字节码 + interp 前端 + 可替换后端 + 类加载器 + 反射 + 引擎级 GC（路线 B） | [x] | **[~]** | 六期代码全在：`trm/{trm_loader,trm_interp,trm_sys,trm_gc,trm_backend,trm_reflect}.tie`。**6 期探针实测：b/c/f 全绿**（b: 27 断言 rc=0；c: 34 断言 rc=0 含环 GC/负例；f: 24 断言 rc=0 含四端契约矩阵）；**能力本体实测可跑**：自写 `lir1.tie` 单函数 load rc=0 + `run_by_name` **result=7 正确**；`refl1.tie` 反射全通（模块名/版本/函数名/op 名/describe/module_info + 动态 invoke **result=42**） | **a/d/e 三期探针实测失败**（`tests/_p732a|d|e_probe`，rc=1，失败 10/7/11 项）。根因**不是能力缺失、而是探针陈旧**：p.9.21.7(D1)/ce0dbc0 改了 tieir 值空间重映射（`tieir_ser.tie:715` 出生序连续性校验），而这三个探针按旧布局先建全部函数再建指令 ⇒ 「指令结果值非连续（指令 0 文件 3 期望 2）」。自写 2 函数复现（`lir2.tie` 同样报错），而**真实编译器产出的 3 函数 `.tieir` 加载 rc=0**。⇒ 判 `[~]`：**能力已落地，但 6 期「探针 ALL PASS」的验收证据今天跑不出来** |
| 104 | p.7.3.3 编译器侧 trm 目标接线（`--target trm` 可插拔后端，默认不启用） | [x] | [x] | `driver/cli_args.tie:182`（`--target trm` → `g_trm_mode`）+ `:203`（`--backend trm` 同）；`driver/pipeline.tie:359 kpass_trmemit` + `:519` 注册 `pass_trmemit_real` + `:524 pipeline_trm` + `:22` 按 `asm_target=="trm"` 分流；**实测** `tiec t1.tie --target trm -o t1.tieir` **rc=0 产出 421037 字节 .tieir**；`tests/_p733_probe/trm_probe_733.tie` 生成 `.tieir` 后运行 **rc=0，5 断言全 PASS**（含「真实编译器产物函数 calc::add 按名可查」） | 「默认不启用、全程不动」属实（`g_trm_mode` 门控）。括注的「自举不动点 + 回归 104 PASS」同 p.7.1.1 未复现，但本条主验收（产物可被引擎加载校验 + 函数按名可查）**已实测通过**，故不降级 |
| 675 | 关联定稿：docs/designs/trm-final-design.md（对齐 p.7.3 trm 重定位） | （无标记） | [x] | 同 p.7.3.1：`:5-8` 修订头 + `:400 §10` 编号清理 + 双语 | 已就地修订，无另立档 |
| 676 | 关联定稿：docs/release.md（对齐 p.7.2 多仓拆分与聚合发行、p.9.4 tiu 独立定位、发行物出仓） | （无标记） | [x] | §3.4 组件仓表 + §3.5 组件独立发行/出仓 + §4.5 聚合发行 + §4.6 registry；tiu 独立定位见 `:62/:114/:142`（不依赖 trm、可与 trm 同用）；出仓经 `git ls-files dist/` 实测零 zip | 四项对齐要求逐项命中 |
| 677 | 关联定稿：docs/superpowers/specs/2026-08-29-plugin-kernel-design.md（落地编号对齐 p.7.1.x） | （无标记） | [x] | `:158-159` 明写「落地编号按 ROAD.md p.7.1.x 执行：S1–S6 对应 p.7.1.1–p.7.1.6，安全算法底座 p.7.1.7，TSHA 家族 p.7.1.8；本文档不再自行编号」+ `:165-172` 步骤表已改写为 p.7.1.x 列 | 编号对齐彻底，S1–S6 自编号已作废 |

---

## 标记有误的条目（**需上报**）

> 本节共 **6 条**标记有误（对应上表 6 个 `[~]`），另有第 7 小节为备案项（不判有误）。

### 1. `ROAD.md:82` p.7.2.3 主仓聚合发行 —— `[x]` → `[~]`

**证据**：`tie-main/scripts/agg-check.tie` **编译失败**。

```sh
cd F:/Projects/tie-repo/tie-main
F:/Projects/tie-repo/tiec/compiler/tiec.exe scripts/agg-check.tie -l2 -t0 --no-warn --no-cache \
  -o F:/Projects/_tmp/aggchk.exe
# rc=1
# error[E00483] @26:1: 无法读取导入文件 'compiler/config.tie'（文件不存在）
```

加 `--lib-root F:/Projects/tlib` 仍 rc=1（同错）——脚本用的是**相对路径** import
`../compiler/config.tie` + `../std/tsha1.tie`，而 p.7.2.7 已把这两棵树迁出 tie-main。

**能力未全失**：tiec 仓有一份分叉副本，`tiec/scripts/agg-check.tie` 编译 rc=0，
`--self-test` 输出「自检 ALL PASS」（良性通过 / 篡改拦截 / 缺失检出三断言全过）。
⇒ 逻辑在，**主仓那份是死代码**。ROAD 括注「agg-check.tie（聚合校验，--self-test 三断言全过）」
在 tiec 仓成立，在 tie-main 仓不成立。

### 2. `ROAD.md:83` p.7.2.4 发行目录 2026.2 改造 —— `[x]` → `[~]`

**证据**：产物存在但**早于代码、且未含拆分后路径**。

| 检查 | 实测 |
| --- | --- |
| `dist/tie-2026.2-win-x64.zip` | 存在，347579482 字节，**时间戳 2026-09-11 11:12** |
| `dist/tie-2026.2-src.zip` | 存在，238282465 字节，同时间戳 |
| 包内 `src/` 子目录 | `compiler/ editor/ examples/ ext/ rdu/ skills/ std/` —— **拆分前的旧布局** |
| 包内 `src/components/` | **0 条目**（`package.tie:363 s3_components` 专为拆分后 12 组件仓而加，从未进产物） |
| 包内 `src/ext/gfx/skia` | **13943 条目**（提交 `acc4086`「skia 剪枝 9 文件，src.zip 138→73MB」晚于 zip 一天，剪枝未作用于该产物） |
| `dist/tie-2026.2/` 解压目录 | **不存在**（只剩 zip） |

⇒ ROAD 括注「实测打包 dist/tie-2026.2（bin/docs/src + 包根文档）+ 两个 zip，解包跑通 hello」
在 2026-09-11 当时为真；今天该产物**不能代表当前 `package.tie` 的行为**，也未包含
p.7.2.7 拆分后的 `src/components/` 聚合形态。

### 3. `ROAD.md:86` p.7.2.7 多仓拆分执行落地 —— `[x]` → `[~]`

**证据（拆分本体为真）**：`git ls-files` 在 `compiler/ std/ tests/ pkg/ examples/ ext/ repl/`
下返回 0 条；六仓均有 `.git` + `tie-lang/*` origin；`tsp` 保留 11 条历史提交。

**证据（副作用为假）**：拆分打断了 tie-main 自己的发行工具链——

```sh
cd F:/Projects/tie-repo/tie-main
F:/Projects/tie-repo/tiec/compiler/tiec.exe dist/main.tie -l2 -t0 --no-warn --no-cache \
  -o F:/Projects/_tmp/distmain.exe
# rc=1
# error[E00483] @11:1: 无法读取导入文件 'std/args.tie'（文件不存在）
```

`dist/` 下 9 个 `.tie` 全部 `import "../std/*.tie"`（archive/assemble/checksum/installer/
main/msi 六个），`scripts/agg-check.tie` import `../compiler/config.tie` + `../std/tsha1.tie`
⇒ **tie-main 当前既构建不了发行打包器，也构建不了聚合校验器**。

另：`tink` / `tlib` / `twi` 三个组件仓在 `F:/Projects/tie-repo/` 下**无 `.git`**，
与 `release.md:120 §3.4` 宣称的组件独立仓清单不符（p.7.2.7 括注只列了「六仓」，
README:130/134/135 却已把 tink/tdb/twi 标「已独立」——README 领先于事实）。

### 4. `ROAD.md:103` p.7.3.2 tieir 字节码 + interp + 后端 + 类加载器 + 反射 + 引擎级 GC —— `[x]` → `[~]`

**证据**：6 期探针中 **a/d/e 三期实测 rc=1**。

| 探针 | rc | 失败项 | 首条失败信息 |
| --- | --- | --- | --- |
| `tests/_p732a_probe` | 1 | 10 | `tieir 指令结果值非连续（指令 0 文件 8 期望 2）` |
| `tests/_p732d_probe` | 1 | 7 | `控制流落出（块 0 无结尾 ret/br）`（load 已失败连锁） |
| `tests/_p732e_probe` | 1 | 11 | `tieir 指令结果值非连续（指令 0 文件 3 期望 2）` |
| `tests/_p732b_probe` | 0 | 0 | 全绿（27 断言） |
| `tests/_p732c_probe` | 0 | 0 | 全绿（34 断言） |
| `tests/_p732f_probe` | 0 | 0 | 全绿（24 断言） |

**能力本体不缺**（自写探针实测）：
- `lir1.tie`（单函数手建 LIR）：`load rc=0` + `run_by_name("add",[3,4])` = **7 正确**
- `refl1.tie`（单模块反射）：模块名/版本/函数名/op 名/describe/module_info 全对，
  动态 `invoke add(20,22)` = **42 正确**
- 真实编译器 **3 函数** `.tieir`：`trm.load rc=0`，`module_count=1`（`loadprobe.tie`）

**根因是探针陈旧，不是能力缺失**：p.9.21.7(`3b07272`) + `ce0dbc0` 引入 D1 值空间
重映射，`tieir_ser.tie:710-716` 增加了「文件结果值必须等于期望领号」的出生序连续性
校验。这三个探针沿用旧布局（**先把 4 个函数全建完再建指令**，参数值先于结果值领号），
于是撞上校验。自写 2 函数版（`lir2.tie`）用同样布局 ⇒ 同样报错；
真实编译器按新布局发射 ⇒ 加载通过。

⇒ ROAD 括注「**6 期探针 ALL PASS**」今天**跑不出来**（3/6 失败）。
能力已落地，但验收证据链断了。

### 5. `ROAD.md:69` p.7.1.1 核心微内核化 —— `[x]` → `[~]`

**证据（机制全通）**：自写 `keel711.tie` 实测 `boot → reg=6 / cli=13 / find=0 /
kind=pass / pipeline kind=pipeline / boot 幂等=true / 重复 register 幂等=true /
run default pipeline rc=0`。

**证据（验收证据断裂两处）**：
1. 仓内验收探针 `tests/_p711_probe/keel_probe.tie` **编译失败**：
   `error[E00391] @121:5: 命名空间函数 'keelcli::register' 未定义`。
   根因：p.7.1.6 让 `keel_boot.tie:121` 的 `register_cli()` 调 `keelcli.register`，
   而该探针只 import registry/boot/executor 三文件，**未补 `keel_cli.tie`**
   （`keel_boot.tie:31-33` 明写「本文件不 import keel_cli.tie，依赖入口 import 链内联」）。
   ⇒ p.7.1.6 落地时**打断了 p.7.1.1 的验收探针**，两处 `[x]` 同时成立但探针不再可跑。
2. 「tiecA==tiecB 不动点 + .ll 逐字节等价」**未复现**：完整自举二阶段
   （27.8MB `.ll` → exe）跑 **30 分钟超时**（rc=124），当前 HEAD 是否仍二阶不动点未验证。

### 6. `ROAD.md:74` p.7.1.6 CLI 子命令注册化 —— `[x]` → `[~]`

**证据**：注册与分派机制通，但**终点是桩**。

`driver/keelcli.tie:32-35`：
```
pub func keelcli_cmd_stub(cmd: string) -> i64 {
    println("[keel-cli] 子命令 '" + cmd + "' 已按注册表分派（工具链未接入 tiec，边界见 p.7.1.6）: " + ...)
    return 0
}
```
`keelcli_handle` 的 14 个 case 中 **13 个 `return keelcli_cmd_stub(...)`**，
只有 `case 13: return keelcli_pkg_handle()` 不是桩——而 `keelcli_pkg_handle`
(`:109-121`) 也只是 println「实际执行: keelpkg.xxx」+ 用法文本，**不调用 keelpkg**。

实机 13 条子命令全部 rc=0 且输出 `[keel-cli] 子命令 ... 已按注册表分派`，
但**没有一个执行了真实工具链**。

⇒ ROAD 括注「实机 tie pack/verify **命中**」= 命中桩分派，不是命中 pack/verify 实现。
验收标准原文「全命令行按注册项分派」在**机制层**达成（注册表 + 按表分派 + 13 项登记），
在**行为层**未达成。判 `[~]`，缺口 = 真实工具链接入（源码注释即如此自认）。

### 7. `ROAD.md:75` p.7.1.7 —— `[x]` 成立，但文档内部计数不符（不判有误，备案）

清单表头写「归属层偏差（建议迁移，不移动）| **6 项**」，而 §4 正文只列 **5 条**
（chacha20→std、ascon_aead→rdu、ed25519→ext、x25519→ext、ecdsa_p256→归并 ext）。
§2 表内标注「归属层偏差」的行也是 5 行。属文档内部小瑕疵，不影响判定。

---

## 卡在何处（`[~]` 条目的半成品状态）

### p.7.1.1 —— 机制 100%，卡在「验收探针」与「二阶不动点」两关

| 步骤 | 状态 |
| --- | --- |
| keel_registry/boot/executor 三文件 | ✅ 在（15916 / 7049 / 5250 字节） |
| driver 真实 5 pass + 2 pipeline 接线 | ✅ `driver/pipeline.tie:502-524` |
| 注册表执行骨架可跑（boot/dispatch/幂等） | ✅ 实测 rc=0，11 项断言全过 |
| **原验收探针可编译** | ❌ `tests/_p711_probe/keel_probe.tie` 缺 `keel_cli.tie` import |
| **tiecA==tiecB 二阶不动点** | ❓ 未验证（27.8MB `.ll` 链接 30 分钟超时，rc=124） |
| 回归 104 PASS | ❓ 未复跑（`scripts/regress-s21.tsh.tie` 需 tsh 宿主，`repl.exe --version` 无输出） |

**下一步动作**：给 `keel_probe.tie` 补 `import keel_cli.tie`（一行）→ 恢复验收探针；
二阶不动点需后台长跑（>30 min）单独立项，不要挂在 p.7.1.1 验收下。

### p.7.1.6 —— 注册与分派 100%，卡在「工具链接入」这一跳

| 步骤 | 状态 |
| --- | --- |
| keel_cli 注册表（register/has/count/desc_of） | ✅ `keel_cli.tie:63` |
| boot 登记 13 个 `cli:xxx` | ✅ `keel_boot.tie:121-132`，实测 count=13 |
| driver `tie<cmd>` 层按表分派 + 未登记报错 | ✅ `keelcli.tie:39-103` 14 个 case |
| 库树收敛文档（std/ext/rdu ↔ lib_v1 定位） | ✅ `docs/plans/2026-09-11-p7116-libtree-convergence.md` |
| **13 子命令真实执行** | ❌ 13/13 走 `keelcli_cmd_stub`（`keelcli.tie:32`） |
| **`tie pkg` 真实转 keelpkg** | ❌ `keelcli_pkg_handle` 只 println，不调 keelpkg |

**下一步动作**：`keelcli_cmd_stub` 的 13 个 case 换成真实实现入口；
`keelcli_pkg_handle` 改为调 `keelpkg.publish/info/versions`（模块已有且探针全绿，
只差接线）。**注意**：这与 p.7.2.5 已在 `release.md §4.6` 写明的边界重叠，
接线时应把 p.7.1.6 与 p.7.2.5 一起收口，否则两条永远互相引用对方。

### p.7.2.3 —— 校验逻辑 100%，卡在「主仓副本 import 路径」

| 步骤 | 状态 |
| --- | --- |
| `scripts/tie-versions.data.tie` 版本集 | ✅ 8 组件约束表 |
| `scripts/agg-check.tie` 校验逻辑 | ✅ tiec 副本编译 rc=0，`--self-test` 三断言 ALL PASS |
| `release.md §4.5` 聚合布局 | ✅ 在 |
| **tie-main 副本可编译** | ❌ `E00483 compiler/config.tie` 不存在 |
| **两仓副本一致** | ❌ tiec 版已改 `import "/std/tsha1.tie"`（库根别名），tie-main 版仍 `../std/tsha1.tie` |

**下一步动作**：把 tiec 版 `import "/std/tsha1.tie"` 的库根别名写法回灌 tie-main，
并删掉 tie-main 对 `../compiler/config.tie` 的依赖（改 `/std` 别名 + 库根取值）。
**这是 p.7.2.7 拆分遗留的唯一硬伤，5 分钟可修。**

### p.7.2.4 —— 打包脚本能编译，产物是「过期证据」

| 步骤 | 状态 |
| --- | --- |
| `scripts/package.tie` 5 步改造 | ✅ 编译 rc=0（无 import，纯系统命令 + 自写 zip） |
| `src/` 收拢 + 独立 `-src.zip` 逻辑 | ✅ `:233-278` s3_examples/s3_libs/s3_compiler |
| 拆分后组件聚合 `src/components/` | ✅ 代码在（`:363-401` 12 个组件仓 robocopy + prune） |
| **产物含 `src/components/`** | ❌ 0 条目（zip 早于该功能 1 天） |
| **产物已剪 skia** | ❌ 13943 条目残留（zip 早于剪枝提交 1 天） |
| `dist/tie-2026.2/` 目录可查 | ❌ 不存在（只剩 zip） |

**下一步动作**：重跑一次 `package.tie` 出新版 zip + 解压目录，作为 p.7.2.4 的
当前证据；否则 `[~]` 长期挂着。注意打包耗时（历史 zip 347MB + 13843 skia 文件）。

### p.7.3.2 —— 引擎能力 100%，卡在「a/d/e 探针的 IR 布局迁移」

| 期 | 能力 | 探针现状 |
| --- | --- | --- |
| a tieir 加载/校验 + InterpBackend | ✅ 自写 `lir1.tie` load rc=0、add=7 | ❌ 探针 rc=1（10 失败） |
| b 库层 min 域 + C1 平台桥 | ✅ | ✅ 27 断言 rc=0 |
| c 引擎级 GC | ✅ 精确根 + mark-sweep + 周期 | ✅ 34 断言 rc=0 |
| d Backend 三接口 + 热点提升 | ✅ 4 后端登记 + 回退哨兵 -66 | ❌ 探针 rc=1（7 失败） |
| e 反射/内省 + 动态 invoke | ✅ 自写 `refl1.tie` 全对 + invoke=42 | ❌ 探针 rc=1（11 失败） |
| f 四端平台表 + 域/契约矩阵 | ✅ | ✅ 24 断言 rc=0 |

**卡点定位到一行**：`compiler/middle/tieir_ser.tie:715`
```
if ivl != next_orig {
    set_err("tieir 指令结果值非连续（指令 " + ii2 + " 文件 " + ivl + " 期望 " + next_orig + "）")
```
p.9.21.7 (`3b07272`) + `ce0dbc0` 的 D1 值空间重映射落地后，**手建 LIR 必须按
「函数边界处参数领号、结果随指令领号」的交错布局**；而 a/d/e 三探针仍是
「全部函数先建（参数一次领完）→ 再建指令」的旧布局。

**下一步动作**（三选一，建议 a）：
- **a. 改探针**（推荐）：把 a/d/e 的 `build_*` 改为「建一个函数 → 建它的块与指令 →
  再建下一个函数」，对齐 D1 布局。能力不动，只改测试代码顺序。
- b. 放宽校验：给 `tieir_ser.tie` 加兼容分支接受旧布局（治标，且与 D1 意图冲突）。
- c. 提供 `ir` 层构造助手（如 `ir.begin_func_batch/flush`）供探针按新布局建模块。

---

## ROAD 里完全没提、但该提的缺口

1. **主仓发行工具链被打断（p.7.2.7 的未申报副作用）**
   `dist/*.tie`（6 个文件）+ `scripts/agg-check.tie` 全部 import 已迁出的
   `../std/`、`../compiler/` ⇒ **tie-main 现在构建不了自己的打包器与聚合校验器**。
   p.7.2.7 只申报了「删除对应目录并同步文档引用/聚合脚本收敛清单」，
   **没申报脚本 import 未同步**。这是 p.7 档唯一「拆出真伤」。

2. **`.ll` 字节级不可复现：缓存命中与否改变 IR（编译器缺陷）**
   同一输入、同一编译器、`--emit-ir` 两次：

   | 条件 | sha256（前 16） | 字节数 |
   | --- | --- | --- |
   | 首次运行（缓存未建立） | `203908a074169f54` | 27857621 |
   | 二次运行（缓存命中） | `3ef652c63ed62b8d` | 27862327 |
   | `--no-cache` 两次 | `203908a074169f54`（两次一致） | 27857621 |

   `diff` 显示差异在文件头 extern 声明段（缓存命中版多出 `GetCommandLineW` /
   `CreateFileW` / `tl_tbl$tbl_new_deep` 等 11 条 declare，两条顺序也变了）。
   ⇒ **`.ll` 逐字节等价只在固定缓存状态下成立**。这条直接削弱 p.7.1.1 /
   p.7.2.6 / p.7.3.3 三处「.ll 逐字节等价」的验收语义——ROAD 没写这个前提。
   **建议单列为编译器缺陷**（可复现、影响可复现构建声明）。

3. **README 组件索引领先于仓库事实（文档失真）**
   `README.md:130` 标 tink「已独立」、`:134` tdb「已独立」、`:135` twi「已独立」，
   但 `F:/Projects/tie-repo/{tink,tlib,twi}` **无 `.git`**，未完成建仓。
   p.7.2.7 括注只承认「六仓」，README 却已按 11 组件表全部标「已独立」。

4. **p.7.3.2 的「interp 执行真实编译器产物」仍是空的**
   `tests/_p733_probe` 注释自陈：「真实编译器 `--target=trm` 产物为 LLVM 风格
   tie-IR（zext/alloca/load 等），interp 前端语义基准是 LIR 子集……完整闭环需要
   路线 B 的 LIR 发射层」。实测确认：真实产物可**加载 + 函数按名可查**，
   但**不可执行**。⇒ p.7.3.2 的「InterpBackend 纯函数执行」只在**手建 LIR** 上成立。
   ROAD 用「interp 前端」这个措辞掩盖了「只跑 LIR 子集」这个限定。

5. **p.7.1.6 与 p.7.2.5 互相甩锅**
   p.7.1.6 说真实工具链「边界见 p.7.1.6」（自指）；
   `release.md §4.6` 说 `tie pkg` 三操作「服务端/协议随 p.9.2.2 正式落地」。
   ⇒ `tie pkg publish` 这条命令**当前无任何条目真正负责它**（p.7.2.5 说做了、
   p.7.1.6 说没接、p.9.2.2 说将来做）。排期时会漏。

6. **关联定稿一节没有可勾选标记**
   第 671–682 行是 3 条无标记散列，格式上无法参与 `[x]/[ ]` 计数，
   也无法像 p.7 各条那样附「已落地日期 + 证据」。建议归档重写时补成
   `- [x] …——已落地 YYYY-MM-DD：证据`。

7. **p.7.1.7 清单文档表头计数与正文不符**（6 vs 5，见上文第 7 条）。

---

## 附：核验方法与纪律

* **不复用文档结论**：所有判定基于 `grep` 定位 + 自写/仓内探针实测。
  采信 SUMMARY.md 的仅一处——它对 p.7 档无覆盖。
* **编译探针写法**：`./compiler/tiec.exe <probe> -l2 -t0 --no-warn --no-cache -o F:/Projects/...`
  （`-o` 必须 `F:/` 盘符；不用管道看结果；UTF-8 输出用 `grep -a` 或 `iconv -f gbk -t utf-8`）。
* **CWD 敏感**：`tests/_p713_probe` / `_p714_probe` / `_p733_probe` 用相对路径读写
  样本文件，**必须在 `F:/Projects/tie-repo/tiec` 下运行**；在别处跑会假失败
  （本轮首次跑 p713/p714 即踩到，切回 tiec 目录后全绿）。
* **探针陈旧与能力缺失的区分方法**：对失败项自写**最小复现**再判
  ——`lir1.tie`（单函数过）/ `lir2.tie`（双函数挂）定位到 D1 布局约束；
  `multifunc.tie`（真实编译器 3 函数过）证明能力未缺失。
* **未完成验证（诚实标注）**：tiecA==tiecB 二阶不动点、回归 104 PASS 基线，
  本轮**未取得证据**（前者 30 分钟超时 rc=124；后者缺 tsh 宿主无法驱动
  `regress-s21.tsh.tie`）。相关条目的判定不依赖这两项，但括注中的这两项
  应视为**未经本轮复核**。
