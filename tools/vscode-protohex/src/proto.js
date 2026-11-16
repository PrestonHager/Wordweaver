// proto.js
//
// A small .proto parser. It only pulls out what we need to decode the wire format:
// messages, their fields, and enums. Services, options, and extensions are skipped.

const fs = require("fs");
const path = require("path");

const SCALARS = new Set([
  "double", "float", "int32", "int64", "uint32", "uint64", "sint32", "sint64",
  "fixed32", "fixed64", "sfixed32", "sfixed64", "bool", "string", "bytes",
]);

function tokenize(text) {
  const tokens = [];
  const re = /\s+|\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[A-Za-z_.][\w.]*|-?\d[\w.+-]*|[{}=;<>,\[\]()]/y;
  let pos = 0;
  while (pos < text.length) {
    re.lastIndex = pos;
    const m = re.exec(text);
    if (!m) throw new Error(`Unexpected character '${text[pos]}' at offset ${pos}`);
    pos = re.lastIndex;
    const tok = m[0];
    // Skip whitespace and comments.
    if (/^\s/.test(tok) || tok.startsWith("//") || tok.startsWith("/*")) continue;
    tokens.push(tok);
  }
  return tokens;
}

class Schema {
  constructor() {
    // Full names (no leading dot) to definitions.
    this.messages = new Map();
    this.enums = new Map();
    this.loaded = new Set();
  }

  loadFile(file) {
    file = path.resolve(file);
    if (this.loaded.has(file)) return;
    this.loaded.add(file);
    const parser = new Parser(tokenize(fs.readFileSync(file, "utf8")), this, file);
    parser.parseFile();
    // Imports are relative to the importing file. We skip ones we can't find, like google/protobuf/*.
    for (const imp of parser.imports) {
      const candidate = path.resolve(path.dirname(file), imp);
      if (fs.existsSync(candidate)) this.loadFile(candidate);
    }
  }

  // Resolve every field's type name now that all files are loaded.
  link() {
    for (const msg of this.messages.values()) {
      for (const field of msg.fields.values()) {
        if (SCALARS.has(field.typeName)) {
          field.kind = "scalar";
          field.type = field.typeName;
          continue;
        }
        const full = this.resolve(field.typeName, msg.fullName);
        if (this.messages.has(full)) {
          field.kind = "message";
          field.type = full;
        } else if (this.enums.has(full)) {
          field.kind = "enum";
          field.type = full;
        } else {
          // Unknown types decode like raw wire data.
          field.kind = "unknown";
          field.type = field.typeName;
        }
      }
    }
  }

  // Protobuf scoping: try the innermost scope first, then walk outward.
  resolve(name, scope) {
    if (name.startsWith(".")) return name.slice(1);
    const parts = scope ? scope.split(".") : [];
    while (true) {
      const candidate = [...parts, name].join(".");
      if (this.messages.has(candidate) || this.enums.has(candidate)) return candidate;
      if (!parts.length) return name;
      parts.pop();
    }
  }

  // Find a message by full name, or by its short name if that's unique.
  findMessage(name) {
    if (this.messages.has(name)) return this.messages.get(name);
    const matches = [...this.messages.values()].filter((m) => m.fullName.endsWith("." + name));
    return matches.length === 1 ? matches[0] : undefined;
  }
}

class Parser {
  constructor(tokens, schema, file) {
    this.t = tokens;
    this.i = 0;
    this.schema = schema;
    this.file = file;
    this.pkg = "";
    this.imports = [];
  }

  peek() { return this.t[this.i]; }
  next() {
    if (this.i >= this.t.length) throw new Error(`${this.file}: unexpected end of file`);
    return this.t[this.i++];
  }
  expect(tok) {
    const got = this.next();
    if (got !== tok) throw new Error(`${this.file}: expected '${tok}' but got '${got}'`);
  }

  // Skip to the end of a statement, or past a whole { } block.
  skipStatement() {
    let depth = 0;
    while (this.i < this.t.length) {
      const tok = this.next();
      if (tok === "{") depth++;
      else if (tok === "}") { if (--depth <= 0) return; }
      else if (tok === ";" && depth === 0) return;
    }
  }

  parseFile() {
    while (this.i < this.t.length) {
      const tok = this.peek();
      if (tok === "package") { this.next(); this.pkg = this.next(); this.expect(";"); }
      else if (tok === "import") {
        this.next();
        let name = this.next();
        if (name === "public" || name === "weak") name = this.next();
        this.imports.push(name.slice(1, -1));
        this.expect(";");
      }
      else if (tok === "message") this.parseMessage(this.pkg);
      else if (tok === "enum") this.parseEnum(this.pkg);
      else if (tok === ";") this.next();
      else this.skipStatement();
    }
  }

  parseMessage(scope) {
    this.expect("message");
    const name = this.next();
    const fullName = scope ? `${scope}.${name}` : name;
    const msg = { name, fullName, fields: new Map() };
    this.schema.messages.set(fullName, msg);
    this.expect("{");
    this.parseMessageBody(msg);
    return msg;
  }

  parseMessageBody(msg) {
    while (this.peek() !== "}") {
      const tok = this.peek();
      if (tok === "message") this.parseMessage(msg.fullName);
      else if (tok === "enum") this.parseEnum(msg.fullName);
      else if (tok === "oneof") {
        // Oneof members are plain fields on the wire.
        this.next(); this.next(); this.expect("{");
        while (this.peek() !== "}") {
          if (this.peek() === "option" || this.peek() === ";") this.skipStatement();
          else this.parseField(msg);
        }
        this.expect("}");
      }
      else if (["option", "reserved", "extensions", "extend", ";"].includes(tok)) this.skipStatement();
      else if (tok === "map") this.parseMapField(msg);
      else this.parseField(msg);
    }
    this.expect("}");
  }

  parseField(msg) {
    let label = "";
    if (["repeated", "optional", "required"].includes(this.peek())) label = this.next();
    const typeName = this.next();
    const name = this.next();
    this.expect("=");
    const number = parseInt(this.next(), 10);
    // Field options, like [packed = false].
    let packed;
    if (this.peek() === "[") {
      const start = this.i;
      this.skipUntil("]");
      const opts = this.t.slice(start, this.i).join(" ");
      const m = /packed\s*=\s*(true|false)/.exec(opts);
      if (m) packed = m[1] === "true";
    }
    this.expect(";");
    msg.fields.set(number, { name, number, typeName, repeated: label === "repeated", packed });
  }

  // map<K, V> is sent as a repeated message with key = 1 and value = 2.
  parseMapField(msg) {
    this.expect("map"); this.expect("<");
    const keyType = this.next(); this.expect(",");
    const valueType = this.next(); this.expect(">");
    const name = this.next();
    this.expect("="); const number = parseInt(this.next(), 10);
    if (this.peek() === "[") this.skipUntil("]");
    this.expect(";");
    const entryName = `${msg.fullName}.${name}Entry`;
    const entry = { name: `${name}Entry`, fullName: entryName, fields: new Map() };
    entry.fields.set(1, { name: "key", number: 1, typeName: keyType, repeated: false });
    entry.fields.set(2, { name: "value", number: 2, typeName: valueType, repeated: false });
    this.schema.messages.set(entryName, entry);
    msg.fields.set(number, { name, number, typeName: "." + entryName, repeated: true });
  }

  skipUntil(tok) {
    while (this.next() !== tok);
  }

  parseEnum(scope) {
    this.expect("enum");
    const name = this.next();
    const fullName = scope ? `${scope}.${name}` : name;
    const values = new Map();
    this.expect("{");
    while (this.peek() !== "}") {
      const tok = this.next();
      if (tok === "option" || tok === "reserved") { this.i--; this.skipStatement(); continue; }
      if (tok === ";") continue;
      this.expect("=");
      const number = parseInt(this.next(), 10);
      if (this.peek() === "[") this.skipUntil("]");
      this.expect(";");
      if (!values.has(number)) values.set(number, tok);
    }
    this.expect("}");
    this.schema.enums.set(fullName, { name, fullName, values });
  }
}

function loadSchema(files) {
  const schema = new Schema();
  for (const file of files) schema.loadFile(file);
  schema.link();
  return schema;
}

module.exports = { loadSchema, Schema, SCALARS };
