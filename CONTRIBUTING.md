# tie 贡献指南

*EN: Contributing Guide*

本指南定义 tie 开发的编号、模块与变更记录规范。**所有贡献者与 AI 代理必须遵守**。

EN: This guide defines the numbering, module, and changelog conventions for tie development. **All contributors and AI agents must follow it.**

## 1. 编号规范：p.x.x.x

*EN: Numbering convention: p.x.x.x*

废弃一切无意义的字母+数字混合标记（如 H1、M1、P1、F1 等编号）。
统一使用 **p.x.x.x** 四段编号：

EN: All meaningless letter-digit mixed tags (e.g., H1, M1, P1, F1) are deprecated. Use the **p.x.x.x** four-part numbering instead:

```
p.<发布档>.<开发模块>.<子项>
p.<release slot>.<development module>.<sub-item>
```

* **p** = 预发布（preview）。**大版本号省略**：完整的版本号是 `<大版本>-p<发布档>...`
  （如 `2026.1-preview.5` → 编号写作 `p.5.x.x`），写作时不再写大版本号。

* **第一个 x = 发布档**（发布序号）：每出一个新的预发布版递增
  （preview\.1 → p.1，preview\.5 → p.5）。正式版之前的修复批次继续顺延下一档号。

* **第二个 x = 开发模块序号**：在**每个预发布版开发前**由主导者定好：
  本版要开展哪几个开发模块、每个模块几号、该模块干什么。

* **第三个 x = 子项**：模块内细分项，**不用预先规划**，实现时自动递增
  （第一个子项从 1 起；只有单个子项时也可省略为 p.x.y）。

EN:

* **p** = preview. The **major version is omitted**: the full version reads `<major>-p<slot>...` (e.g., `2026.1-preview.5` → `p.5.x.x`); the major version is not written.

* **First x = release slot**: increments with each new preview release (preview\.1 → p.1, preview\.5 → p.5). Fix batches before the stable release continue with the next slot number.

* **Second x = development module number**: decided by the lead **before each preview version starts** — how many modules this version has, their numbers, and what each module does.

* **Third x = sub-item**: a finer split inside a module, **not pre-planned**; it increments automatically during implementation (the first sub-item starts at 1; p.x.y is fine when there is only one item).

### 编号使用示例

*EN: Numbering examples*

| 编号 / Number | 含义 / Meaning                                                                                  |
| ----------- | --------------------------------------------------------------------------------------------- |
| `p.5.1.1`   | preview\.5 · 开发模块 1 · 子项 1 / preview\.5 · dev module 1 · sub-item 1                           |
| `p.6.2`     | 正式版修复档 6 · 开发模块 2（只有一项时省略子项）/ stable-fix slot 6 · dev module 2 (sub-item omitted when single) |
| `p.6.3.2`   | 正式版修复档 6 · 开发模块 3 · 子项 2 / stable-fix slot 6 · dev module 3 · sub-item 2                      |

### 开发模块规划流程（每版开发前必做）

*EN: Development-module planning flow (required before each version)*

1. 大版本开始时：确定本大版本的整体工作方向（写入本指南同区/计划文档）。
2. 每个预发布版开发前：定好本版开发模块清单——
   `p.<发布档>.1 = 做什么`、`p.<发布档>.2 = 做什么`……
   只定到第二个 x；第三个 x 实现时自动补。
3. 任务分发：按**开发模块**分发（不再使用「里程碑」一词，统一称**开发模块**）；
   每个模块可由独立子代理/负责人认领，完成后汇报编号。
4. 各模块完成时，在 CHANGELOG 对应条目标注其 p 编号，方便追溯。

EN:

1. At the start of a major version: decide the overall direction (recorded here or in a plan doc).
2. Before each preview version: define its development-module list — `p.<slot>.1 = what it does`, `p.<slot>.2 = what it does`, ... Only plan up to the second x; the third x is filled in during implementation.
3. Task dispatch: by **development module** (the word "milestone" is no longer used; say **development module**); each module can be claimed by an independent sub-agent/owner, who reports the number on completion.
4. When a module lands, annotate its p number in the corresponding CHANGELOG entry for traceability.

## 2. 变更记录规范（CHANGELOG.md）

*EN: Changelog convention (CHANGELOG.md)*

见 [CHANGELOG.md](CHANGELOG.md) 顶部「写作规范」块，要点：

EN: See the "writing rules" block at the top of [CHANGELOG.md](CHANGELOG.md). Key points:

* 写完即记（与 commit 同内容），不批量攒；

* 条目格式：`## [类型] 一句话标题（YYYY-MM-DD）`，可附 `（p.x.y.z）` 编号；

* 时间倒序，新条目在版本段标题之下、更旧条目之上；

* 版本段标题：`## Harbor-2026.1-preview.N（YYYY-MM-DD）` / `## 2026.1（正式版，进行中）`；

* 条目必须位于其版本段标题之下，归属以 git tag 边界为准；

* 禁止：重复条目、`---##` 等烂格式、正文夹带旧标题残留、删除历史条目；

* 大版本归档：正式版发布时把当前 CHANGELOG.md 复制为仓库根 `<版本>.CHANGELOG`，
  清空重记下一版本。

EN:

* Log each change immediately (same content as the commit); do not batch.

* Entry format: `## [type] one-line title (YYYY-MM-DD)`, optionally with `（p.x.y.z）`.

* Newest first: new entries go under their version heading, above older ones.

* Version headings: `## Harbor-2026.1-preview.N（YYYY-MM-DD）` / `## 2026.1（stable, in progress）`.

* Entries must sit under their version heading; membership follows git tag boundaries.

* Forbidden: duplicate entries, malformed headings (`---##`), stray legacy headers in the body, deleting history.

* Major-version archive: on stable release, copy this CHANGELOG.md to `<version>.CHANGELOG` at the repo root, then start a fresh one.

## 3. 提交与发布流程

*EN: Commit and release flow*

* 每次开发/修复：写代码 → 跑验证/探针 → 追加 CHANGELOG 条目（写 p 编号）→ git commit。

* 大版本开发前：确定工作方向与首批开发模块编号（本指南同区记录）。

* 预发布版开发前：确定本版开发模块编号清单（只定到第二个 x）。

* 预发布版发布：打 tag `Harbor-<大版本>-preview.N`，更新 NEW\.md。

* 正式版发布：打 tag、归档 CHANGELOG 为 `<大版本>.CHANGELOG`、清空重记。

EN:

* Every dev/fix: write code → run verification/probes → append a CHANGELOG entry (with p number) → git commit.

* Before a major version: set the direction and the first development-module numbers (recorded in this guide).

* Before a preview version: set that version's development-module numbers (only up to the second x).

* Preview release: tag `Harbor-<major>-preview.N`, update NEW\.md.

* Stable release: tag, archive CHANGELOG as `<major>.CHANGELOG`, start fresh.

## 4. 术语

*EN: Terminology*

* **开发模块** = 单位开发批次/工作项（旧称「里程碑」，已停用）。

* **发布档** = 每次预发布/发布窗口的序号。

EN:

* **Development module** = a unit development batch/work item (formerly "milestone"; deprecated).

* **Release slot** = the sequence number of each preview/release window.

