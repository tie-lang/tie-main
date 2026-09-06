# -*- coding: utf-8 -*-
# lsp_smoke.py：tsp 冒烟测试——模拟 vscode-languageclient 帧序列
# 发送：initialize → initialized → didOpen(带括号错误) → shutdown → exit
# 校验：initialize 响应含 capabilities；didOpen 后收到 publishDiagnostics 且含错误。
import subprocess, json, sys, time

def frame(msg):
    b = json.dumps(msg).encode('utf-8')
    return b'Content-Length: %d\r\n\r\n' % len(b) + b

def read_frame(f):
    # 读头部
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

msgs = [
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":None,"rootUri":"file:///tmp","capabilities":{}}},
    {"jsonrpc":"2.0","method":"initialized","params":{}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///tmp/a.tie","languageId":"tie","version":1,"text":"func main() {\n    println(\"hello\")"}}},
    {"jsonrpc":"2.0","id":2,"method":"shutdown","params":None},
    {"jsonrpc":"2.0","method":"exit","params":None},
]

p = subprocess.Popen([r"F:\Projects\tie-repo\tie-main\compiler\lsp\tsp.exe"],
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

import threading
def drain():
    try:
        while True:
            r = read_frame(p.stdout)
            if r is None:
                break
            out.append(r)
    except Exception:
        pass

p.wait(timeout=10)
for m in out:
    print(json.dumps(m, ensure_ascii=False))

# 校验
ok = True
got_init = any(m.get('id') == 1 and 'result' in m and 'capabilities' in m['result'] for m in out)
got_diag = any(m.get('method') == 'textDocument/publishDiagnostics' and m.get('params',{}).get('diagnostics') for m in out)
print("== init ok:", got_init, "| diag ok:", got_diag)
if got_init and got_diag:
    print("SMOKE:PASS")
else:
    print("SMOKE:FAIL")
    sys.exit(1)