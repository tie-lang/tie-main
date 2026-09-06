# -*- coding: utf-8 -*-
# lsp_smoke2.py：tsp 冒烟 v2——生命周期 + 双向诊断（未定义函数 / 合法无诊断）
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

def run(uri, text):
    msgs = [
        {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"rootUri":"file:///tmp"}},
        {"jsonrpc":"2.0","method":"initialized","params":{}},
        {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":uri,"languageId":"tie","version":1,"text":text}}},
        {"jsonrpc":"2.0","id":2,"method":"shutdown","params":None},
        {"jsonrpc":"2.0","method":"exit","params":None},
    ]
    p = subprocess.Popen([TSP], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for m in msgs:
        p.stdin.write(frame(m)); p.stdin.flush()
    p.wait(timeout=8)
    outs = []
    while True:
        r = read_frame(p.stdout)
        if r is None: break
        outs.append(r)
    return outs

def diag_msgs(outs):
    ms = []
    for o in outs:
        if o.get('method') == 'textDocument/publishDiagnostics':
            for d in o['params']['diagnostics']:
                ms.append(d['message'])
    return ms

ok = True
# 用例 A：未定义函数 + 已定义函数 → 只报未定义的
text_a = 'func main() {\n    helper()\n    undefined_func()\n}\n\nfunc helper() {\n}\n'
out_a = run('file:///tmp/a.tie', text_a)
msgs_a = diag_msgs(out_a)
print("A 诊断:", msgs_a)
if any('undefined_func' in m for m in msgs_a) and not any('helper' in m and 'undefined' in m for m in msgs_a):
    print("A PASS")
else:
    print("A FAIL")
    ok = False

# 用例 B：无诊断（括号匹配 + 全部声明）
text_b = 'func main() {\n    println("hi")\n}\n'
out_b = run('file:///tmp/b.tie', text_b)
msgs_b = diag_msgs(out_b)
print("B 诊断:", msgs_b)
if len(msgs_b) == 0:
    print("B PASS")
else:
    print("B FAIL")
    ok = False

print("SMOKE2:" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)