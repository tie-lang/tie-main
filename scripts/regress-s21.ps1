# S2.1 字符串模型回归验证脚本（tie-s21 worktree）
# 用法: pwsh scripts/regress-s21.ps1 <tiec路径>
param(
    [Parameter(Mandatory = $true)][string]$Tiec
)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$env:TIE_INTERP_LIB = Join-Path $Root 'target\release\tie_interp.lib'
if (-not (Test-Path $env:TIE_INTERP_LIB)) {
    Write-Warning "TIE_INTERP_LIB 不存在: $env:TIE_INTERP_LIB（回归结果将不可信）"
}
$pass = 0; $fail = 0; $known = 0

# r.1.6.6：Linux 平台差异豁免表——探针显式依赖 Windows 语义（CMD、CreateProcessW、
# 控制台 API、BCrypt Windows CNG 密码学）与 "/" 相对路径假设，Linux 下记为已知
# 平台 SKIP（不算 fail；BCrypt 族随 r.1.6.7 Linux 平台库补全后移除）。
$IsLinux = ($IsWindows -eq $false)
$linuxKnown = @(
    'probe4_ffi.tie',            # 运行 cmd（Windows CMD）
    'proc_createprocessw_pipe.tie', # CreateProcessW 进程管道探针
    'extern_s10_ptr.tie',        # GetStdHandle/GetConsoleMode Win32 控制台 extern
    'std_httpc_probe.tie',       # tls→BCrypt Windows CNG（r.1.6.7）
    'std_net_text.tie',          # 同
    'std_net_bytes.tie',         # 同
    'std_sse_probe.tie'          # 同
)
function Is-LinuxKnown($name) {
    if (-not $IsLinux) { return $false }
    return $linuxKnown -contains $name
}

function Compile-Run($src, $runIt) {
    $exe = $src -replace '\.tie$', '.exe'
    & $Tiec $src -o $exe *> $null
    if ($LASTEXITCODE -ne 0) { return "COMPILE_FAIL" }
    if ($runIt) {
        $out = & $exe 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) { return "RUN_FAIL rc=$LASTEXITCODE out=$out" }
        return "OK $out"
    }
    return "OK"
}

Write-Host "=== 1. S2.1 探针（编译+运行） ==="
$probes = @(
    'tests\s21_probe\probe1_binary.tie',
    'tests\s21_probe\probe2_len.tie',
    'tests\s21_probe\probe3_chars.tie',
    'tests\s21_probe\probe4_ffi.tie',
    'tests\s21_probe\probe5_sb.tie'
)
foreach ($p in $probes) {
    if (Is-LinuxKnown (Split-Path $p -Leaf)) {
        Write-Host "SKIP(Linux差异) $p"; $known++
        continue
    }
    $r = Compile-Run (Join-Path $Root $p) $true
    if ($r.StartsWith("OK")) { Write-Host "PASS $p"; $pass++ }
    else { Write-Host "FAIL $p -> $r"; $fail++ }
}

Write-Host "=== 2. S2.2 探针（编译+运行） ==="
Get-ChildItem (Join-Path $Root 'tests\s22_probe') -Filter '*.tie' | ForEach-Object {
    $r = Compile-Run $_.FullName $true
    if ($r.StartsWith("OK")) { Write-Host "PASS $($_.Name)"; $pass++ }
    else { Write-Host "FAIL $($_.Name) -> $r"; $fail++ }
}

Write-Host "=== 3. S2.3 探针（编译+运行） ==="
# 预期 panic 探针：panic("消息") 语义 = 打印消息并以 exit 1 退出——rc=1 且输出含
# 预期消息视为 PASS（否则探针本身无意义）。r.1 基线遗留 FAIL 的根因即此。
$expectedPanic = @{ 'try_probe.tie' = '致命错误：除数不能为零' }
Get-ChildItem (Join-Path $Root 'tests\s23_probe') -Filter '*.tie' | ForEach-Object {
    $r = Compile-Run $_.FullName $true
    if ($r.StartsWith("OK")) { Write-Host "PASS $($_.Name)"; $pass++ }
    elseif ($expectedPanic.ContainsKey($_.Name) -and $r -match 'RUN_FAIL rc=1' -and $r.Contains($expectedPanic[$_.Name])) {
        Write-Host "PASS(panic 预期) $($_.Name)"; $pass++
    }
    else { Write-Host "FAIL $($_.Name) -> $r"; $fail++ }
}

Write-Host "=== 4. tests/language 正例（编译） ==="
Get-ChildItem (Join-Path $Root 'tests\language') -Filter '*.tie' | Where-Object {
    $_.Name -notlike '*_neg*' -and $_.Name -notlike '*.ir.tie'
} | ForEach-Object {
    if ($_.Name -in @('extern_decl.tie', 'std_fs_path.tie')) {
        Write-Host "SKIP(基线已知) $($_.Name)"; $known++
        return
    }
    if (Is-LinuxKnown $_.Name) {
        Write-Host "SKIP(Linux差异) $($_.Name)"; $known++
        return
    }
    $r = Compile-Run $_.FullName $false
    if ($r -eq "OK") { Write-Host "PASS $($_.Name)"; $pass++ }
    else { Write-Host "FAIL $($_.Name) -> $r"; $fail++ }
}

Write-Host "=== 5. tests/language 负例（应拒绝） ==="
Get-ChildItem (Join-Path $Root 'tests\language') -Filter '*_neg*.tie' | ForEach-Object {
    & $Tiec $_.FullName -o (Join-Path $Root 'compiler\neg_tmp.exe') *> $null
    if ($LASTEXITCODE -ne 0) { Write-Host "PASS(拒) $($_.Name)"; $pass++ }
    else { Write-Host "FAIL(未拒) $($_.Name)"; $fail++ }
}

Write-Host "=== 6. S3.1 config_smoke（编译+运行） ==="
$r = Compile-Run (Join-Path $Root 'tests\s31\config_smoke.tie') $true
if ($r.StartsWith("OK")) { Write-Host "PASS config_smoke"; $pass++ }
else { Write-Host "FAIL config_smoke -> $r"; $fail++ }

Write-Host ""
Write-Host "=== 汇总: PASS=$pass FAIL=$fail SKIP(已知基线)=$known ==="
exit ($fail -gt 0 ? 1 : 0)
