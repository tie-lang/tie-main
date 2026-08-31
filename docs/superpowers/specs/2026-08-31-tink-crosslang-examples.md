# tink 跨语言接入示例代码

* 日期：2026-08-31

* 状态：示例（配合 tink 设计文档 `2026-08-31-tink-design.md`）

* 说明：tink 是**通用数据流互联服务**——任意语言组件只要遵守统一 zd 帧协议即可成为管道节点。tink 的帧协议已实现为**各语言库/包**（与 tie 的 `std/tink.tie` 一一对应），接入方直接引用库，不必手写帧协议：

| 语言     | 库/包                             | 核心 API                                                               |
| ------ | ------------------------------- | -------------------------------------------------------------------- |
| tie    | `std/tink.tie`（命名空间 `tink`）     | `tink.crc32 / frame_encode / frame_next / frame_skip`                |
| Rust   | `tink` crate（`tink/rust/`）      | `tink::crc32 / frame_encode / frame_next / frame_skip`               |
| C      | `tink.h` + `tink.c`（`tink/c/`）  | `tink_crc32 / tink_frame_encode / tink_frame_next / tink_frame_skip` |
| Python | `tink` 包（`tink/python/tink.py`） | `tink.crc32 / frame_encode / frame_next / frame_skip`                |

各实现为**纯函数**（字节进出，不碰 IO），API 语义与校验向量完全一致（`crc32("123456789") == 0xCBF43926`），并带各自语言的单元测试。本文给出 4 种语言的最小节点实现，展示同一「引用库 → 读帧 → 解析 → 处理 → 编码 → 写帧」模式。

## 1. 示例协议定稿

**帧格式**（stdin/stdout 上的字节流）：

```
帧 = [ len: u32 BE ][ payload: len 字节 ][ crc: u32 BE ]
len   = payload 字节数
crc   = CRC32-IEEE(payload)（多项式 0xEDB88320）
```

**载荷**（zd 子集，仅为示例可读性，正式实现用 zd v2 全类型）：

```
i64 数组 = fixarray 头(0x90 | n) + n 个 fixint(0x00..0x7f)
         （示例值限定 0..127，元素个数 ≤ 15）
```

**节点行为**：循环读帧 → 校验 CRC → 解析 i64 数组 → 每元素 +1 → 编码 → 写帧；EOF 结束。CRC 解析与帧编码全部交给 tink 库，节点只需处理 IO 与 zd 载荷。

**管道用法**（tink 主形态，混合任意语言组件）：

```
tink pipe "gen:nums | add-one-tie | add-one-rust | add-one-c | add-one-py | sink:print"
```

***

## 2. tie 节点（add\_one.tie）

基于 `std/tink.tie`：

```tie
type tie<logic>
// tink add_one 节点 —— tie 语言接入示例（帧协议来自 std/tink.tie）
// IO 约定：tink 桥提供 stdin 字节流读取与 stdout 字节流写入
//   （示例以 stdin_read(n) / stdout_write(bytes) 表示，具体原语按 tink 桥实现）
import "../std/tink.tie" as tink

// 读一帧：拼出完整帧字节，交给 tink.frame_next 解析 + 校验 CRC
func read_frame() -> table<i64> {
    var head = stdin_read(4)
    if len(head) < 4 {
        return table_new_i64()          // EOF 哨兵
    }
    var n = ((head[0] & 0xFF) << 24) | ((head[1] & 0xFF) << 16) | ((head[2] & 0xFF) << 8) | (head[3] & 0xFF)
    var body = stdin_read(n)
    var tail = stdin_read(4)
    if len(body) < n || len(tail) < 4 {
        return table_new_i64()
    }
    var raw = table_new_i64()
    var i: i64 = 0
    while i < 4 { table_push(raw, head[i]); i = i + 1 }
    i = 0
    while i < n { table_push(raw, body[i]); i = i + 1 }
    i = 0
    while i < 4 { table_push(raw, tail[i]); i = i + 1 }
    var (payload, next) = tink.frame_next(raw, 0)
    if next < 0 {
        return table_new_i64()
    }
    return payload
}

func write_frame(p: table<i64>) {
    stdout_write(tink.frame_encode(p))   // 依桥提供 concat/拼接原语
}

// ---------- zd 子集编解码 ----------
// fixarray(0x90|n) + n 个 fixint(0x00-0x7f)
func decode_i64_array(p: table<i64>) -> table<i64> {
    var out = table_new_i64()
    if len(p) < 1 || (p[0] & 0xF0) != 0x90 {
        return out
    }
    var n = p[0] & 0x0F
    if len(p) != 1 + n {
        return out
    }
    var i: i64 = 1
    while i <= n {
        table_push(out, p[i])
        i = i + 1
    }
    return out
}

func encode_i64_array(v: table<i64>) -> table<i64> {
    var out = table_new_i64()
    table_push(out, 0x90 | len(v))
    var i: i64 = 0
    while i < len(v) {
        table_push(out, v[i] & 0xFF)
        i = i + 1
    }
    return out
}

// ---------- 主循环 ----------
func main() {
    var payload = read_frame()
    if len(payload) == 0 {
        return                          // EOF
    }
    var vals = decode_i64_array(payload)
    if len(vals) == 0 {
        return
    }
    var i: i64 = 0
    while i < len(vals) {
        vals[i] = vals[i] + 1
        i = i + 1
    }
    write_frame(encode_i64_array(vals))
}
```

***

## 3. Rust 节点（add\_one.rs）

基于 `tink` crate：

```rust
// Cargo.toml: tink = "0.1"
use std::io::{self, Read, Write};

/// 读一帧：拼出完整帧字节，交给 tink::frame_next 解析 + 校验 CRC
fn read_frame() -> io::Result<Option<Vec<u8>>> {
    let stdin = io::stdin();
    let mut lock = stdin.lock();
    let mut len_b = [0u8; 4];
    match lock.read_exact(&mut len_b) {
        Ok(_) => {}
        Err(e) if e.kind() == io::ErrorKind::UnexpectedEof => return Ok(None),
        Err(e) => return Err(e),
    }
    let n = u32::from_be_bytes(len_b) as usize;
    let mut body = vec![0u8; n];
    lock.read_exact(&mut body)?;
    let mut tail = [0u8; 4];
    lock.read_exact(&mut tail)?;
    let mut raw = Vec::with_capacity(n + 8);
    raw.extend_from_slice(&len_b);
    raw.extend_from_slice(&body);
    raw.extend_from_slice(&tail);
    let (payload, _next) = match tink::frame_next(&raw, 0) {
        Some(x) => x,
        None => return Ok(None), // 帧损坏 / CRC 失败（生产应区分错误）
    };
    Ok(Some(payload))
}

/// 写一帧：长度 + payload + CRC
fn write_frame(out: &mut impl Write, payload: &[u8]) -> io::Result<()> {
    out.write_all(&tink::frame_encode(payload))?;
    out.flush()
}

/// zd 子集：fixarray(0x90|n) + n 个 fixint
fn decode_i64_array(p: &[u8]) -> Option<Vec<i64>> {
    if p.is_empty() || p[0] & 0xF0 != 0x90 { return None; }
    let n = (p[0] & 0x0F) as usize;
    if p.len() != 1 + n { return None; }
    Some(p[1..].iter().map(|&b| b as i64).collect())
}

fn encode_i64_array(vals: &[i64]) -> Vec<u8> {
    let mut out = vec![0x90 | vals.len() as u8];
    for &v in vals { out.push(v as u8); }
    out
}

fn main() -> io::Result<()> {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    while let Some(payload) = read_frame()? {
        let Some(mut vals) = decode_i64_array(&payload) else { continue; };
        for v in vals.iter_mut() { *v += 1; }
        write_frame(&mut out, &encode_i64_array(&vals))?;
    }
    Ok(())
}
```

***

## 4. C 节点（add\_one.c）

基于 `tink.h` / `tink.c`：

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "tink.h"   /* tink_crc32 / tink_frame_encode / tink_frame_next / tink_frame_skip */

/* 读一帧：拼出完整帧字节，交给 tink_frame_next 解析 + 校验 CRC */
static int read_frame(uint8_t **out, size_t *n) {
    uint8_t h[4];
    if (fread(h, 1, 4, stdin) != 4) return 0;              /* EOF */
    size_t len = ((size_t)h[0] << 24) | ((size_t)h[1] << 16) | ((size_t)h[2] << 8) | h[3];
    uint8_t *raw = malloc(len + 8);
    if (!raw) return -1;
    memcpy(raw, h, 4);
    if (len && fread(raw + 4, 1, len, stdin) != len) { free(raw); return -1; }
    if (fread(raw + 4 + len, 1, 4, stdin) != 4) { free(raw); return -1; }

    const uint8_t *p; size_t plen, next;
    if (!tink_frame_next(raw, len + 8, 0, &p, &plen, &next)) { free(raw); return -1; }
    uint8_t *dup = malloc(plen ? plen : 1);
    if (!dup) { free(raw); return -1; }
    if (plen) memcpy(dup, p, plen);
    free(raw);
    *out = dup; *n = plen;
    return 1;
}

static void write_frame(const uint8_t *p, size_t n) {
    uint8_t stack[8];
    uint8_t *frame = (n <= 64) ? stack : malloc(n + 8);
    size_t wrote = tink_frame_encode(p, n, frame);
    fwrite(frame, 1, wrote, stdout);
    if (frame != stack) free(frame);
    fflush(stdout);
}

int main(void) {
    uint8_t *payload; size_t n;
    while ((read_frame(&payload, &n)) == 1) {
        /* zd 子集：fixarray(0x90|n) + n 个 fixint */
        if (n < 1 || (payload[0] & 0xF0) != 0x90 || n != 1 + (payload[0] & 0x0F)) { free(payload); continue; }
        size_t cnt = payload[0] & 0x0F;
        for (size_t i = 1; i <= cnt; i++) payload[i] = (uint8_t)(payload[i] + 1);
        write_frame(payload, n);
        free(payload);
    }
    return 0;
}
```

***

## 5. Python 节点（add\_one.py）

基于 `tink` 包：

```python
import sys
import tink  # tink 包：crc32 / frame_encode / frame_next / frame_skip

def read_frame():
    """读一帧；EOF/CRC 失败返回 None"""
    header = sys.stdin.buffer.read(4)
    if not header:
        return None
    n = int.from_bytes(header, "big")
    body = sys.stdin.buffer.read(n)
    tail = sys.stdin.buffer.read(4)
    res = tink.frame_next(header + body + tail, 0)
    if res is None:
        return None
    payload, _ = res
    return payload

def write_frame(payload):
    sys.stdout.buffer.write(tink.frame_encode(payload))
    sys.stdout.buffer.flush()

def decode_i64_array(p):
    """zd 子集：fixarray(0x90|n) + n 个 fixint"""
    if not p or p[0] & 0xF0 != 0x90:
        return None
    n = p[0] & 0x0F
    if len(p) != 1 + n:
        return None
    return list(p[1:])

def encode_i64_array(vals):
    return bytes([0x90 | len(vals)]) + bytes(vals)

def main():
    while True:
        payload = read_frame()
        if payload is None:
            break
        vals = decode_i64_array(payload)
        if vals is None:
            continue
        write_frame(encode_i64_array([v + 1 for v in vals]))

if __name__ == "__main__":
    main()
```

***

## 6. 混合管道示例

四个语言节点可任意混排（同一帧协议 + 各自语言 tink 库，语言无关）：

```
# gen:nums 产出 zd 帧（如 [1,2,3]），四种语言各 +1，最后 sink 打印
tink pipe "gen:nums | add-one-tie | add-one-rust | add-one-c | add-one-py | sink:print"
# 期望输出帧：[1,2,3] → [2,3,4] → [3,4,5] → [4,5,6] → [5,6,7]
```

任意语言接入节点时只需：

1. 引用该语言的 tink 库/包（见文首表格），用它完成帧编码/解析/CRC 校验；
2. 处理 payload（zd 数据）；
3. 写 stdout 帧：长度 + payload + CRC，flush。

***

## 7. 接入检查清单

* [ ] 使用语言对应的 tink 库/包（tie: `std/tink.tie`；Rust: `tink` crate；C: `tink.h`/`tink.c`；Python: `tink.py`）

* [ ] 帧格式与 tink 库一致（长度大端、CRC32-IEEE）——库已保证，勿手写

* [ ] 读端处理 EOF（无输入即退出）

* [ ] CRC 校验失败不静默传递（报错或退出）——库在 `frame_next` 中校验

* [ ] 写端 flush，保证帧完整到达下游

* [ ] 无外部状态/依赖 tink 内部——仅依赖 zd 帧协议与 tink 库

