# -*- coding: utf-8 -*-
# lsp_smoke7.py：tsp 跨文件引用/重命名（p.6.9.7/6.9.10 完善）
# A 定义 shared 并在自身调用；B import A 后以 a.shared(5) 调用。
# 校验：references 跨文件找到 A/B 两处；rename 生成跨文件 WorkspaceEdit。
import subprocess, json, sys, threading, io

def frame(msg):
    b = json.dumps(msg, ensure_ascii=False).encode('utf-8')
    return b'Content-Length: %d\r\n\r\n' % len(b) + b

def read_frame(f):
    hdr = b''
    while b'\r\n\r\n' not in hdr:
        c = f.read(1)
        if not c:
            return None
        hdr += c
    ln = 0
    for line in hdr.split(b'\r\n'):
        if line.lower().startswith(b'content-length:'):
            ln = int(line.split(b':')[1].strip())
    return json.loads(f.read(ln).decode())

TSP = r"F:\Projects\tie-repo\tie-main\compiler\lsp\tsp.exe"
UA = "file:///f:/Projects/tie-repo/tie-main/compiler/lsp/_smoke_a.tie"
UB = "file:///f:/Projects/tie-repo/tie-main/compiler/lsp/_smoke_b.tie"
# import 从磁盘解析：先落盘 A/B（B 的 import 读取 A）
with io.open(r"f:\Projects\tie-repo\tie-main\compiler\lsp\_smoke_a.tie", "w", encoding="utf-8", newline="") as fh:
    fh.write("pub func shared(x: i64) -> i64 {\n    return x\n}\n")
with io.open(r"f:\Projects\tie-repo\tie-main\compiler\lsp\_smoke_b.tie", "w", encoding="utf-8", newline="") as fh:
    fh.write('import "./_smoke_a.tie"\n\nfunc main() {\n    var y = shared(5)\n    println(y)\n}\n')
text_a = "pub func shared(x: i64) -> i64 {\n    return x\n}\n"
text_b = "import \"./_smoke_a.tie\"\n\nfunc main() {\n    var y = shared(5)\n    println(y)\n}\n"

msgs = [
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":None,"rootUri":"file:///f:/Projects/tie-repo/tie-main","capabilities":{}}},
    {"jsonrpc":"2.0","method":"initialized","params":{}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":UA,"languageId":"tie","version":1,"text":text_a}}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":UB,"languageId":"tie","version":1,"text":text_b}}},
    # references：A 中 shared 声明处（L0 char 9）→ 应含 B 内调用 + 声明
    {"jsonrpc":"2.0","id":2,"method":"textDocument/references","params":{"textDocument":{"uri":UA},"position":{"line":0,"character":9},"context":{"includeDeclaration":True}}},
    # rename：同位置 → WorkspaceEdit 含 A 与 B 两个 uri 的编辑
    {"jsonrpc":"2.0","id":3,"method":"textDocument/rename","params":{"textDocument":{"uri":UA},"position":{"line":0,"character":9},"newName":"renamed"}},
    # definition：B 中 shared 调用处（L3 char 12）→ 应跳到 A 的声明
    {"jsonrpc":"2.0","id":4,"method":"textDocument/definition","params":{"textDocument":{"uri":UB},"position":{"line":3,"character":12}}},
    {"jsonrpc":"2.0","id":5,"method":"shutdown","params":None},
    {"jsonrpc":"2.0","method":"exit","params":None},
]
p = subprocess.Popen([TSP], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
outs = []
for m in msgs:
    p.stdin.write(frame(m)); p.stdin.flush()
def drain():
    while True:
        r = read_frame(p.stdout)
        if r is None:
            break
        outs.append(r)
th = threading.Thread(target=drain, daemon=True)
th.start(); th.join(60)
if th.is_alive():
    p.kill()
    th.join()
p.wait(timeout=5)

results = {}
diags = {}
for o in outs:
    if 'id' in o and isinstance(o.get('id'), int):
        results[o['id']] = o.get('result')
    if o.get('method') == 'textDocument/publishDiagnostics':
        diags[o['params']['uri']] = [d['message'][:40] for d in o['params']['diagnostics']]

ok = True
def chk(name, cond):
    global ok
    print(("  PASS: " if cond else "  FAIL: ") + name)
    ok = ok and cond

print("诊断 A:", diags.get(UA, []))
print("诊断 B:", diags.get(UB, []))

refs = results.get(2)
refs_s = json.dumps(refs, ensure_ascii=False)
chk("references 数量 >= 2（B 调用 + A 声明）", isinstance(refs, list) and len(refs) >= 2)
chk("references 含 A 文档（声明）", UA in refs_s)
chk("references 含 B 文档（跨文件调用）", UB in refs_s)
chk("references 含 A 声明行 0", '"line": 0' in refs_s or '"line":0' in refs_s)

ren = results.get(3)
ren_s = json.dumps(ren, ensure_ascii=False)
chk("rename 含 newText renamed", 'renamed' in ren_s)
chk("rename 跨文件含 B", UB in ren_s)
chk("rename 跨文件含 A", UA in ren_s)

defn = results.get(4)
defn_s = json.dumps(defn, ensure_ascii=False)
chk("definition 跨文件 B→A 声明", UA in defn_s and ('"line": 0' in defn_s or '"line":0' in defn_s))

# 阶段 2：import 变更级联——把 A 磁盘内容改坏，发 didChangeWatchedFiles，
# B（import A）应重分析并产生错误诊断
bad_a = "pub func shared(x: i64) -> i64 {\n    return x\n"
with io.open(r"f:\Projects\tie-repo\tie-main\compiler\lsp\_smoke_a.tie", "w", encoding="utf-8", newline="") as fh:
    fh.write(bad_a)
p2 = subprocess.Popen([TSP], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
msgs2 = [
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":None,"rootUri":"file:///f:/Projects/tie-repo/tie-main","capabilities":{}}},
    {"jsonrpc":"2.0","method":"initialized","params":{}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":UA,"languageId":"tie","version":1,"text":text_a}}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":UB,"languageId":"tie","version":1,"text":text_b}}},
    {"jsonrpc":"2.0","method":"workspace/didChangeWatchedFiles","params":{"changes":[{"uri":UA,"type":2}]}},
    {"jsonrpc":"2.0","id":9,"method":"shutdown","params":None},
    {"jsonrpc":"2.0","method":"exit","params":None},
]
for m in msgs2:
    p2.stdin.write(frame(m)); p2.stdin.flush()
outs2 = []
def drain2():
    while True:
        r = read_frame(p2.stdout)
        if r is None:
            break
        outs2.append(r)
th2 = threading.Thread(target=drain2, daemon=True)
th2.start(); th2.join(40)
if th2.is_alive():
    p2.kill()
    th2.join()
p2.wait(timeout=5)
diags2 = {}
for o in outs2:
    if o.get('method') == 'textDocument/publishDiagnostics':
        diags2[o['params']['uri']] = [d['message'][:60] for d in o['params']['diagnostics']]
print("级联后 A 诊断:", diags2.get(UA, []))
print("级联后 B 诊断:", diags2.get(UB, []))
chk("级联：B 重分析后出现错误诊断（A 磁盘变坏）", len(diags2.get(UB, [])) > 0)

print("== SMOKE7:" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
