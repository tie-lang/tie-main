# 缺陷报告：TLS 1.3 实况握手 CertificateVerify 验签不匹配 —— 【已根治 2026-09-03】

> 报告日期 / Date：2026-09-02；根治日期 / Resolved：2026-09-03
> 组件 / Component：ext/tls（纯 tie）TLS 1.3 客户端 CertificateVerify 验签
> 归属仓库 / Repo：tie-main
> 严重度 / Severity：已闭环

## 根因（三处叠加）

1. **CVer 签名 content 遗漏上下文串与 NUL**：RFC 8446 §4.4.3 的 content 完整构造为
   `0x20*64 ‖ "TLS 1.3, server CertificateVerify\0" ‖ Transcript-Hash`（OpenSSL
   `statem_lib.c get_cert_verify_tbs_data` 同源）。tie 侧原实现只拼了 `0x20*64 ‖ TH`，
   WebFetch 拉取 OpenSSL 3.0 源码比对后补齐。
2. **转录本（Transcript-Hash）哈希按套件**：0x1301→SHA-256、0x1302→SHA-384；探针当前
   仅 0x1301（SHA-256），s_client 会话为 0x1302（SHA-384）。已注释说明后续扩展。
3. **EC OID 常量笔误**：`x509_parse_spki` 中 EC OID 误写为 `2a8648_86_ce3d0201`
   （多一个 0x86），正确应为 `2a8648ce3d0201`（1.2.840.10045.2.1）→ EC 证书 SPKI
   检测恒失败（isf/ief=0）。修正后 EC 路径工作。

## 兼容性附加

- OpenSSL s_server 实况 ECDSA CertificateVerify 以 **DER（0x30，约 70-72B）** 而非 TLS
  规范的裸 r||s 发送：verify_ecdsa 增加 DER→raw 归一化（同时保留 64B raw 路径）。

## 验证

- RSA 套件（0x0804 PSS-SHA256，256B）：`PASS server CertificateVerify signature (algo=2052 len=256)`
- EC 套件（0x0403，DER 70B）：`PASS server CertificateVerify signature (algo=1027 len=70)`
- TLS 1.2 探针、链校验探针、字节网络探针、GCM/DER/ChaCha-Poly 全回归 PASS。
- 探针 CVer 校验已从 WARN 提升为 fail（验签不过即失败）。
