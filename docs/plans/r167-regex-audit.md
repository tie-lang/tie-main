# r.1.6.10 · regex 运行期桥现状审计
## r.1.6.10 · Regex Runtime-Bridge Audit (delivered as plan / 审计+设计项)

> 范围：只审计与设计映射，**不实现**。实现为 r.1.6.11。
> Scope: audit + POSIX mapping design only, **no implementation** (that is r.1.6.11).
> 基座 base: GitHub tie-lang/tie-main `r.1` @ 13a84b6，worktree `wt-167b` 分支 `r.167-regex`。
> 平台平台目标: Linux x86_64 (glibc), `<regex.h>` regcomp/regexec/regfree。

---

## 1. 背景 / Background

正则五原语是 tie 语言底座内置（`regex_match` / `regex_find` / `regex_find_all` /
`regex_group` / `regex_replace`），调度在 `compiler/backend/irgen_expr.tie`：

- `regex_find_all` → `tig_regex_find_all` (irgen_expr.tie:2185)
- `regex_find` (2319) / `regex_replace` (2323) / `regex_group` (2327) / `regex_match` (2331) → 对应 `tig_regex_*`

每个 `tig_regex_*`（irgen_regex.tie:815–1027）先判 `rex_lit_pat(id)`：

```
func rex_lit_pat(id: i64) -> bool { return s_tags[call_arg(id, 1)] == 2 }
```

- **字面量 pattern**（`arg1` 的 type tag == 2，即字符串字面量）→ 编译器内联**纯 tie 回溯 VM**
  （`g_used_interp=false`）。
- **运行期 pattern**（非字面量，`std/xxx` 把 pattern 当参数传入）→ `rex_bridge_*` → **Rust 桥
  `tie_regex_*`**（`g_used_interp=true`）。Linux 目标无 `tie_interp.lib` → **链接被拒**。

`std/regex.tie` 是**另一条路径**：它在 std 层自研纯 tie 引擎（不调五原语），因此 `import regex`
的程序不再触桥。但其它探针（`std_httpc`/`std_net_text` 等）直接调语言内置五原语、传运行期
pattern，仍回退 Rust 桥 → Linux 阻塞。这正是本项要处理的分界。

---

## 2. 五原语精确 ABI / Five-Primitive ABI

tie 语言层签名（字节串，`s21_str_byte` / `str_sub_bytes` 按字节偏移；`arg0`=subject，`arg1`=pattern）：

| 内置 | 参数 (arg0,arg1,arg2) | 返回类型 | 语义 |
|---|---|---|---|
| `regex_match`   | `(s:str, pat:str)`        | bool | 是否在 s 中存在匹配 |
| `regex_find`    | `(s:str, pat:str)`        | str  | 第一个匹配子串；无匹配返回 `""` |
| `regex_find_all`| `(s:str, pat:str)`        | `table<string>` | 全部非重叠匹配子串表 |
| `regex_group`   | `(s:str, pat:str, k:i64)` | str  | 第 k 组子串；k==0 整体；未匹配/越界返回 `""` |
| `regex_replace` | `(s:str, pat:str, repl:str)` | str | 全部替换；repl 支持 `$N`/`$0` 捕获引用 |

Rust 桥符号名 + `llvmgen_str.tie` declare 形状（llvmgen_str.tie:527–541）：

| 桥符号 | declare 形状 | 说明 |
|---|---|---|
| `tie_regex_match`    | `declare i8 @tie_regex_match(ptr, ptr, ptr)` | 3 个 ptr；返回 i8=bool（第 3 个 ptr 是 irgen 传的 `alloca i8` 出参槽，结果以返回值 i8 为准） |
| `tie_regex_find`     | `declare ptr @tie_regex_find(ptr, ptr)`      | 返回字符串 ptr |
| `tie_regex_find_all` | `declare ptr @tie_regex_find_all(ptr, ptr)`  | 返回**表句柄，非字符串**（`is_table_bridge`=true，llvmgen_inst.tie:198–205 黑名单，禁止补头） |
| `tie_regex_group`    | `declare ptr @tie_regex_group(ptr, ptr, i64)`| 组号 i64 |
| `tie_regex_replace`  | `declare ptr @tie_regex_replace(ptr, ptr, ptr)`| |

实现出处：

- 桥调用点：irgen_regex.tie `rex_bridge_match`(707)/`find`(738)/`find_all`(751)/`group`(764)/`replace`(789)，每处先 `g_used_interp = true`。
- 端到端调度：`tig_regex_match`(815)/`find`(846)/`group`(877)/`find_all`(948)/`replace`(983)。
- 字面量内联引擎边界：`rex_lit_pat` 判 `s_tags[arg1]==2`；`rex_prelude`(479) `rx_compile`(400) 把 pattern 编译成 `g_rx_prog/g_rx_cls/g_rx_ngroups` 指令程序 + `rex_link`(457) 拷入运行时表。

---

## 3. 分界判定 / Literal-vs-Runtime Boundary

```
tig_regex_<X>(id):
    if !rex_lit_pat(id):  return rex_bridge_<X>(id)      # 运行期 → Rust 桥 → g_used_interp=true
    # else 内联纯 tie 回溯 VM (g_used_interp=false)
```

- `rex_lit_pat(id)` 只判 `s_tags[call_arg(id,1)]==2`（**pattern 参数**是否字符串字面量），与 subject 无关。
- 内联引擎支持语法子集（irgen_regex.tie:24–27 与 std/regex.tie:21–24 声明一致）：
  字面量、`.`、`[abc]` `[a-z]` `[^...]`、`\d \w \s`（+大写取反）、量词 `* + ?`（贪婪）、锚点 `^ $`、
  分组 `()`、转义字面量 `\. \\ \*` 等、交替 `|`；**逐字节匹配**。
- 局限：`{n,m}`、反向引用、前瞻/后顾、`\b`、Unicode 类、非捕获组 `(?:)` 均不支持；`(?s)` dotall 无（`.` 本就匹配换行）。

**结论**：tie 的 regex 是 **POSIX ERE 近亲子集**（非 PCRE）。其语法恰好落在 ERE 之内：
`.`、`[...]`、`^`、`$`、交替 `|`、量词 `* + ?`、捕获组 `()`、转义字面量。→ `regcomp` 用
`REG_EXTENDED` 足够，无需 `REG_ICASE`（tie 大小写敏感）等。差异仅限 tie 自创的 `\d \w \s`
速记（+大写取反）与 `\t \n \r` 转义——见 §5 预处理。

---

## 4. 安装可行性 → 跳过原型 / Prototype: Skipped on Windows

校验本机：clang 存在（`D:\LLVM\bin\clang.exe`），但 `<regex.h>` / glibc `regcomp` 在 MSVC libc
目标**不可用**（Windows `System32` 与 LLVM 资源目录均无 `regex.h`；即便有头文件，`regcomp/regfree`
是 glibc API，MSVC CRT 不提供符号）。按任务纪律**跳过 C 原型**，映射设计基于 glibc `<regex.h>`
文档，语义验证**留待 Linux CI**（r.1.6.11 实现后由 linux-r16 流水线回归）。

---

## 5. POSIX regcomp/regexec 映射设计 / Mapping Design

三 libc 符号（`regcomp`/`regexec`/`regfree`）已列入 r.1.6.16 主代理 `is_libc_sym` 统一登记，
本项不登记。建议 declare 形状（x86_64 SysV）：

```
declare i32 @regcomp(ptr, ptr, i32)                    ; (regex_t*, pattern, REG_EXTENDED)
declare i32 @regexec(ptr, ptr, i64, ptr, i32)          ; (regex_t*, string, nmatch, regmatch_t*, 0)
declare void @regfree(ptr)
```

### 5.1 pattern 预处理 / Pattern Preprocessor（把 tie 扩展 → 纯 ERE）

POSIX ERE **无** `\d \w \s \t \n \r`。glibc ERE 会把普通字符前的 `\` 视为转义该字符
（`\d`→字面 `d`，`\t`→字面 `t`）→ **语义崩坏**。故对运行期 pattern 先做一次字节级改写后
再 `regcomp`。tie 保留转义（`\. \\ \* \+ \? \( \) \[ \] \| \$ \^`）本就是 ERE 转义，原样保留：

| tie 写法 | ERE 等价（C locale） | 说明 |
|---|---|---|
| `\d` | `[[:digit:]]`         | = `[0-9]` |
| `\D` | `[^[:digit:]]`        | 大写=取反 |
| `\w` | `[[:alnum:]_]`        | = `[0-9A-Za-z_]`，逐字节 |
| `\W` | `[^[:alnum:]_]`       | |
| `\s` | `[[:space:]]`         | glibc space 集 = tie `rx_cls_space` 的 {32,9,10,13,11,12}，**完全一致** |
| `\S` | `[^[:space:]]`        | |
| `\n` `\t` `\r` | 字面换行/TAB/CR 字节 | tie `rx_emit_cchar` 处即如此 |
| 其它 `\X`（非 ERE 定义） | 当作字面 X | 与 tie 一致 |

**字符类内部** `[...]` 同样展开：`[\d]`→`[[:digit:]]`、`[\w-]`→`[_[:alnum:]-]`、
`[\n]`→含换行字节，负类 `[^...]` 同理（ERE 中 `^` 紧跟 `[` 为取反）。

预处理须注意：`]` 作首字符、`-` 的位置语义在 ERE 与 tie 略有差异（ERE 把 次位 `]`当字面、
`-` 首尾当字面），这部分按 ERE 既定规则即可，风险低。预处理是**字节级扫描**，只做字面改写，
不解析结构；改写产物仍须逐字节长度与源 pattern 等价（除被展开的速记）。

### 5.2 调用/结果转换（各原语）/ Per-Primitive Call & Result

缓冲管理（regex_t / regmatch_t）：
- `regex_t`：opaque 结构，x86_64 glibc 为固定尺寸（`struct re_pattern_buffer` + 成员）。
  IR 侧用固定大小字节 alloca 承载（建议按 glibc 头实测尺寸取保守常量，或放宽到 ≥512B 上界，
  r.1.6.11 实现时 pin）。备选：为 Linux 编一个**小 C shim**（放进 trm/native 后端）封装
  regcomp/regexec，免 IR 硬编码结构尺寸——两者皆零 Rust，语义相同；路线优先级留给 r.1.6.11 纪要。
- `regmatch_t`：glibc `{ regoff_t rm_so; regoff_t rm_eo; }`，大小 2×regoff_t；`regoff_t` 实现
  相关（glibc 通常 32bit → 8B/项）。nmatch = `re_nsub + 1`；`re_nsub` 由 `regcomp` 写入
  `regex_t`，IR 侧读取需结构偏移常量（或 shim 回传）。

各原语（`regcomp(&re, pre, REG_EXTENDED)` 一次，成功 ret==0 才继续；失败语义同 tie 编译失败）：

- **match**：`regexec(&re, s, nmatch, pm0, 0)`。ret==0 → true，`=REG_NOMATCH(1)` → false。
  返回 i8。`(s,pat)` 两参；一次性 compile+exec。不打 out 出参槽。
- **find**：regmatch_t[1]；`regexec` 命中 → 返回 `sub(s, pm[0].rm_so, pm[0].rm_eo)`；否则 `""`。
- **group(s,pat,k)**：`regexec` 命中；`k==0` → 整体 `[rm_so0,rm_eo0]`；`k>=1`：
  `rm_so_k==-1`（该组未参与匹配）→ `""`；否则 `sub(s, rm_so_k, rm_eo_k)`；
  `k>re_nsub` → `""`。**rm_so/rm_eo 提取**：`regmatch_t*` 数组下标访问（字节偏移）。
- **find_all(s,pat)**：`find_all` 匹配循环，把每次命中子串 `sub(s, rm_so, rm_eo)` push 进返回表。
- **replace(s,pat,repl)**：匹配循环，前缀/替换/尾缀拼接进 StringBuilder；`repl` 扫 `$N/$0` →
  `sub(s, rm_so_N, rm_eo_N)` 或整体，与 irgen `rex_emit_repl` 一致。

### 5.3 匹配循环 / Find-all & Replace loop（含空匹配防死循环）

`regexec` 的 `string` 是每次扫描起点。为复用一次编译、循环取后续匹配：

```
last = 0; start = 0
loop:
    rc = regexec(&re, s+start, nmatch, pm, 0)
    if rc != 0: break
    m = pm[0]; eo = m.rm_eo - (m.rm_eo - m.rm_so 为空时? m.rm_so : eo)   # 见下
    # find_all: push sub(s, rm_so, rm_eo)   replace: append sub(last..rm_so)+repl
    if rm_eo == rm_so:  start = rm_eo + 1    # 空匹配 → 前进 1 字节，镜像 irgen tig_select 空推进
    else:               start = rm_eo
    if start > slen: break
# 尾缀 append sub(last..slen)
```

> 关键；`regexec` 内部已做“左端优先”扫描，返回的就是指定起点起的最左匹配，因此循环里无需再
> 逐起点重试——irgen 内联引擎的“逐 start 试匹配”由 `regexec` 的搜索取代，效率反而更高（一次性）。

**/ 性能纪律**：find_all/replace 拼接一律用 StringBuilder（`s21_sb_append` / `s21_sb_append_byte`），
禁止 `out += x` 逐字符（p.6.3 教训，且 tie 无 GC 会 O(n²)+内存爆炸）；`regcomp` **每次内置调用
只一次**、find_all/replace 循环内复用，禁止每匹配重复编译。

---

## 6. 语义差异与回归风险 / Semantic Divergence & Regression Risk

1. **左端最左 vs POSIX 左端最长（首要风险）**：tie 内联引擎是 leftmost-**first**（贪婪优先，
   交替 `a|ab` 于 "ab" → `a`）；glibc POSIX ERE 是 leftmost-**longest**（`a|ab` → `ab`）。
   仅影响含歧义交替/量词的 pattern，探针常用 pattern 多为无歧义字面，风险低但需 r.1.6.11 用例覆盖。
2. **`.` 与换行 / dotall 等价**：tie `.`（RX_ANY）匹配任意字节含 `\n`；glibc **不设 REG_NEWLINE**
   时 `.` 也匹配换行 → **语义一致**。注意**不得**设 `REG_NEWLINE`（否则 `.` 与 `^ $` 行为全变）。
3. **锚点范围 / find_all 中 `^ $`**：tie 的 `^`/`$` 仅对**整体串**起止（ATSTART pos==0 /
   ATEND pos==slen）。`regexec` 的锚以**传入的 string 基址**计——find_all 循环推进 start 后，
   `^` 会退化为“片段起点”。绝大多数 find_all 不以 `^` 开头，可接受；具文档化差异，r.1.6.11 若
   需严格保真可对 `^`-锚 pattern 单跑一次 regexec(pattern 锚整体)、其余走循环。
4. **`\d \w \s` 等速记必须预处理**，否则 glibc 当字面字符 → 静默错判（§5.1）。
5. **空匹配**：tie 内联对零长匹配前进 +1（irgen `tig_select_i`）；映射循环须同样处理，否则死循环。
6. **组未参与匹配**：tie 槽初始 0→`""`；POSIX `rm_so==-1` → 映射转 `""`，语义对齐。
7. **大小写/Unicode**：tie 逐字节、大小写敏感；glibc 在 UTF-8 C locale 下 `.`/类按整字符计但
   rm_so/rm_eo 仍是字节偏移。仅用 C/byte 语义，避开 locale 类 `[:alpha:]` 多字节折叠差异；tie
   无大小写折叠需求。

---

## 7. 实现建议 / Implementation Notes (for r.1.6.11)

- 落点：`compiler/backend/irgen_regex.tie`。在每个 `tig_regex_*` 的 `rex_bridge_*` 调用**之前**
  插入 `if tig_is_linux() { return rex_linux_<X>(id) }`（或把 Linux 分支并入 `rex_bridge_*`）。
- **`g_used_interp` 不得再置位**：Linux 分支走内联 IR + libc `regcomp/regexec/regfree` 直调，
  与 p.6.4 内联系列一致（其余非 Linux 目标保留 `rex_bridge_*` 的 `g_used_interp=true` 现状）。
- `pattern` 预处理（§5.1）作为运行期的字节级改写函数；字面量 pattern 走内联 VM 不受影响。
- `re_nsub`/结构尺寸：Linux 实现需 pin glibc `regex_t.size`/`regmatch_t` 布局；建议立小 C shim
  承担 regcomp→(regex_t 句柄, re_nsub) 与 regexec→regmatch_t[]，盾住 IR 结构偏移脆弱性
  （r.1.6.16 只登记符号，shim 属 trm/native，不算 Rust 桥）。
- 探针：Linux CI 以 `std_httpc`/`std_net_text` 走过五原语运行期路径；`examples/regex_demo.tie`
  回归（r.1.6.6 已 97 PASS/0 FAIL，需在 Linux 回归豁免表核对 regex 探针不再 SKIP）。

---

## 8. 参考文件 / References

- `compiler/backend/irgen_regex.tie` —— 内联 VM + 桥分界（`rex_lit_pat`/`rex_bridge_*`/`tig_regex_*`/`rex_prelude`/`rex_emit_repl`）
- `compiler/backend/llvmgen_str.tie:527–541` —— 五桥 declare 形状
- `compiler/backend/llvmgen_inst.tie:198–205` —— `is_table_bridge`（find_all 返回表，禁止补头）
- `compiler/backend/irgen_expr.tie:2185,2319–2331` —— 五内置调度
- `compiler/backend/irgen_expr.tie:6422` —— `tig_is_linux()`
- `compiler/backend/irgen.tie:529` —— `is_libc_sym()`（regcomp/regexec/regfree 由 r.1.6.16 登记）
- `std/regex.tie` —— std 层纯 tie 引擎（参考语义/语法契约，非本项改造对象）