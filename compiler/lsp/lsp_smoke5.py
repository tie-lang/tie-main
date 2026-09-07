# -*- coding: utf-8 -*-
# lsp_smoke5.py：tsp 特征波冒烟（p.6.9.6-6.9.8）
# 校验 completion / definition / references / signatureHelp / documentSymbol
import subprocess, json, sys, threading

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
    ln = 0
    for line in hdr.split(b'\r\n'):
        if line.lower().startswith(b'content-length:'):
            ln = int(line.split(b':')[1].strip())
    return json.loads(f.read(ln).decode())

TSP = r"F:\Projects\tie-repo\tie-main\compiler\lsp\tsp.exe"
URI = "file:///tmp/f.tie"
# L0: add 声明；L4: main；L5: var x = add(1, 2)
text = "func add(a: i64, b: i64) -> i64 {\n    return a + b\n}\n\nfunc main() {\n    var x = add(1, 2)\n    println(x)\n}\n"

msgs = [
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":None,"rootUri":"file:///tmp","capabilities":{}}},
    {"jsonrpc":"2.0","method":"initialized","params":{}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":URI,"languageId":"tie","version":1,"text":text}}},
    # completion 空词缀（L5 char 10 在 '=' 后）→ 含 add 与关键字
    {"jsonrpc":"2.0","id":2,"method":"textDocument/completion","params":{"textDocument":{"uri":URI},"position":{"line":5,"character":10}}},
    # completion 前缀 "ad"（L5 char 14）→ 只含 add
    {"jsonrpc":"2.0","id":3,"method":"textDocument/completion","params":{"textDocument":{"uri":URI},"position":{"line":5,"character":14}}},
    # definition：add(1,2) 的 add（L5 char 12）→ L0
    {"jsonrpc":"2.0","id":4,"method":"textDocument/definition","params":{"textDocument":{"uri":URI},"position":{"line":5,"character":12}}},
    # references：同位置 → L5 调用 + L0 声明 = 2
    {"jsonrpc":"2.0","id":5,"method":"textDocument/references","params":{"textDocument":{"uri":URI},"position":{"line":5,"character":12},"context":{"includeDeclaration":True}}},
    # signatureHelp：add(1, 之后（L5 char 19）→ activeParameter=1
    {"jsonrpc":"2.0","id":6,"method":"textDocument/signatureHelp","params":{"textDocument":{"uri":URI},"position":{"line":5,"character":19}}},
    # documentSymbol → add + main
    {"jsonrpc":"2.0","id":7,"method":"textDocument/documentSymbol","params":{"textDocument":{"uri":URI}}},
    {"jsonrpc":"2.0","id":8,"method":"shutdown","params":None},
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
th.start()
th.join(40)
if th.is_alive():
    p.kill()
    th.join()
p.wait(timeout=5)

results = {}
for o in outs:
    if 'id' in o and isinstance(o.get('id'), int):
        results[o['id']] = o.get('result')

ok = True
def chk(name, cond):
    global ok
    print(("  PASS: " if cond else "  FAIL: ") + name)
    ok = ok and cond

comp_empty = json.dumps(results.get(2), ensure_ascii=False)
comp_ad = json.dumps(results.get(3), ensure_ascii=False)
chk("completion 空词缀含 add", '"add"' in comp_empty)
chk("completion 空词缀含关键字 if", '"if"' in comp_empty)
chk("completion 前缀 ad 只含 add 相关", 'add' in comp_ad and 'Point' not in comp_ad and 'main' not in comp_ad)

defn = json.dumps(results.get(4), ensure_ascii=False)
chk("definition 命中 add 声明行 0", '"line": 0' in defn or '"line":0' in defn)
chk("definition 命中 uri", URI in defn)

refs = results.get(5)
refs_s = json.dumps(refs, ensure_ascii=False)
chk("references 数量=2（调用+声明）", isinstance(refs, list) and len(refs) == 2)
chk("references 含声明行 0", '"line": 0' in refs_s or '"line":0' in refs_s)
chk("references 含调用行 5", '"line": 5' in refs_s or '"line":5' in refs_s)

sig = json.dumps(results.get(6), ensure_ascii=False)
chk("signatureHelp 含 func add", 'func add' in sig)
chk("signatureHelp activeParameter=1", '"activeParameter": 1' in sig or '"activeParameter":1' in sig)
chk("signatureHelp 含参数 a: i64", 'a: i64' in sig)

dss = json.dumps(results.get(7), ensure_ascii=False)
chk("documentSymbol 含 add", '"name": "add"' in dss or '"name":"add"' in dss)
chk("documentSymbol 含 main", 'main' in dss)

print("== SMOKE5:" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
