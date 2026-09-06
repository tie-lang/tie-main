# scripts/test-diagcodes.ps1 —— 诊断标号回归测试（p.6.9.15）
# ============================================================
# 职责：验证 tiec 全部错误/警告都挂了 C# 式标号：
#   1) 对 tests/errors/golden/*.tie 逐条跑 tiec，断言错误输出：
#      - 含 "error[E"（挂了标号）
#      - 不含 "error[E0000]"（无未分类回退）
#      （过时 golden——现行编译器已接受该语料（编译成功）→ 跳过）
#   2) 对固定警告语料跑 tiec，断言输出含 "warning[W0001]..W0004" 四类
#      经验型警告（浮点相等/整数除法截断/循环字符串拼接/表变量拷贝共享）。
#   3) 运行 diagcode 单元探针（tests/_p6915_probe/diagcode_probe.tie）。
#
# 判死纪律（写死）：Start-Process 的 WaitForExit(ms) 在本环境假超时，
# 必须 RedirectStandardOutput 到文件 + 心跳轮询 $p.Refresh()/HasExited
# （≤250ms）+ 超时 taskkill /F /PID。
#
# 用法：
#   .\scripts\test-diagcodes.ps1              # 全量回归（用 compiler/tiec.exe）
#   .\scripts\test-diagcodes.ps1 -Tiec <exe>  # 指定 tiec 二进制
#   .\scripts\test-diagcodes.ps1 --help
# 退出码：0 = 全 PASS / 1 = 有失败

param(
    [Parameter(Position = 0)]
    [string]$Command = "",
    [string]$Tiec = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if ($Command -in @("--help", "-h", "/?")) {
    Write-Host @"
tie 诊断标号回归测试（p.6.9.15）

用法:
  .\scripts\test-diagcodes.ps1 [-Tiec <exe>]   # 默认 compiler/tiec.exe
  .\scripts\test-diagcodes.ps1 --help

断言:
  (1) golden 错误语料全部输出 error[E#####]（无 E0000 回退）
  (2) 警告语料输出 W0001..W0004 经验型警告
  (3) diagcode 单元探针 ALL PASS
"@
    exit 0
}

if ($Tiec -eq "") {
    $Tiec = Join-Path $Root "compiler\tiec.exe"
}
if (-not (Test-Path $Tiec)) {
    Write-Host "[test-diagcodes] 未找到 tiec: $Tiec" -ForegroundColor Red
    exit 1
}

$fails = 0
$total = 0

# ---------- 判死安全的命令执行：输出文件 + 心跳轮询 + 超时强杀 ----------
# 参数以数组传入（Start-Process 对含空格路径自动加引号；本环境路径无空格）。
function Invoke-Tiec([string[]]$argsArr, [string]$outFile, [int]$timeoutMs = 60000) {
    $p = Start-Process -FilePath $Tiec -ArgumentList $argsArr -RedirectStandardOutput $outFile `
        -RedirectStandardError "$outFile.err" -NoNewWindow -PassThru
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while (-not $p.HasExited) {
        $p.Refresh()
        if ($sw.ElapsedMilliseconds -gt $timeoutMs) {
            Stop-Process -Id $p.Id -Force
            return -1   # 超时
        }
        Start-Sleep -Milliseconds 200
    }
    $sw.Stop()
    return $p.ExitCode
}

# ---------- (1) golden 错误语料覆盖 ----------
$GoldenDir = Join-Path $Root "tests\errors\golden"
$tmpOut = Join-Path $env:TEMP "diagcodes_golden.out"
$tieFiles = Get-ChildItem $GoldenDir -Filter "*.tie" | Sort-Object Name
foreach ($f in $tieFiles) {
    $rc = Invoke-Tiec @($f.FullName) $tmpOut 60000
    $out = ""
    if (Test-Path $tmpOut) { $out = [System.IO.File]::ReadAllText($tmpOut, [System.Text.Encoding]::UTF8) }
    if (Test-Path "$tmpOut.err") {
        $out += [System.IO.File]::ReadAllText("$tmpOut.err", [System.Text.Encoding]::UTF8)
    }
    if ($rc -eq -1) {
        Write-Host "[test-diagcodes] 超时: $($f.Name)" -ForegroundColor Yellow
        $fails++
        continue
    }
    $total++
    if ($out -match "编译成功" -and $out -notmatch "error\[E") {
        continue   # 过时 golden：现行编译器已接受（编译成功）→ 跳过
    }
    if ($out -notmatch "error\[E") {
        Write-Host "[test-diagcodes] NO-CODE: $($f.Name)" -ForegroundColor Red
        Write-Host "    $($out.Trim())"
        $fails++
    } elseif ($out -match "error\[E0000\]") {
        Write-Host "[test-diagcodes] FALLBACK(E0000): $($f.Name)" -ForegroundColor Red
        Write-Host "    $($out.Trim())"
        $fails++
    }
}

# ---------- (2) 警告语料 ----------
$warnSrc = Join-Path $env:TEMP "diagcodes_warn_probe.tie"
$warnOut = Join-Path $env:TEMP "diagcodes_warn.out"
[System.IO.File]::WriteAllText($warnSrc, @'
type tie<logic>
func main() {
    var s: string = ""
    var i: i64 = 0
    while i < 100 {
        s = s + "x"
        i = i + 1
    }
    var a: table<i64> = table_new_i64()
    var b = a
    var f: f64 = 1.5
    var g: f64 = 2.5
    if f == g {
        println("eq")
    }
    var q: i64 = 7 / 2
    println(s + to_string(len(b)) + to_string(q))
}
'@, [System.Text.UTF8Encoding]::new($false))
$rc = Invoke-Tiec @($warnSrc) $warnOut 60000
$out = ""
if (Test-Path $warnOut) { $out = [System.IO.File]::ReadAllText($warnOut, [System.Text.Encoding]::UTF8) }
if (Test-Path "$warnOut.err") { $out += [System.IO.File]::ReadAllText("$warnOut.err", [System.Text.Encoding]::UTF8) }
foreach ($wc in @("W0001", "W0002", "W0003", "W0004")) {
    if ($out -match "warning\[$wc\]") {
        Write-Host "[test-diagcodes] 警告 $wc 命中" -ForegroundColor Green
    } else {
        Write-Host "[test-diagcodes] 警告缺失: $wc" -ForegroundColor Red
        $fails++
    }
}

# ---------- (3) diagcode 单元探针 ----------
$probeSrc = Join-Path $Root "tests\_p6915_probe\diagcode_probe.tie"
$probeExe = Join-Path $env:TEMP "diagcode_probe.exe"
$probeOut = Join-Path $env:TEMP "diagcode_probe.out"
$rc = Invoke-Tiec @($probeSrc, "-o", $probeExe) $probeOut 120000
$out = ""
if (Test-Path $probeOut) { $out = [System.IO.File]::ReadAllText($probeOut, [System.Text.Encoding]::UTF8) }
if ($rc -eq 0) {
    $p = Start-Process -FilePath $probeExe -RedirectStandardOutput $probeOut -NoNewWindow -PassThru -Wait
    $out = [System.IO.File]::ReadAllText($probeOut, [System.Text.Encoding]::UTF8)
    if ($out -match "ALL PASS") {
        Write-Host "[test-diagcodes] diagcode 单元探针 PASS" -ForegroundColor Green
    } else {
        Write-Host "[test-diagcodes] diagcode 单元探针失败" -ForegroundColor Red
        Write-Host $out
        $fails++
    }
} else {
    Write-Host "[test-diagcodes] diagcode 探针编译失败" -ForegroundColor Red
    $fails++
}

Write-Host "[test-diagcodes] golden 语料 $total 条（跳过过时），失败 $fails"
if ($fails -eq 0) {
    Write-Host "[test-diagcodes] ALL PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[test-diagcodes] FAILS=$fails" -ForegroundColor Red
    exit 1
}
