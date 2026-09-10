# r.1.6.12 regex 运行期 pattern 探针目录

`regex_runtime_linux_probe.tie` 验收 r.1.6.11（trm-lite `trm_lite_linux.a` 新增
`linux_compat_regex.o` 成员提供的 Rust 桥同名 `tie_regex_*` 五原语 POSIX C 实现）。

所有 pattern 以**变量**传入（非字面量）→ `rex_lit_pat` 判 false → 走 `rex_bridge_*`
→ 符号 `tie_regex_*`（桥路径），避开字面量内联 VM。

## 验证结论（本机 = Windows 宿主，Linux 交叉）

- **Windows 本机运行**：`tie-main\target\release\tie_interp.lib` **不存在** → 链接报
  `undefined tie_regex_*`（且上游 g_used_interp 拦截）。这是**预期**：本探针服务 Linux
  桥验收；Windows 需先构建 tie_interp.lib。
- **Linux 交叉**：`tiec regex_runtime_linux_probe.tie --target linux-x64 -o <tmp>`，
  设 `TIE_TRM_LITE_LIB` 指向 `wt-167b-trm\trm_lite_linux.a`。在 **r.1.6.16 登记前**，
  `rex_bridge_*` 仍无条件置 `g_used_interp=true` → `link_exe` 报
  **"Linux 目标暂不支持 tie-interp 桥"** 屏障（need_interp 分支，toolchain.tie:232）。
  该屏障属于 **r.1.6.16 主代理**：在 `is_libc_sym` 登记 `tie_regex_match/find/`
  `find_all/group/replace` 五符号后，`tig_ext_call_typed` 对它们不再置
  `g_used_interp` → 屏障消失，链接错误收窄为 **仅缺 Linux CRT**（crtn.o/-lc，需 Linux
  目标机/CI 环境）。**本探针不修改 is_libc_sym**（留给 r.1.6.16）。
- 桥符号/ABI 层自洽性（在无 Linux CRT 的前提下）已单独验证：`linux_compat_regex.o`
  五桥 + 对 `tl_tbl$tbl_new` 的引用在 `trm_lite_linux.a` 内由 `tl_runtime.o` 解析；
  手动 clang 链接仅剩 CRT/pthread 缺失，无 `undefined tie_regex_*`、无重复定义。

## 覆盖

match / find / find_all（多匹配 + 长文本 ×1000 线性）/ group（$0、k=1/2、越界=空）/
replace（`\d` 速记、`\s` 速记、`$2/$1` 重排、`$0` 整体）。pattern 均运行期变量，
确保走桥。空匹配推进与缓冲预分配由桥内实现保证（见 linux_compat_regex.c）。