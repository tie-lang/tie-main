# -*- coding: utf-8 -*-
# lsp_smoke6.py：tsp 波次三冒烟（p.6.9.9-6.9.11）
# 校验 semanticTokens / foldingRange / rename / documentHighlight / codeAction / formatting
import subprocess, json, sys, threading

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
URI = "file:///tmp/g.tie"
# L0: add 声明；L3: main；L4: 体内调用 add
text = "func add(a: i64, b: i64) -> i64 {\n    return a + b\n}\nfunc main() {\n    var x = add(1, 2)\n    println(x)\n}\n"

msgs = [
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":None,"rootUri":"file:///tmp","capabilities":{}}},
    {"jsonrpc":"2.0","method":"initialized","params":{}},
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":URI,"languageId":"tie","version":1,"text":text}}},
    # semanticTokens：data 非空
    {"jsonrpc":"2.0","id":2,"method":"textDocument/semanticTokens/full","params":{"textDocument":{"uri":URI}}},
    # foldingRange：add 函数体折叠
    {"jsonrpc":"2.0","id":3,"method":"textDocument/foldingRange","params":{"textDocument":{"uri":URI}}},
    # rename：光标在 add(1,2)（L4 char 12）→ 3 处编辑（两处调用 + 声明）
    {"jsonrpc":"2.0","id":4,"method":"textDocument/rename","params":{"textDocument":{"uri":URI},"position":{"line":4,"character":12},"newName":"sum"}},
    # documentHighlight：同位置 → >= 2
    {"jsonrpc":"2.0","id":5,"method":"textDocument/documentHighlight","params":{"textDocument":{"uri":URI},"position":{"line":4,"character":12}}},
    # codeAction：缺分号修复（虚构诊断）
    {"jsonrpc":"2.0","id":6,"method":"textDocument/codeAction","params":{"textDocument":{"uri":URI},"range":{"start":{"line":0,"character":0},"end":{"line":0,"character":1}},"context":{"diagnostics":[{"range":{"start":{"line":0,"character":0},"end":{"line":0,"character":1}},"message":"期望 语句结束符"}]}}},
    # formatting：无缩进输入 → 2 空格缩进
    {"jsonrpc":"2.0","id":7,"method":"textDocument/formatting","params":{"textDocument":{"uri":URI},"options":{"tabSize":2,"insertSpaces":True}}},
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

semtok = results.get(2)
semtok_s = json.dumps(semtok, ensure_ascii=False)
chk("semanticTokens data 非空", isinstance(semtok, dict) and isinstance(semtok.get('data'), list) and len(semtok['data']) > 0)

fold = results.get(3)
fold_s = json.dumps(fold, ensure_ascii=False)
chk("foldingRange 非空", isinstance(fold, list) and len(fold) > 0)
chk("foldingRange 含 add 函数体", isinstance(fold, list) and any(isinstance(f, dict) and f.get('startLine') == 0 for f in fold))

ren = json.dumps(results.get(4), ensure_ascii=False)
chk("rename 含 newText sum", '"sum"' in ren)
chk("rename 编辑数 >= 2", ren.count('"range"') >= 2)

hl = results.get(5)
hl_s = json.dumps(hl, ensure_ascii=False)
chk("highlight 数量 >= 2", isinstance(hl, list) and len(hl) >= 2)

ca = json.dumps(results.get(6), ensure_ascii=False)
chk("codeAction 含插入分号", '插入分号' in ca and 'newText' in ca and '";"' in ca)

fmt = results.get(7)
fmt_s = json.dumps(fmt, ensure_ascii=False)
chk("formatting 返回 TextEdit", isinstance(fmt, list) and len(fmt) > 0 and 'newText' in fmt_s)
chk("formatting 2 空格缩进", '  var x = add(1, 2)' in fmt_s)

print("== SMOKE6:" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
