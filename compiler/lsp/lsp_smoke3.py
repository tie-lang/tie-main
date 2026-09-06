# -*- coding: utf-8 -*-
# lsp_smoke3.py：tsp hover 冒烟——didOpen 后对已声明函数发 hover，校验返回签名
import subprocess, json, sys

def frame(m):
    b = json.dumps(m).encode('utf-8')
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

text = 'func add(a: i64, b: i64) -> i64 {\n    return a + b\n}\n\nfunc main() {\n    var x = add(1, 2)\n}\n'
# add 在第一行第 6 列（func add( 的 add 起点）
msgs = [
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"rootUri":"file:///tmp"}},
    {"jsonrpc":"2.0","method":"initialized","params":{}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///tmp/h.tie","languageId":"tie","version":1,"text":text}}},
    {"jsonrpc":"2.0","id":2,"method":"textDocument/hover","params":{"textDocument":{"uri":"file:///tmp/h.tie"},"position":{"line":0,"character":6}}},
    {"jsonrpc":"2.0","id":3,"method":"shutdown","params":None},
    {"jsonrpc":"2.0","method":"exit","params":None},
]
p = subprocess.Popen([TSP], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
for m in msgs:
    p.stdin.write(frame(m)); p.stdin.flush()
p.wait(timeout=8)
outs = []
while True:
    r = read_frame(p.stdout)
    if r is None:
        break
    outs.append(r)

ok = True
hover = None
for o in outs:
    if o.get('id') == 2:
        hover = o.get('result')
        print("HOVER:", json.dumps(hover, ensure_ascii=False) if hover else hover)

if hover and 'add' in json.dumps(hover):
    print("HOVER PASS")
else:
    print("HOVER FAIL")
    ok = False

# 诊断应无未定义（add 已声明）
for o in outs:
    if o.get('method') == 'textDocument/publishDiagnostics':
        print("DIAGS:", [d['message'] for d in o['params']['diagnostics']])

print("SMOKE3:" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)