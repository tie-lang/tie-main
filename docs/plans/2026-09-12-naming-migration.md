# tie 生态命名迁移执行计划 —— 尽早 · 彻底
*EN: tie Ecosystem Naming Migration Plan — early · thorough*

**日期** / Date: 2026-09-12 · **类型** / Type: 执行计划（命名规范落地；尽早 + 彻底，不留旧名兼容期）
**依据** / Basis: `docs/designs/tie-naming-convention.md` v0.2（按实体类型分类命名）· 用户要求「尽早 · 彻底」（2026-09-12 定）
**关联** / Related: 命名规范（tie-naming-convention.md）· ROAD p.9.x 各组件仓 · tie-repo 本地工作区
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: Executes the component renames from the naming convention —
> tiedb→tdb · tiwi→twi · tie-pkg→tpkg · tie-diag→tdiag — **early and
> thorough**. Early: most p.9.x components are not yet repos/released (tiwi
> unfinished, tie-pkg not created, tiedb not formally released), so renaming
> now costs zero migration. Thorough: one full sweep per repo, **no legacy-name
> grace period**; acceptance = grep for old names returns 0 hits (excluding
> historical commit messages). Order = smallest blast radius first (tdiag →
> tpkg → twi → tdb). Each repo = one revertible commit.

---

## 1. 原则 / Principles

* **尽早**：趁 p.9.x 组件未建仓/未发行，改名零成本——立即执行，不排期到 2026.2 尾端
* **彻底**：一次性全量改完，**不留旧名兼容期**（生态规划期无兼容包袱）
* **每仓一提交**、可回退；顺序 = 影响面从小到大

## 2. 迁移内容（每仓）/ Per-repo Migration

1. **GitHub 仓库名**：`gh repo rename tie-lang/<旧> --new-name <新>`
2. **本地目录**：`tie-repo/<旧> → tie-repo/<新>`
3. **包/模块名**：namespace / import 路径全改
4. **文档引用**：ROAD / CHANGELOG / release.md / 设计文档 / 记忆——旧名全清
5. **发行 artifact 名**：`<旧>-<版本> → <新>-<版本>`
6. **依赖声明**：其他仓 import 处全改
7. **CI/脚本**：构建脚本内的名字

## 3. 迁移顺序 / Order（影响面从小到大）

| 序 | 改名 | 现状 | 影响面 |
|---|---|---|---|
| 1 | tie-diag → **tdiag** | 已存在独立仓（文档+生成工具）| 最小（文档为主）|
| 2 | tie-pkg → **tpkg** | 未建仓（ROAD 登记）| 小（仅文档引用）|
| 3 | tiwi → **twi** | 未完成（p.9.7）| 小（ROAD/文档）|
| 4 | tiedb → **tdb** | 有 tieDB 目录 + 文档引用 | 最大（最后做最稳）|

## 4. 彻底性验收 / Acceptance

* 每仓迁移后：全仓 `grep 旧名` = **0 命中**（历史 commit 消息除外）
* 生态级验收：tie-main 全库 grep 旧名（tdb/twi/tpkg/tdiag 的旧名）= 0 命中（历史 commit 除外）
* 文档不留旧名；不设新旧并行期

## 5. 执行记录 / Execution Log

| 仓 | 状态 | 日期 | 提交 |
|---|---|---|---|
| tdiag | 待执行 | 2026-09-12 | — |
| tpkg | 待执行 | — | — |
| twi | 待执行 | — | — |
| tdb | 待执行 | — | — |

---

## 附录 / Appendix

* 术语 / Terms：改名迁移（rename migration）· 兼容期（grace period，本计划不留）· 影响面（blast radius）
* 演进：执行记录随每仓完成更新（上表）；验收通过 = 该仓迁移闭环