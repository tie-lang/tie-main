# Keel Architecture — Core Mechanism Summary

> **Keel（龙骨）** is the codename for the tie 2026.2 compiler architecture, corresponding to the release codename **Drydock（干船坞, 2026.2）**. Official designation: the complete compiler restructure enters the **Keel Architecture** era.
>
> Sources: [tie 全平台插件化设计](docs/superpowers/specs/2026-08-29-plugin-kernel-design.md) · [plugin-kernel 实施计划](docs/plans/plugin-kernel.md) · [tieir 格式](docs/plans/tieir-format.md) · [发行版设计规划 · 代号表](docs/release.md)

**Keel（龙骨）** is a **unified-registry microkernel**: the compiler is completely restructured so that the core retains *only mechanisms* — a loader, a universal registry, an auditor, and an execution skeleton — carrying **zero behavior** of its own. Every behavior in the platform is a *registration item*.

## Core Kernel (Mechanism Layer Only)

* `boot` — bootstrap loader (two-phase registration; built-ins registered first)
* `registry` — universal registry mapping (name/field → kind → implementation reference)
* `auditor` — security auditor (field whitelist / unknown-field rejection / version + hash + signature verification)
* `executor` — pipeline execution skeleton (reads registered pipeline data, dispatches registered passes)
* tieir reader + dispatch tables + columnar / interner / types + TSHA1 hash primitive base

## Registration Model

Every behavior is a registration item carrying:

* `id` (globally unique, e.g. `pkg:my_pkg::pass_inliner`) + `kind` (pass | pipeline | builtin | role | cli | lib | …)
* `version` (semver) + `tie` (language-version constraint) + `impl` (fn / data table / tieir reference / port export) + `deps` + `meta` (source priority + registration order)

Three invariants:

1. **id is stable and decoupled from internal indices** — the outside world references modules only by `id+version`; same-id/same-version is idempotent; same-id/different-version is arbitrated by priority (built-in < config < project < dependency package), with explicit `dependencies` constraints taking precedence.
2. **Version gating** — the auditor rejects IR-version mismatch, unsatisfied language-version constraints, and un-resolvable dependency graphs.
3. **id/version themselves are audited** — segment-name whitelist (malicious segments like `hook/script/exec` banned), valid semver, unknown fields rejected.

## Bootstrapping Safety

The built-in bootstrap set (default pipeline definition + builtin function family + built-in role table + CLI skeleton) is embedded in the binary as a *startup plugin*; boot registers it first. `tiec` compiles itself with **no external plugins** — the registration sequence proceeds normally and self-hosting is safe. External plugins are just more registration items and can never preempt already-registered built-ins (first-registered wins).

## Pipeline Extensibility

The pipeline itself is a registered item (`pipeline:default` = an ordered list of pass references). External plugins declare `extends: pipeline:default, anchor: <pass>` to insert/replace passes at specified anchors — through the same registration and audit channel. The core skeleton only reads pipeline data → resolves pass references → executes.

## Distribution

* **tieir** (binary IR distribution): module header → type table → symbol table → columnar IR body → export table → span/docs segment; consumers load it **without running the frontend**.
* **Config forms**: `tie:data` (plaintext, developer-facing) → `tie:zd` (compressed binary variant via `tie publish`); the loader treats both identically and audits the unpacked content the same way.

## Security Model (two orthogonal axes)

* **Fingerprint (what was shipped)** — anti-tamper, no central authority: per-file `tsha1f` + package-tree-root `tsha1x`, written into `tie.pkg hash` + `tie.lock`; the loader recomputes and compares.
* **Credential (who shipped it)** — decentralized authentication: the package carries `publisher` + `pubkey` (Ed25519) + `pubkey_fp` (trust anchor) + `package.sig` (signature over the tree root).

Full audit chain (any link failing → rejection):

1. fingerprint-tree recomputation → 2. in-package signature verification → 3. fp consistency against the `tie.lock` anchor (TOFU; first load prompts trust confirmation) → 4. IR version → 5. id/version validity → 6. field whitelist → 7. dependency resolution → 8. registration-conflict arbitration.

Safety holds even with **no official registry**: an attacker without the publisher's private key cannot forge a signature matching an anchored fp; key rotation simply triggers re-confirmation of the new fp.