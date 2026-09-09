// tests/_r151_probe/R151StringAbiProbe.java —— r.1.5.1 tie string 跨 FFM 返回 ABI 探针
// ============================================================
// 跨语言消费 tests/_r151_probe/r151_string_abi.dll（tiec --shared 产物）：
//   MethodHandle downcall（FunctionDescriptor.of(ADDRESS)）调用导出符号
//   r151$ascii / r151$chinese / r151$binary / r151$empty / r151$concat_long /
//   r151$version，断言 tie string 返回布局：
//     ① 返回值 = 单个指针（数据指针，非结构体/双值/引用计数盒）
//     ② 数据指针 -8 处 = 8 字节小端 i64 长度头（UTF-8 字节数）
//     ③ [data, data+len) = UTF-8 字节（含内嵌 NUL，二进制安全）
//     ④ data[len] = '\0'（边界自动 NUL，strlen 兼容）
// 编译运行：
//   javac -encoding UTF-8 R151StringAbiProbe.java
//   java --enable-native-access=ALL-UNNAMED R151StringAbiProbe r151_string_abi.dll
// 需要 Java 25+（java.lang.foreign 稳定；reinterpret(address,size,arena,cleanup) 需 JDK 22+）。

import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.foreign.ValueLayout;
import java.lang.invoke.MethodHandle;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;

public class R151StringAbiProbe {

    static int failures = 0;

    static void check(String what, boolean ok) {
        System.out.println((ok ? "PASS " : "FAIL ") + what);
        if (!ok) {
            failures++;
        }
    }

    /** 调用 r151$name，按 {ptr,len} ABI 读回并断言字节全等 + 边界 NUL。 */
    static void probe(SymbolLookup lib, Linker linker, Arena arena,
                      String name, byte[] expected) throws Throwable {
        String sym = "r151$" + name;
        MemorySegment target = lib.find(sym).orElseThrow(
            () -> new IllegalStateException("symbol not exported: " + sym));
        MethodHandle mh = linker.downcallHandle(
            target, FunctionDescriptor.of(ValueLayout.ADDRESS));

        MemorySegment raw = (MemorySegment) mh.invoke();
        long addr = raw.address();
        check(sym + " 返回非空指针", addr != 0);
        if (addr == 0) {
            return;
        }

        // ① ② 长度头：data[-8 .. 0) 为 i64 小端长度（ofAddress 定址 + reinterpret 定长）
        MemorySegment hdr = MemorySegment.ofAddress(addr - 8).reinterpret(8);
        long len = hdr.get(ValueLayout.JAVA_LONG_UNALIGNED, 0);
        check(sym + " 长度头 = 字节数 " + expected.length + "（实测 " + len + "）",
              len == expected.length);

        // ③ 数据区逐字节
        MemorySegment data = MemorySegment.ofAddress(addr).reinterpret(Math.max(len, 0));
        byte[] bytes = data.toArray(ValueLayout.JAVA_BYTE);
        check(sym + " 数据字节全等", Arrays.equals(bytes, expected));

        // ④ 边界 NUL
        byte nul = MemorySegment.ofAddress(addr + len).reinterpret(1)
            .get(ValueLayout.JAVA_BYTE, 0);
        check(sym + " data[len] 边界 NUL", nul == 0);

        // 附带证明：内嵌 NUL 存在（strlen 语义会截断，长度头语义不会）
        if (name.equals("binary")) {
            check(sym + " 内嵌 NUL 保留（字节[1]=0）", bytes.length > 1 && bytes[1] == 0);
        }
        // 附带证明：空串返回真指针且长度 0
        if (name.equals("empty")) {
            check(sym + " 空串长度头 = 0", len == 0);
        }

        System.out.println("  info: " + sym + " addr=0x" + Long.toHexString(addr)
            + " len=" + len + " utf8=\"" + new String(bytes, StandardCharsets.UTF_8) + "\"");
    }

    public static void main(String[] args) throws Throwable {
        if (args.length < 1) {
            System.err.println("usage: java R151StringAbiProbe <path-to-dll>");
            System.exit(2);
        }
        try (Arena arena = Arena.ofConfined()) {
            SymbolLookup lib = SymbolLookup.libraryLookup(Path.of(args[0]), arena);
            Linker linker = Linker.nativeLinker();

            probe(lib, linker, arena, "ascii",
                  "Hello, tie!".getBytes(StandardCharsets.UTF_8));
            probe(lib, linker, arena, "chinese",
                  "你好，tie 世界！".getBytes(StandardCharsets.UTF_8));
            probe(lib, linker, arena, "binary",
                  new byte[] { 65, 0, 66, 9, 67 });           // 'A' NUL 'B' TAB 'C'
            probe(lib, linker, arena, "empty", new byte[0]);
            probe(lib, linker, arena, "concat_long",
                  ("0123456789".repeat(5)).getBytes(StandardCharsets.UTF_8));
            probe(lib, linker, arena, "version",
                  "0.1.0".getBytes(StandardCharsets.UTF_8));
        }
        System.out.println(failures == 0
            ? "=== r151 string 返回 ABI 探针全部通过（{ptr,len} 单指针布局确认）==="
            : "=== " + failures + " 项失败 ===");
        System.exit(failures == 0 ? 0 : 1);
    }
}
