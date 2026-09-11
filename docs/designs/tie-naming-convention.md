# tie 生态命名规范
*EN: tie Ecosystem Naming Convention*

**日期** / Date: 2026-09-12 · **类型** / Type: 生态规范（跨领域；统一命名，解决 tiec/tiedb 与 tiu/t3d 等混乱）
**依据** / Basis: 用户统一命名要求（2026-09-12 定）· 全量改名 + 语义缩写/造词 + **tie-dev（skill）保留 tie- 前缀**（用户否决 tdev）
**关联** / Related: ROAD p.9.x 各组件仓 · tie-format-api-family.md（生态格式家族）· tie-main/tie-lang
**版本** / Version: v0.2（2026-09-12 tie-diag→tdiag 定案归组件仓）· v0.1 初稿

> EXEC BRIEF: Unifies tie ecosystem naming by **entity type**, ending the
> tiec/tiedb-vs-tiu/t3d inconsistency. Rule: `tie` = the language itself and
> its indivisible attachments (the tiec compiler) — brand, kept as-is; `t` =
> independent component repos (libraries/engines/frameworks/tools/services) —
> lowercase suffix, no hyphen, semantic abbreviation or coined word; `tie-` =
> non-component entities (skills like tie-dev, org/docs words) — kept.
> Full rename applies to component repos only: tiedb→tdb, tiwi→twi,
> tie-pkg→tpkg, tie-diag→tdiag. Skills/org/main-repo are exempt.

---

## 1. 分类规则 / Rules by Entity Type

| 实体类型 | 规则 | 现有 | 改名 |
|---|---|---|---|
| 语言本体 | `tie` 保留 | tie | — |
| 语言直接附属（编译器）| `tiec` 保留（tie+compiler 品牌，与语言一体）| tiec | — |
| 组件仓（库/引擎/框架/工具/服务）| `t + 词缀`（小写 · 无连字符 · 语义缩写或造词）| tiu/tink/trm/tsp/t3d/tge/trg/taud/tanim/tphy/tedit/tac/tsci/tstat/tsim/tgeo/timg/tvid/tvfx/tplot | **tiedb→tdb** · **tiwi→twi** · **tie-pkg→tpkg** · **tie-diag→tdiag** |
| 技能（skill）| `tie-` 保留（不套组件规则）| tie-dev | — |
| 组织/主仓 | `tie-lang` / `tie-main` 保留 | tie-lang/tie-main | — |

## 2. 核心语义区分 / Core Distinction

* **`tie`** = 语言本体及**直接一体物**（编译器 tiec）——语言不可分割的品牌
* **`t`** = **独立组件**——可独立发行/使用的仓（数据库/安装器/渲染/音频/物理/编辑器/生成器…）
* **`tie-`** = **非组件实体**（skill 技能包 / 组织名 / 文档词）——语义上是 tie 的一部分，不套组件规则

## 3. 词缀规则 / Suffix Rules

* **语义缩写**：db=数据库 · aud=audio · anim=animation · phy=physics · edit=editor · ci=compiler?（tiec 保留故不用）· stat=statistics · sci=science · sim=simulation · geo=geometry · img=image · vid=video · vfx=特效 · plot=绘图 · tac=api compiler（造词）
* **造词**：ink=互联（tink，tinker 造词）· trg=render graph（缩写）
* **数字例外**：t3d（已定案，t+3d）
* **变体后缀**：trm-lite（trm 轻量变体，`-lite` 后缀保留）
* 小写 · 无连字符 · 2–5 字母

## 4. 改名执行 / Rename Execution

* **本轮改名的组件仓**（不一致项 → t 前缀）：tiedb→tdb · tiwi→twi · tie-pkg→tpkg · **tie-diag→tdiag**（2026-09-12 定案：归组件仓）
* 已符合的组件仓（不动）：tiu/tink/trm/tsp/trm-lite/t3d/tge/trg/taud/tanim/tphy/tedit/tac/tsci/tstat/tsim/tgeo/timg/tvid/tvfx/tplot
* 保留（不套组件规则）：tie / tiec / tie-dev / tie-lang / tie-main
* 改名影响：仓库名 · 文档 · 发行 artifact · 依赖声明——**逐仓迁移，一次性改名不并行新旧**

## 5. 边界说明 / Boundary Notes

* **tie-diag → tdiag 已定案**（2026-09-12）：诊断配套归**组件仓**（含生成工具，可独立发行），按规则改名 tdiag
* skill（tie-dev）：技能包，**永不套组件规则**（用户明确否决 tdev）

## 6. 未讨论项（不落为结论） / Not Yet Concluded

* 改名**迁移计划**（逐仓时序/兼容处理）· 旧名兼容期（文档是否标注旧名）· 发行 artifact 命名随之变更的细节——**均未推演**，推演完成后补章

---

## 附录 / Appendix

* 术语 / Terms：组件仓（component repo，独立发行单元）· 词缀（suffix，语义缩写/造词）· 直接一体物（indivisible attachment，如编译器与语言）
* 演进：本文档为命名规范；改名执行按 §4 逐仓迁移