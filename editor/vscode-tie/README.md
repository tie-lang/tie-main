# vscode-tie — tie 语言支持

tie 语言的 VSCode 扩展：语法高亮、智能缩进、代码片段，并通过 **tsp** 语言服务器（tie 语言服务器，0-Rust 自举）提供诊断、hover、跳转定义与补全。

## 功能清单

| 功能 | 说明 |
| --- | --- |
| 语法高亮 | 关键词 / 类型 / 运算符 / 数字（含 0x 与下划线分隔）/ 字符串 / 注释 / 文件类型声明（`type tie<...>` 头部声明着色）/ 内置函数 |
| 智能缩进 | 函数 / struct / 命名空间 / 控制流行尾 `{` 自动缩进，`}` 自动对齐，`case` / `default` 自动缩进 |
| 代码片段 | `func`、`struct`、`ns-method`（命名空间方法函数）、`if` / `ifelse`、`for`（范围遍历）、`while`、`switch`、`import`、`println` |
| 诊断 | 打开 / 编辑 `.tie` 文件时，错误与纠错实时显示在「问题」面板（括号配对、未定义函数等） |
| Hover | 悬停函数显示签名（`func add(a: i64, b: i64) -> i64 {`） |

> 诊断 / hover / 跳转 / 补全均来自 tsp（tie 语言服务器，`compiler/lsp/` 全 tie 编写），扩展只负责连接与展示。

## 依赖

- **VS Code ≥ 1.75**
- **tsp**（tie 语言服务器）：扩展已内置 `vendor/tsp.exe`（0.2.0+），默认即用，无需额外安装。

## 安装

### 打包安装（vsix，推荐）

```bash
npm install
npm run compile
npx @vscode/vsce package
```

生成 `vscode-tie-0.2.0.vsix`（内含 `vendor/tsp.exe`）后，在 VS Code 扩展面板选择「从 VSIX 安装…」。

### 开发调试（F5）

1. 安装依赖并构建：

   ```bash
   npm install
   npm run compile
   ```

2. 构建 tsp（若需更新内置服务器）：

   ```bash
   cd ../..         # 仓库根
   compiler/tiec.exe compiler/lsp/server.tie -o compiler/lsp/tsp.exe
   cp compiler/lsp/tsp.exe editor/vscode-tie/vendor/tsp.exe
   ```

3. 在 VS Code 中打开 `editor/vscode-tie`，按 `F5` 启动「扩展开发宿主」，打开任意 `.tie` 文件体验。

## 配置

| 配置项 | 说明 |
| --- | --- |
| `tie.lsp.command` | 启动语言服务器的命令，数组形式 `[命令, 参数...]`。默认 `["auto"]`。 |

- **默认 `["auto"]`（推荐）**：自动探测 tsp，顺序为
  ① 扩展内 `vendor/tsp.exe` → ② 仓库 `compiler/lsp/tsp.exe` 与 `lsp/tsp.exe` → ③ `PATH` 中的 `tsp` → ④ 回退 `["tie", "--lsp"]`。
- **自定义指向**：可配置为 tsp 绝对路径，例如：

  ```json
  { "tie.lsp.command": ["F:/Projects/tie/target/release/tsp.exe"] }
  ```

  > 注意：旧版 Rust tie 的路径（如 `F:/Projects/tie/target/release/tie.exe`）已失效。
  > 若配置的路径不存在，扩展会自动回退到自动探测并输出警告。
  > 修改配置后请执行「重新加载窗口」（`Developer: Reload Window`）。

服务器启动失败时，扩展会弹出提示引导检查配置；服务器 stderr 与客户端日志见「输出 → tie」（若用 `"auto"` 且探测到 tsp，会打印 `自动探测语言服务器：...` 便于确认）。

## 开发

```bash
npm run compile   # 类型检查（tsc）+ 打包（esbuild）→ out/extension.js
npm run watch     # 增量编译（开发调试用）
```

- 源码：`src/extension.ts`（vscode-languageclient 客户端；服务器命令探测见 `readServerCommand`/`autoDetectServer`）
- tsp：`../lsp/`（tie 语言服务器，全 tie 编写：`protocol.tie`/`server.tie`），构建产物 `vendor/tsp.exe`
- 语法：`syntaxes/tie.tmLanguage.json`（TextMate 语法，顶层 scope `source.tie`）
- 语言配置：`language-configuration.json`（注释 / 括号 / 自动闭合 / onEnterRules 智能缩进）
- 片段：`snippets/tie.code-snippets`

## 协议兼容

扩展使用标准 LSP 协议（vscode-languageclient）与 tsp 后端通信，文档同步为全量模式（`textDocumentSync=1`）。tsp 冒烟测试：`compiler/lsp/lsp_smoke{1,2,3}.py`（握手 / 诊断 / hover 回环）。