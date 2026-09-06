# -*- coding: utf-8 -*-
# fix_reserved.py：把 tsp 源码里的保留字标识符改名为安全名
files = [
    'compiler/lsp/server.tie',
    'compiler/lsp/protocol.tie',
]
for p in files:
    s = open(p, encoding='utf-8').read()
    # code (参数) -> errcode
    s = s.replace('code: i64', 'errcode: i64')
    s = s.replace('to_string(code)', 'to_string(errcode)')
    # params (参数) -> parms；仅影响签名与局部 var（JSON 键 "params" 是字符串，不受影响）
    s = s.replace('params: string', 'parms: string')
    s = s.replace('var params', 'var parms')
    s = s.replace('"params":' + ' ' + '+', '"params":' + ' ' + '+')  # 无操作保护
    s = s.replace('parms + diagnostics', 'parms + diagnostics')
    open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')