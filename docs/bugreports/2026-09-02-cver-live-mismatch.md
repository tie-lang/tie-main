# 缺陷报告：TLS 1.3 实况握手 CertificateVerify 验签不匹配（本地 Strawberry openssl s_server）

> 报告日期 / Date：2026-09-02
> 组件 / Component：ext/tls（纯 tie）TLS 1.3 客户端 CertificateVerify 验签路径
> 归属仓库 / Repo：tie-main
> 严重度 / Severity：中（进程可完成握手与应用数据回环，但服务器身份绑定校验未通过——安全验证缺口，未达标即不可用于真实 https）

## 一、现象 / Symptom

`tests/tls_probe/tls13_hello.tie` 对本机 `openssl s_server -tls1_3 -rev`（Strawberry OpenSSL，C:\Strawberry\c\bin\openssl.exe，证书 c.pem/k.pem 为本地自签 RSA-2048）完成完整 TLS 1.3 握手：

- server Finished verify_data 校验 **PASS**（转录本字节级精确）；
- 应用数据双向加密回环 **PASS**；
- **CertificateVerify（rsa_pss_rsae_sha256=0x0804，256 字节）验签不匹配**（探针 WARN）。

## 二、已建立的事实（全部实测）/ Established Facts

1. **转录本精确**：server Finished = HMAC(server_hs_key, SHA256(CH..CVer)) 通过 ⇒ probe 的转录本与服务器视角逐字节一致；CVer 覆盖的前缀 CH..Certificate 是其精确前缀。
2. **PSS 数学正确**：用 k.pem 对 content = 0x20*64‖SHA256(转录本) 执行 `openssl dgst -sign`（pss, salt=32），再由同一套 tie/python 管线验证 → **PASS**（受控签名对照）；管线同时验证过 RFC  значений（FIPS SHA-256、RFC 4231 HMAC、RFC 5869 HKDF）。
3. **签名与密钥配对**：服务器 CVer 签名 powmod 后 EM 末字节恒为 0xBC（多次独立会话复现），salt=32 位置的结构（全零 PS + 0x01 标记）成立 ⇒ 签名确为本密钥下的合法 PSS EM。
4. **捕获无污染**：探针落盘的 cver_transcript/cver_sig 与其解密出的原始线字节逐字节一致（对拍通过）；`openssl pkeyutl -verify`（同一密钥、content=0x20*64‖SHA256(转录本)、salt 32）对服务器签名 → **Signature Verification Failure**。
5. **服务器多项式排除**：`openssl s_client` 对同一服务器本身可完成握手（其内部 CVer 校验通过）；而对其 -msg 转储重建的同一结构数据，同一套验签管线同样不匹配——排除了「探针独有污染」，问题收敛在「对实况内容构造的认知缺口」。

## 三、穷举矩阵（全部 NONE）/ Exhaustive Scan Matrix

对服务器签名、同一密钥，扫描组合全部无命中：
- 转录本：帧式/纯消息体式；前缀 CH、CH+SH、+EE、+Cert、+CVer、+Finished；非连续组合 11 种（如 SH+EE+Cert 等）；
- 内容包装：0x20*64（长度 16/32/40/48/64/96、填充 0x20/0x00）‖ TH/原始转录本；无包装直接 TH；摘要双层/单层 SHA-256/SHA-384/SHA-512；
- 上下文串：空 / "TLS 1.3, server CertificateVerify" 等 4 种；
- EM 布局 2 种（含/不含前导 0x00）、DB 顶位清除 2 种、盐长 0..222 全扫。

## 四、最小复现 / Minimal Repro

前置：任意生成自签 RSA-2048 证书（c.pem/k.pem），`openssl s_server -accept 19844 -tls1_3 -cert c.pem -key k.pem -rev`；
运行 `compiler\tiec.exe tests\tls_probe\tls13_hello.tie` 后执行产物，观察 `WARN CVer mismatch`。
复现产物（供离线分析）：cver 转录本/签名/SPKI 十六进制仍在诊断脚本轨迹中（见下一节）。

## 五、下一步方向 / Next Steps

1. 对照 OpenSSL 3.6 `tls13_cert_verify.c`/`s_server` 签名输入构造（时间点/缓冲拼接），重点核对其对 CertificateVerify content 的 Transcript-Hash 起点；
2. 用 `-keylogfile` 双端记录配合 OPENSSL 源码逐步比对转录本哈希起始偏移；
3. 备选：以 RFC 8448 完整握手向量（含 CertificateVerify 与固定签名）做离线权威对照，隔离「实现」与「服务器行为」。

（此问题不阻塞 p.6.6.1 其余构成：链校验（AC-5）、TLS 1.2（AC-6）、统一入口（AC-7）均可独立推进；CVer 实况验签达标前，tls.tie 的 https 落地暂缓。）
