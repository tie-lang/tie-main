# -*- coding: utf-8 -*-
# lsp_smoke4.py：tsp 编译器级诊断冒烟（p.6.9.3/6.9.5）
# 校验：
#   1. 语义错误文档 → publishDiagnostics 含编译器错误（未声明的变量）
#   2. 警告文档（整数除法截断）→ 诊断 severity=2
#   3. 正常文档 → 诊断空数组
#   4. import 相对路径解析（base_dir 从 uri 推导）→ 无「无法读取导入文件」错误
import subprocess, json, sys, os

def frame(msg):
    b = json.dumps(msg).encode('utf-8')
    return b'Content-Length: %d\r\n\r\n' % len(b) + b

def read_frame(f):
    hdr = b''
    while b'\r\n\r\n' not in hdr:
        c = f.read(1)
        if not c:
            return None
        hdr += c
    length = 0
    for line in hdr.split(b'\r\n'):
        if line.lower().startswith(b'content-length:'):
            length = int(line.split(b':')[1].strip())
    body = f.read(length)
    return json.loads(body)

base = "file:///f:/Projects/tie-repo/tie-main/compiler/lsp/"

ok_doc = "func add(a: i64, b: i64) -> i64 {\n    return a + b\n}\n\nfunc main() -> i64 {\n    var x = add(1, 2)\n    return x\n}\n"
err_doc = "func main() -> i64 {\n    var x = 1\n    println(undef_var)\n    return 0\n}\n"
warn_doc = "func main() -> i64 {\n    var x = 7 / 2\n    return x\n}\n"
imp_doc = "import \"../../std/stdio.tie\" as stdio\n\nfunc main() -> i64 {\n    stdio.write_str(\"ok\")\n    return 0\n}\n"

msgs = [
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":None,"rootUri":base,"capabilities":{}}},
    {"jsonrpc":"2.0","method":"initialized","params":{}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":base+"ok.tie","languageId":"tie","version":1,"text":ok_doc}}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":base+"err.tie","languageId":"tie","version":1,"text":err_doc}}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":base+"warn.tie","languageId":"tie","version":1,"text":warn_doc}}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":base+"imp.tie","languageId":"tie","version":1,"text":imp_doc}}},
    {"jsonrpc":"2.0","id":2,"method":"shutdown","params":None},
    {"jsonrpc":"2.0","method":"exit","params":None},
]

p = subprocess.Popen([r"F:\Projects\tie-repo\tie-main\compiler\lsp\tsp_new.exe"],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)
for m in msgs:
    p.stdin.write(frame(m))
    p.stdin.flush()

out = []
while True:
    r = read_frame(p.stdout)
    if r is None:
        break
    out.append(r)
p.wait(timeout=30)

diags_by_uri = {}
for m in out:
    if m.get('method') == 'textDocument/publishDiagnostics':
        diags_by_uri[m['params']['uri']] = m['params']['diagnostics']

ok = True
def chk(name, cond):
    global ok
    print(("  PASS: " if cond else "  FAIL: ") + name)
    ok = ok and cond

print("== 诊断内容 ==")
for uri, diags in sorted(diags_by_uri.items()):
    for d in diags:
        print("  %s %s [%d] %s" % (uri.split('/')[-1], d['range']['start'], d['severity'], d['message'][:60]))
    if not diags:
        print("  %s (无诊断)" % uri.split('/')[-1])

chk("ok 文档无诊断", len(diags_by_uri.get(base+"ok.tie", [])) == 0)
errs = diags_by_uri.get(base+"err.tie", [])
chk("err 文档有 1 条 error 诊断", len(errs) == 1 and errs[0]['severity'] == 1)
chk("err 消息为未声明变量", any('未声明的变量' in d['message'] for d in errs))
warns = diags_by_uri.get(base+"warn.tie", [])
chk("warn 文档有 warning 诊断", any(d['severity'] == 2 for d in warns))
imps = diags_by_uri.get(base+"imp.tie", [])
chk("import 文档无错误", all(d['severity'] != 1 for d in imps))

print("== SMOKE4:" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
