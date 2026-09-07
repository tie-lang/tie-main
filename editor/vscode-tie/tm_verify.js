// 本地验证 tie.tmLanguage.json 的 token 分类（不依赖 VSCode 运行）
// 用法：node tm_verify.js
const fs = require('fs');
const path = require('path');
const vsctm = require('vscode-textmate');
const oniguruma = require('vscode-oniguruma');

const GRAMMAR = path.join(__dirname, 'syntaxes', 'tie.tmLanguage.json');

async function main() {
    const wasmPath = path.join(__dirname, 'node_modules', 'vscode-oniguruma', 'release', 'onig.wasm');
    const wasm = fs.readFileSync(wasmPath).buffer;
    await oniguruma.loadWASM(wasm);
    const raw = fs.readFileSync(GRAMMAR, 'utf-8');
    const grammar = await vsctm.parseRawGrammar(raw, GRAMMAR);
    const registry = new vsctm.Registry({
        onigLib: Promise.resolve({
            createOnigScanner: (sources) => new oniguruma.OnigScanner(sources),
            createOnigString: (str) => new oniguruma.OnigString(str),
        }),
    });
    const ruleStack = null;
    const gram = await registry.addGrammar(grammar);

    const samples = [
        'var err_vals = table_new_string()',
        'err_vals = table_new_string()',
        'err_vals = err_vals + 1',
        'func main() {',
        '    var x: i64 = 42',
        '    x = 99',
        'namespace foo',
        'struct Point {',
        'import "x.tie" as y',
        '    println("hi")',
        'tsha.tsha1f(msg, 8)',
        'var name: string = "abc"',
    ];
    for (const line of samples) {
        const r = gram.tokenizeLine(line, ruleStack);
        console.log('LINE: ' + line);
        for (const t of r.tokens) {
            const scopes = t.scopes.join(' ');
            console.log('   [' + line.slice(t.startIndex, t.endIndex) + '] -> ' + scopes);
        }
    }
}

main().catch((e) => { console.error(e); process.exit(1); });