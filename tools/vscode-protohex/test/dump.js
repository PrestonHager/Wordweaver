// Print the decoded tree for a file, so you can check a spec without opening VS Code.
// Usage: node test/dump.js <spec.protohex.json> <file>

const fs = require("fs");
const path = require("path");
const { loadSchema } = require("../src/proto");
const { decode } = require("../src/decode");

const [specPath, filePath] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const schema = loadSchema((spec.proto || []).map((p) => path.resolve(path.dirname(specPath), p)));
const tree = decode(new Uint8Array(fs.readFileSync(filePath)), schema, spec);

let problems = 0;
function print(node, depth) {
  const range = `${node.start.toString(16).padStart(4, "0")}-${node.end.toString(16).padStart(4, "0")}`;
  const bits = [node.name, node.type && `<${node.type}>`, node.value, node.problem && `!! ${node.problem}`];
  if (node.problem) problems++;
  // Skip tag and length leaves so the output stays readable.
  if (node.kind !== "tag" && node.kind !== "len" && !(node.kind === "value" && node.name === "value")) {
    console.log(`${range} ${"  ".repeat(depth)}${bits.filter(Boolean).join(" ")}`);
  }
  for (const child of node.children || []) print(child, depth + 1);
}
print(tree, 0);
console.log(`\n${problems} problem(s)`);
process.exitCode = problems ? 1 : 0;
