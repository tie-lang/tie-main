# gen-diagcodes.ps1 —— 诊断标号目录生成器（p.6.9.15）
# ============================================================
# 扫描 tiec 编译器源码（compiler/**/*.tie + prep/pkg/repl），抽取全部诊断消息
# 字面量，归一化折叠（ASCII 串 → '%'）为稳定 key，按来源登记家族，生成：
#   1) compiler/frontend/diagcode_cat.gen.tie —— 目录数据（key→code→name）
#   2) <root>/diagdocs/*.md —— 各家族文档骨架
#   3) <root>/diagdocs/diagcodes.json —— 机器可读清单
#
# key 归一化（与运行时 compiler/frontend/diagcode.tie 完全一致）：
#   - 连续可折叠 ASCII（0x21..0x7E）折叠为单个 '%'
#   - 中文/空白原样保留
# 标号规范（用户定稿）：五位纯序号 `E` + 5 位数字（E00001 起全局连续）；
# 家族（词法/语法/语义/运行时/CLI/后端/REPL/LSP/内部）仅记入 JSON 的 family
# 字段与文档，不编码进标号。
#
# 用法：.\scripts\gen-diagcodes.ps1 [-RepoRoot <根>] [-OutDir <输出目录>]

param(
    [string]$RepoRoot = "f:\Projects\tie-repo\tie-main",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
if ($OutDir -eq "") { $OutDir = $RepoRoot }

# ---------- 家族映射 ----------
function Get-Family([string]$path, [string]$key) {
    $rel = $path.Substring($RepoRoot.Length).Replace("\", "/").ToLower()
    if ($key.StartsWith("内部错误") -or $key.Contains("编译器内部错误")) { return 9 }
    if ($key.StartsWith("运行时错误") -or $key.StartsWith("运行时")) { return 4 }
    if ($key.StartsWith("repl ") -or $key.Contains("repl v1")) { return 7 }
    if ($rel -match "lex") { return 1 }
    if ($rel -match "/(parser|pst|pexpr|pstmt|pnames|putil|errors|error_driver)\.tie") { return 2 }
    if ($rel -match "frontend/") { return 3 }
    if ($rel -match "/interp/") { return 4 }
    if ($rel -match "/(driver|config|mode|tdzd|zdwrite)\.tie") { return 5 }
    if ($rel -match "/(backend|middle|proto)") { return 6 }
    if ($rel -match "/lsp/") { return 8 }
    if ($rel -match "/(repl|prep|pkg)") { return 7 }
    return 5
}

# ---------- 归一化折叠：连续可折叠 ASCII 运行 → 单个 '%' ----------
# 定义（与运行时 compiler/frontend/diagcode.tie 完全一致）：按「字符（码点）」遍历，
# 码点在 0x20..0x7E（含空格）的连续运行折叠为一个 '%'；其余字符原样保留。
function Fold-Ascii([string]$s) {
    if ($s -eq "") { return "" }
    $sb = [System.Text.StringBuilder]::new()
    $inFold = $false
    foreach ($ch in $s.ToCharArray()) {
        $cp = [int]$ch
        if ($cp -ge 0x20 -and $cp -le 0x7E) {
            if (-not $inFold) { [void]$sb.Append('%'); $inFold = $true }
        } else {
            $inFold = $false
            [void]$sb.Append($ch)
        }
    }
    return $sb.ToString()
}

# ---------- 解析一条拼接语句：字面段数组 + 插值个数 ----------
function Parse-Concat([string]$code, [int]$startIdx) {
    $n = $code.Length
    $literals = [System.Collections.Generic.List[string]]::new()
    $i = $startIdx
    while ($true) {
        while ($i -lt $n -and ($code[$i] -eq ' ' -or $code[$i] -eq "`t" -or $code[$i] -eq "`n" -or $code[$i] -eq "`r")) { $i++ }
        if ($i -ge $n -or $code[$i] -ne '"') {
            # 语句结束（最后一个插值之后）→ 返回已收集的字面段
            if ($literals.Count -gt 0) { break }
            return $null
        }
        $seg = [System.Text.StringBuilder]::new()
        $i++
        $closed = $false
        while ($i -lt $n) {
            $ch = $code[$i]
            if ($ch -eq '\') {
                if ($i + 1 -lt $n) {
                    $nx = $code[$i + 1]
                    if ($nx -eq 'n') { [void]$seg.Append("`n"); $i += 2; continue }
                    if ($nx -eq 't') { [void]$seg.Append("`t"); $i += 2; continue }
                    if ($nx -eq 'r') { [void]$seg.Append("`r"); $i += 2; continue }
                    if ($nx -eq '"') { [void]$seg.Append('"'); $i += 2; continue }
                    if ($nx -eq '\') { [void]$seg.Append('\'); $i += 2; continue }
                }
                [void]$seg.Append($ch); $i++
                continue
            }
            if ($ch -eq '"') { $closed = $true; $i++; break }
            [void]$seg.Append($ch); $i++
        }
        if (-not $closed) { return $null }
        $literals.Add($seg.ToString())
        while ($i -lt $n -and ($code[$i] -eq ' ' -or $code[$i] -eq "`t")) { $i++ }
        if ($i -ge $n) { break }
        $c = $code[$i]
        if ($c -eq ';' -or $c -eq ')' -or $c -eq ',') { break }
        if ($c -ne '+') { break }
        # 跳过 EXPR 至下一个顶层 '+'
        $i++
        $depth = 0; $inStr = $false
        while ($i -lt $n) {
            $cc = $code[$i]
            if ($inStr) {
                if ($cc -eq '\') { $i += 2; continue }
                if ($cc -eq '"') { $inStr = $false }
                $i++; continue
            }
            if ($cc -eq '"') { $inStr = $true; $i++; continue }
            if ($cc -eq '(' -or $cc -eq '[') { $depth++ }
            elseif ($cc -eq ')' -or $cc -eq ']') { if ($depth -gt 0) { $depth-- } }
            elseif ($cc -eq '+' -and $depth -eq 0) { $i++; break }
            $i++
        }
    }
    if ($literals.Count -eq 0) { return $null }
    return $literals.ToArray()
}

# ---------- 消息名：首个「期望 」/「：」/「:」前截断 ----------
function ShortName([string]$key, [string[]]$literals) {
    # 插值边界以 '?' 占位（仅文档用途；运行时 name_of 用格式化后的完整消息切分）
    $k = (($literals -join '?') -replace "\?+", "?").Trim()
    foreach ($marker in @("期望 ", "：")) {
        $idx = $k.IndexOf($marker, [System.StringComparison]::Ordinal)
        if ($idx -gt 0) { return ($k.Substring(0, $idx)).TrimEnd('：', ':', ' ') }
        if ($idx -eq 0) { break }
    }
    return $k
}

function Add-Key([hashtable]$map, [string]$key, [int]$fam, [string]$name, [string]$src, [string]$tpl, [string[]]$lits) {
    if ($key.Length -eq 0) { return }
    if (-not $map.ContainsKey($key)) {
        $map[$key] = @{ Family = $fam; Name = $name; Src = $src; Template = $tpl; Literals = $lits }
    }
}

# ---------- 扫描 ----------
$exeKeys = @{}
$files = Get-ChildItem (Join-Path $RepoRoot "compiler") -Recurse -Filter "*.tie"
foreach ($extra in @("prep", "pkg", "repl")) {
    $p = Join-Path $RepoRoot $extra
    if (Test-Path $p) { $files += Get-ChildItem $p -Recurse -Filter "*.tie" }
}

$varRe = '(?:sm_err_msg|g_err|c_err_msg|g_role_err|err_msg|tc_err_msg|errtxt|p_err_msg|role_err|e_msg|msg_err)\s*=\s*"'
$retRe = '(?m)^(\s*return\s+)"'

foreach ($f in $files) {
    $text = [System.IO.File]::ReadAllText($f.FullName)
    $rel = $f.FullName.Substring($RepoRoot.Length).Replace("\", "/")
    # 1) 赋值语句
    foreach ($m in [regex]::Matches($text, $varRe)) {
        $start = $m.Index + $m.Length - 1
        if ($start -lt 0 -or $start -ge $text.Length -or $text[$start] -ne '"') { continue }
        $lits = Parse-Concat $text $start
        if ($lits -eq $null) { continue }
        $key = Fold-Ascii ($lits -join '%')
        if ($key -eq "") { continue }
        $key = $key -replace "%{2,}", "%"
        $fam = Get-Family $f.FullName $key
        $name = ShortName $key $lits
        Add-Key $exeKeys $key $fam $name $rel ($lits -join " <...> ") $lits
    }
    # 2) errors.tie 等 return "..." 消息构建器
    if ($f.Name -match 'errors\.tie|putil\.tie|parser\.tie|pstmt_top\.tie|lex_scan\.tie') {
        foreach ($m in [regex]::Matches($text, $retRe)) {
            $start = $m.Index + $m.Length - 1
            $lits = Parse-Concat $text $start
            if ($lits -eq $null) { continue }
            $key = Fold-Ascii ($lits -join '%')
            if ($key -eq "") { continue }
            $key = $key -replace "%{2,}", "%"
            $fam = Get-Family $f.FullName $key
            $name = ShortName $key $lits
            Add-Key $exeKeys $key $fam $name $rel ($lits -join " <...> ") $lits
        }
    }
    # 3) panic 消息（内部错误）
    foreach ($m in [regex]::Matches($text, 'panic\("')) {
        $start = $m.Index + $m.Length - 1
        $lits = Parse-Concat $text $start
        if ($lits -eq $null) { continue }
        $key = Fold-Ascii ($lits -join '%')
        if ($key -eq "") { continue }
        $key = $key -replace "%{2,}", "%"
        $name = ShortName $key $lits
        Add-Key $exeKeys $key 9 $name $rel ($lits -join " <...> ") $lits
    }
    # 4) 消息表（errors.tie 等：table_push(<全局>, "<中文消息>")）——消息文本
    #    存在懒构建数据表（非 return 字面量），按「含非 ASCII 的推送字面量」捕获。
    if ($f.Name -match 'errors\.tie') {
        foreach ($m in [regex]::Matches($text, 'table_push\([a-zA-Z_][a-zA-Z0-9_]*,\s*"')) {
            $start = $m.Index + $m.Length - 1
            $lits = Parse-Concat $text $start
            if ($lits -eq $null) { continue }
            $lit0 = [string]$lits[0]
            if ($lit0 -match '[\u0080-\uFFFF]') {
                $key = Fold-Ascii ($lits -join '%')
                if ($key -eq "") { continue }
                $key = $key -replace "%{2,}", "%"
                $fam = Get-Family $f.FullName $key
                $name = ShortName $key $lits
                Add-Key $exeKeys $key $fam $name $rel ($lits -join " <...> ") $lits
            }
        }
        # 4b) 消息表字面量：var <g>: table<string> = [ "<中文>", ... ]（errors.tie 的
        #     ensure_msg 数据表；err_keys 为英文名会被非 ASCII 过滤掉）
        foreach ($m in [regex]::Matches($text, 'var [a-zA-Z_][a-zA-Z0-9_]*: table<string> = \[')) {
            $i = $m.Index + $m.Length - 1   # 定位到 '['
            $n = $text.Length
            $i++
            while ($i -lt $n) {
                while ($i -lt $n -and ($text[$i] -eq ' ' -or $text[$i] -eq "`t" -or $text[$i] -eq "`n" -or $text[$i] -eq "`r" -or $text[$i] -eq ',')) { $i++ }
                if ($i -ge $n -or $text[$i] -eq ']') { break }
                if ($text[$i] -ne '"') { $i++; continue }
                $lits = Parse-Concat $text $i
                if ($lits -eq $null) { break }
                $lit0 = [string]$lits[0]
                if ($lit0 -match '[\u0080-\uFFFF]') {
                    $key = Fold-Ascii ($lits -join '%')
                    if ($key -ne "") {
                        $key = $key -replace "%{2,}", "%"
                        $fam = Get-Family $f.FullName $key
                        $name = ShortName $key $lits
                        Add-Key $exeKeys $key $fam $name $rel ($lits -join " <...> ") $lits
                    }
                }
                # 前进到该字面量结束（Parse-Concat 之后 $i 未知，直接找下一个引号/逗号）
                while ($i -lt $n -and $text[$i] -ne ',' -and $text[$i] -ne ']') { $i++ }
            }
        }
    }
}

# 手工补充（静态 CLI 消息）
$manual = @(
    @{ Key = "参数错误。输入 tiec --help 查看用法。"; Name = "参数错误"; Fam = 5 },
    @{ Key = "文件类型声明错误"; Name = "文件类型声明错误"; Fam = 5 },
    @{ Key = "构建配置加载失败"; Name = "构建配置加载失败"; Fam = 5 },
    @{ Key = "tieir 读取失败"; Name = "tieir 读取失败"; Fam = 6 },
    @{ Key = "compress-data 失败"; Name = "compress-data 失败"; Fam = 5 },
    @{ Key = "动态库模式错误"; Name = "动态库模式错误"; Fam = 5 }
)
foreach ($mm in $manual) {
    Add-Key $exeKeys $mm.Key $mm.Fam $mm.Name "(manual)" $mm.Key @($mm.Key)
}

# ---------- 排序与分配标号 ----------
# 注意：tie 运行时按 UTF-8 字节序比较（strcmp），目录必须按**字节序**排序，
# 不能用 Sort-Object 的区域语言排序（中文按拼音会错序 → 二分查表失配）。
# 标号规范（用户定稿）：**五位纯序号**——`E` + 5 位全局连续数字（E00001 起，
# 按字节序递增），家族信息不编码进标号（保留在 JSON family 字段与文档）。
$sorted = @($exeKeys.Keys)
[System.Array]::Sort($sorted, [System.StringComparer]::Ordinal)
$map = @{}
$seq = 0
foreach ($key in $sorted) {
    $seq++
    $map[$key] = "E" + $seq.ToString("D5")
}

# ---------- 前缀规则（插值消息：运行时值可能含中文/空格，整串无法精确命中）----------
# 规则 = 前 1~2 个字面段（折叠后）作为归一化前缀；无插值消息也建前缀（CLI 常在
# 消息后追加详情，如 "文件类型声明错误: <detail>"）。取「最长前缀命中」：
# exact 优先、前缀兜底。
$pfx = @{}   # prefix -> code（同一 prefix 归并；首个登记优先）
$pfxCode = @{}
foreach ($key in $sorted) {
    $lits = $exeKeys[$key].Literals
    if ($lits.Count -eq 0) { continue }
    $p0 = Fold-Ascii ([string]$lits[0])
    if ($p0 -eq "") { continue }
    if ($lits.Count -ge 2) {
        $p1 = Fold-Ascii ([string]$lits[1])
        $p = $p0 + "%" + $p1
        $p = $p -replace "%{2,}", "%"
    } else {
        $p = $p0
    }
    if (-not $pfx.ContainsKey($p)) {
        $pfx[$p] = $exeKeys[$key].Name
        $pfxCode[$p] = $map[$key]
    }
}

# ---------- 输出目录数据文件 ----------
$catFile = Join-Path $RepoRoot "compiler\frontend\diagcode_cat.gen.tie"
$sb = [System.Text.StringBuilder]::new()
[void]$sb.AppendLine("type tie<class>")
[void]$sb.AppendLine("// compiler/frontend/diagcode_cat.gen.tie —— 诊断标号目录（p.6.9.15 生成文件，勿手改）")
[void]$sb.AppendLine("// 生成：scripts/gen-diagcodes.ps1；exact $($sorted.Count) 条 + prefix $($pfxCode.Count) 条；运行时归一化后二分查表。")
[void]$sb.AppendLine("// 标号规范：五位纯序号 E+5 位（E00001 起全局连续）；家族仅记 JSON family/文档，不编码进标号。")
[void]$sb.AppendLine("var cat_keys: table<string>;")
[void]$sb.AppendLine("var cat_codes: table<string>;")
[void]$sb.AppendLine("var pfx_keys: table<string>;")
[void]$sb.AppendLine("var pfx_codes: table<string>;")
[void]$sb.AppendLine("namespace diagcat {")
[void]$sb.AppendLine("pub func ensure() {")
[void]$sb.AppendLine("    if len(cat_keys) > 0 {")
[void]$sb.AppendLine("        return")
[void]$sb.AppendLine("    }")
[void]$sb.AppendLine("    cat_keys = table_new_string()")
[void]$sb.AppendLine("    cat_codes = table_new_string()")
[void]$sb.AppendLine("    pfx_keys = table_new_string()")
[void]$sb.AppendLine("    pfx_codes = table_new_string()")
foreach ($key in $sorted) {
    $code = $map[$key]
    $escKey = $key.Replace("\", "\\").Replace('"', '\"')
    [void]$sb.AppendLine("    table_push(cat_keys, `"$escKey`")")
    [void]$sb.AppendLine("    table_push(cat_codes, `"$code`")")
}
$pfxSorted = @($pfxCode.Keys)
[System.Array]::Sort($pfxSorted, [System.StringComparer]::Ordinal)
foreach ($p in $pfxSorted) {
    $escP = $p.Replace("\", "\\").Replace('"', '\"')
    [void]$sb.AppendLine("    table_push(pfx_keys, `"$escP`")")
    [void]$sb.AppendLine("    table_push(pfx_codes, `"$($pfxCode[$p])`")")
}
[void]$sb.AppendLine("}")
[void]$sb.AppendLine("// 二分查表：key → code；未命中返回空串。")
[void]$sb.AppendLine("pub func lookup(key: string) -> string {")
[void]$sb.AppendLine("    ensure()")
[void]$sb.AppendLine("    var lo: i64 = 0")
[void]$sb.AppendLine("    var hi: i64 = len(cat_keys) - 1")
[void]$sb.AppendLine("    while lo <= hi {")
[void]$sb.AppendLine("        var mid = (lo + hi) / 2")
[void]$sb.AppendLine("        if cat_keys[mid] == key { return cat_codes[mid] }")
[void]$sb.AppendLine("        if cat_keys[mid] < key { lo = mid + 1 } else { hi = mid - 1 }")
[void]$sb.AppendLine("    }")
[void]$sb.AppendLine("    return `"`"")
[void]$sb.AppendLine("}")
[void]$sb.AppendLine("// 前缀规则：返回归一化前缀表（最长命中由 diagcode 侧完成）。")
[void]$sb.AppendLine("pub func pfx_count() -> i64 { ensure(); return len(pfx_keys) }")
[void]$sb.AppendLine("pub func pfx_key(i: i64) -> string { return pfx_keys[i] }")
[void]$sb.AppendLine("pub func pfx_code(i: i64) -> string { return pfx_codes[i] }")
[void]$sb.AppendLine("}")
[System.IO.File]::WriteAllText($catFile, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))

# ---------- 机器可读清单（td 数据文件；用户定稿：不用 JSON 用 td） ----------
# td = tie 数据表字面量（type tie<data> 头 + 表名 + 对象数组）。清单本身供
# 文档生成等非性能敏感读取；性能敏感路径用 zd 变体：
#   tiec --compress-data diagdocs/diagcodes.data.tie -o diagdocs/diagcodes.zd
$diagDir = Join-Path $OutDir "diagdocs"
if (-not (Test-Path $diagDir)) { New-Item -ItemType Directory -Path $diagDir -Force | Out-Null }

# td 字符串转义（反斜杠/引号/换行）。
function Esc-Td([string]$s) {
    return ($s.Replace("\", "\\").Replace('"', '\"').Replace("`n", '\n').Replace("`r", '\r').Replace("`t", '\t'))
}

$td = New-Object System.Text.StringBuilder
[void]$td.AppendLine("type tie<data>")
[void]$td.AppendLine("// diagdocs/diagcodes.data.tie —— 诊断标号机器可读清单（p.6.9.15，生成文件勿手改）")
[void]$td.AppendLine("// 列：code/key/name/family/src/template；family 1 词法 2 语法 3 语义 4 运行时 5 CLI 6 后端 7 REPL 8 LSP 9 内部")
[void]$td.AppendLine("diagcodes = [")
foreach ($key in $sorted) {
    [void]$td.AppendLine("    [ `"code`": `"$($map[$key])`", `"key`": `"$(Esc-Td $key)`", `"name`": `"$(Esc-Td $exeKeys[$key].Name)`", `"family`": $($exeKeys[$key].Family), `"src`": `"$(Esc-Td $exeKeys[$key].Src)`", `"template`": `"$(Esc-Td $exeKeys[$key].Template)`" ],")
}
[void]$td.AppendLine("]")
[System.IO.File]::WriteAllText((Join-Path $diagDir "diagcodes.data.tie"), $td.ToString(), [System.Text.UTF8Encoding]::new($false))

# ---------- 文档骨架 ----------
$famNames = @{ 1 = "词法（Lexer）"; 2 = "语法（Parser）"; 3 = "语义（Semantic）"; 4 = "运行时（Runtime）"; 5 = "CLI 与配置（CLI & Config）"; 6 = "后端与 IR（Backend & IR）"; 7 = "REPL 与解释（REPL）"; 8 = "LSP"; 9 = "内部错误与未分类（Internal）" }
foreach ($fam in 1..9) {
    $entries = @()
    foreach ($key in $sorted) {
        if ($exeKeys[$key].Family -ne $fam) { continue }
        $entries += "### $($map[$key])  $($exeKeys[$key].Name)`n- 消息：``$($exeKeys[$key].Template)``；消息名：$($exeKeys[$key].Name)`n- 出处：``$($exeKeys[$key].Src)``"
    }
    $body = "# tie 诊断标号（家族 $($famNames[$fam])） / tie diagnostic codes — $($famNames[$fam])`n`n> 每种标号的成因与常见解决方案说明由 tie-diag 文档维护；本页为自动生成的目录骨架（按家族分组，标号为五位全局序号）。`n"
    if ($entries.Count -eq 0) {
        $body += "`n_（暂无条目）_`n"
    } else {
        $body += "`n" + ($entries -join "`n`n") + "`n"
    }
    [System.IO.File]::WriteAllText((Join-Path $diagDir "codes-e${fam}.md"), $body, [System.Text.UTF8Encoding]::new($false))
}

Write-Host "[gen-diagcodes] 共 $($sorted.Count) 条诊断；生成 $catFile + diagdocs/"
$famCounts = @{}
foreach ($key in $sorted) {
    $f = [int]$exeKeys[$key].Family
    if (-not $famCounts.ContainsKey($f)) { $famCounts[$f] = 0 }
    $famCounts[$f]++
}
foreach ($fam in 1..9) { Write-Host "  家族 $($fam): $($famCounts[$fam]) 条" }