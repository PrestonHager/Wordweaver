// decode.js
//
// Turns file bytes into a tree of byte ranges, using a spec and the .proto schema it points at.
// Every node has a start and end offset, so the hex view can color the bytes it covers.

const WIRE_NAMES = ["VARINT", "I64", "LEN", "SGROUP", "EGROUP", "I32"];
const VARINT_TYPES = new Set(["int32", "int64", "uint32", "uint64", "sint32", "sint64", "bool"]);
const I64_TYPES = new Set(["fixed64", "sfixed64", "double"]);
const I32_TYPES = new Set(["fixed32", "sfixed32", "float"]);

class DecodeError extends Error {
  constructor(message, pos) {
    super(message);
    this.pos = pos;
  }
}

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(bytes, start, end) {
  let crc = 0xffffffff;
  for (let i = start; i < end; i++) crc = CRC_TABLE[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function hex(bytes, start, end, max = 32) {
  const out = [];
  for (let i = start; i < Math.min(end, start + max); i++) out.push(bytes[i].toString(16).padStart(2, "0"));
  return out.join(" ") + (end - start > max ? " …" : "");
}

const utf8 = new TextDecoder("utf-8", { fatal: true });

class Decoder {
  constructor(bytes, schema, spec) {
    this.bytes = bytes;
    this.view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    this.schema = schema;
    this.spec = spec || {};
    this.typeMaps = this.spec.typeMaps || {};
  }

  readVarint(pos, end) {
    let value = 0n;
    let shift = 0n;
    while (true) {
      if (pos >= end) throw new DecodeError("Ran out of bytes in the middle of a varint", pos);
      const byte = this.bytes[pos++];
      value |= BigInt(byte & 0x7f) << shift;
      if (!(byte & 0x80)) return [value, pos];
      shift += 7n;
      if (shift > 70n) throw new DecodeError("Varint is longer than 10 bytes", pos);
    }
  }

  need(pos, count, end) {
    if (pos + count > end) throw new DecodeError(`Needed ${count} bytes but only ${end - pos} are left`, pos);
  }

  // Look up an entry in one of the spec's typeMaps. Entries are either a message name or { name, message }.
  mapEntry(mapName, key) {
    const map = this.typeMaps[mapName];
    if (!map) return undefined;
    const entry = map[String(key)];
    if (entry === undefined) return undefined;
    return typeof entry === "string" ? { message: entry } : entry;
  }

  // Decode the whole file, using the spec's layout if it has one.
  decodeFile() {
    const end = this.bytes.length;
    let layout = this.spec.layout;
    if (!layout) {
      layout = [{ name: this.spec.root ? this.spec.root.split(".").pop() : "message", type: "message", length: "rest", message: this.spec.root }];
    }
    const { nodes } = this.decodeLayout(layout, 0, end, {}, true);
    return { name: this.spec.name || "file", kind: "group", start: 0, end, children: nodes };
  }

  // Decode a list of layout fields. With `catchErrors`, a failure turns the rest into an error node.
  decodeLayout(fields, pos, end, scope, catchErrors) {
    const nodes = [];
    for (const f of fields) {
      try {
        pos = this.decodeLayoutField(f, pos, end, scope, nodes);
      } catch (e) {
        if (!catchErrors || !(e instanceof DecodeError)) throw e;
        nodes.push(errorNode(e.message, pos, end));
        return { nodes, pos: end };
      }
    }
    return { nodes, pos };
  }

  decodeLayoutField(f, pos, end, scope, nodes) {
    const name = f.name || f.type;
    const key = `layout.${name}`;
    const start = pos;
    switch (f.type) {
      case "bytes": {
        const length = this.lengthOf(f.length, pos, end, scope);
        this.need(pos, length, end);
        pos += length;
        const node = { name, type: `bytes[${length}]`, kind: "header", key, start, end: pos, value: hex(this.bytes, start, pos) };
        if (f.expect) {
          const want = f.expect.replace(/[\s:]/g, "").toLowerCase();
          const got = hex(this.bytes, start, pos, Infinity).replace(/ /g, "");
          if (want !== got) node.problem = `Expected ${want}`;
        }
        scope[name] = { start, end: pos };
        nodes.push(node);
        return pos;
      }
      case "uint": {
        const size = f.size || 4;
        this.need(pos, size, end);
        let value = 0n;
        for (let i = 0; i < size; i++) {
          const b = BigInt(this.bytes[pos + (f.endian === "little" ? size - 1 - i : i)]);
          value = (value << 8n) | b;
        }
        pos += size;
        scope[name] = { start, end: pos, value: Number(value) };
        nodes.push({ name, type: `uint${size * 8} ${f.endian || "big"}`, kind: "header", key, start, end: pos, value: this.withName(f, value) });
        return pos;
      }
      case "varint": {
        const [value, next] = this.readVarint(pos, end);
        pos = next;
        scope[name] = { start, end: pos, value: Number(value), label: this.withName(f, value) };
        nodes.push({ name, type: "varint", kind: "header", key, start, end: pos, value: this.withName(f, value) });
        return pos;
      }
      case "message": {
        const length = this.lengthOf(f.length, pos, end, scope);
        this.need(pos, length, end);
        let msgName = f.message;
        if (f.messageFrom) {
          const sel = scope[f.messageFrom.field];
          const entry = sel && this.mapEntry(f.messageFrom.map, sel.value);
          msgName = entry && entry.message;
        }
        const msg = msgName ? this.findMessage(msgName) : undefined;
        const node = {
          name, kind: "group", key, start, end: pos + length,
          type: msg ? msg.name : msgName ? `${msgName} (not in schema)` : "unknown message",
          children: this.decodeMessage(pos, pos + length, msg),
        };
        if (!node.children.length) node.value = "(empty)";
        scope[name] = { start, end: pos + length };
        nodes.push(node);
        return pos + length;
      }
      case "crc32": {
        this.need(pos, 4, end);
        const from = scope[f.from];
        const got = f.endian === "little" ? this.view.getUint32(pos, true) : this.view.getUint32(pos, false);
        const node = { name, type: "crc32", kind: "crc", key, start, end: pos + 4, value: `0x${got.toString(16).padStart(8, "0")}` };
        if (from) {
          const want = crc32(this.bytes, from.start, start);
          if (want === got) node.value += " ✓";
          else node.problem = `CRC mismatch, expected 0x${want.toString(16).padStart(8, "0")}`;
        }
        nodes.push(node);
        return pos + 4;
      }
      case "repeat": {
        // Repeat until the end of the bytes, or a count from an earlier field.
        const count = typeof f.count === "number" ? f.count : f.count ? scope[f.count].value : Infinity;
        for (let i = 0; i < count && pos < end; i++) {
          const inner = Object.create(scope);
          const itemStart = pos;
          const result = this.decodeLayout(f.fields || [], pos, end, inner, true);
          pos = result.pos;
          const label = (f.label || `${name}[{index}]`)
            .replace("{index}", i)
            .replace(/\{(\w+)\}/g, (m, k) => (inner[k] ? inner[k].label ?? inner[k].value : m));
          nodes.push({ name: label, kind: "group", key: `${key}.item`, start: itemStart, end: pos, children: result.nodes });
          // If this item hit an error it ate the rest of the bytes, so we're done.
          if (result.nodes.some((n) => n.kind === "error")) break;
        }
        return pos;
      }
      default:
        throw new Error(`Unknown layout field type '${f.type}' in spec`);
    }
  }

  lengthOf(length, pos, end, scope) {
    if (typeof length === "number") return length;
    if (length === "rest" || length === undefined) return end - pos;
    const ref = scope[length];
    if (!ref || ref.value === undefined) throw new DecodeError(`Spec refers to unknown length field '${length}'`, pos);
    return ref.value;
  }

  withName(f, value) {
    if (f.names) {
      const entry = this.mapEntry(f.names, value);
      if (entry && entry.name) return `${value} (${entry.name})`;
    }
    return String(value);
  }

  findMessage(name) {
    return this.schema ? this.schema.findMessage(name) : undefined;
  }

  // Decode protobuf fields between start and end. Errors become an error node instead of throwing,
  // unless `strict` is on (used when guessing whether unknown bytes are a message).
  decodeMessage(start, end, msg, strict = false) {
    const nodes = [];
    const counts = new Map();
    // Varint values we've seen so far, so a later bytes field can pick its type from them.
    const seen = {};
    let pos = start;
    while (pos < end) {
      const fieldStart = pos;
      try {
        const [tag, afterTag] = this.readVarint(pos, end);
        const number = Number(tag >> 3n);
        const wire = Number(tag & 7n);
        if (number === 0) throw new DecodeError("Field number 0 isn't allowed", pos);
        pos = afterTag;
        const field = msg && msg.fields.get(number);
        const count = counts.get(number) || 0;
        counts.set(number, count + 1);
        let name = field ? field.name : `#${number}`;
        // A packed field is one run of values, so it doesn't get an index.
        if (field && field.repeated && !(wire === 2 && isPackable(field))) name += `[${count}]`;
        const key = `${msg ? msg.name : "?"}.${field ? field.name : number}`;
        const node = { name, kind: "field", key, start: fieldStart, children: [] };
        node.children.push({
          name: "tag", kind: "tag", start: fieldStart, end: pos,
          value: `field ${number}, wire type ${wire} (${WIRE_NAMES[wire] || "?"})`,
        });
        pos = this.decodeValue(node, field, wire, pos, end, seen, msg, strict);
        node.end = pos;
        nodes.push(node);
      } catch (e) {
        if (strict || !(e instanceof DecodeError)) throw e;
        nodes.push(errorNode(e.message, fieldStart, end));
        break;
      }
    }
    return nodes;
  }

  decodeValue(node, field, wire, pos, end, seen, msg, strict) {
    const type = field ? field.type : undefined;
    const kind = field ? field.kind : "unknown";
    const valueStart = pos;
    const leaf = (value, endPos, extra = {}) => node.children.push({ name: "value", kind: "value", start: valueStart, end: endPos, value, ...extra });
    // Note a mismatch between the schema and the wire, but keep decoding by wire type.
    const expected = field && expectedWire(field);
    if (expected !== undefined && expected !== wire && !(wire === 2 && isPackable(field))) {
      node.problem = `Schema says ${type} (wire type ${expected}) but the wire has type ${wire}`;
    }

    switch (wire) {
      case 0: {
        const [raw, next] = this.readVarint(pos, end);
        const value = this.formatVarint(raw, field, node.problem ? undefined : type, kind);
        node.type = field ? type.split(".").pop() : "varint";
        node.value = value;
        if (field) seen[field.name] = Number(raw);
        leaf(value, next);
        return next;
      }
      case 1: {
        this.need(pos, 8, end);
        const value = type === "double" ? String(this.view.getFloat64(pos, true))
          : type === "sfixed64" ? String(this.view.getBigInt64(pos, true))
            : String(this.view.getBigUint64(pos, true));
        node.type = type || "i64";
        node.value = value;
        leaf(value, pos + 8);
        return pos + 8;
      }
      case 5: {
        this.need(pos, 4, end);
        const value = type === "float" ? String(this.view.getFloat32(pos, true))
          : type === "sfixed32" ? String(this.view.getInt32(pos, true))
            : String(this.view.getUint32(pos, true));
        node.type = type || "i32";
        node.value = value;
        leaf(value, pos + 4);
        return pos + 4;
      }
      case 2: {
        const lenStart = pos;
        const [rawLen, afterLen] = this.readVarint(pos, end);
        const length = Number(rawLen);
        node.children.push({ name: "length", kind: "len", start: lenStart, end: afterLen, value: String(length) });
        pos = afterLen;
        this.need(pos, length, end);
        const contentEnd = pos + length;
        this.decodeLen(node, field, pos, contentEnd, seen, msg, strict);
        return contentEnd;
      }
      default:
        throw new DecodeError(`Wire type ${wire} isn't supported`, pos);
    }
  }

  decodeLen(node, field, start, end, seen, msg, strict) {
    const kind = field ? field.kind : "unknown";
    const type = field ? field.type : undefined;
    const leaf = (value, extra = {}) => node.children.push({ name: "value", kind: "value", start, end, value, ...extra });

    // First, a message with a known type.
    if (kind === "message") {
      const sub = this.schema.messages.get(type);
      node.type = sub.name;
      node.children.push(...this.decodeMessage(start, end, sub, strict));
      if (start === end) node.value = "(empty)";
      return;
    }
    // Then packed repeated numbers, like `repeated uint32 form`.
    if (field && isPackable(field)) {
      node.type = `${type.split(".").pop()}[] packed`;
      let pos = start;
      let i = 0;
      const values = [];
      while (pos < end) {
        const itemStart = pos;
        let next;
        let value;
        if (expectedWire(field) === 0) {
          const [raw, n] = this.readVarint(pos, end);
          value = this.formatVarint(raw, field, type, kind);
          next = n;
        } else {
          const size = expectedWire(field) === 1 ? 8 : 4;
          this.need(pos, size, end);
          value = size === 8 ? String(this.view.getBigUint64(pos, true)) : String(this.view.getUint32(pos, true));
          if (type === "float") value = String(this.view.getFloat32(pos, true));
          if (type === "double") value = String(this.view.getFloat64(pos, true));
          next = pos + size;
        }
        values.push(value);
        node.children.push({ name: `[${i++}]`, kind: "value", start: itemStart, end: next, value });
        pos = next;
      }
      node.value = `[${values.join(", ")}]`;
      return;
    }
    if (type === "string") {
      node.type = "string";
      let text;
      try { text = utf8.decode(this.bytes.subarray(start, end)); }
      catch { node.problem = "Not valid UTF-8"; text = hex(this.bytes, start, end); }
      node.value = JSON.stringify(text);
      leaf(node.value);
      return;
    }
    if (type === "bytes") {
      // The spec can say a bytes field holds a message picked by a sibling field, like Patch upserts.
      const dyn = msg && this.spec.bytesTypes && this.spec.bytesTypes[`${msg.fullName}.${field.name}`];
      if (dyn) {
        const sel = seen[dyn.from];
        const entry = sel !== undefined && this.mapEntry(dyn.map, sel);
        const sub = entry && this.findMessage(entry.message);
        if (sub) {
          node.type = `bytes → ${sub.name}`;
          node.children.push(...this.decodeMessage(start, end, sub, strict));
          if (start === end) node.value = "(empty)";
          return;
        }
      }
      node.type = `bytes[${end - start}]`;
      node.value = hex(this.bytes, start, end);
      leaf(node.value);
      return;
    }
    // Finally, no schema info, so guess: a nested message, then text, then raw bytes.
    if (end > start) {
      try {
        const children = this.decodeMessage(start, end, undefined, true);
        node.type = "message?";
        node.children.push(...children);
        return;
      } catch (e) {
        if (!(e instanceof DecodeError)) throw e;
      }
      try {
        const text = utf8.decode(this.bytes.subarray(start, end));
        if (!/[\x00-\x08\x0e-\x1f]/.test(text)) {
          node.type = "string?";
          node.value = JSON.stringify(text);
          leaf(node.value);
          return;
        }
      } catch { /* Not text, so it's raw bytes. */ }
    }
    node.type = `bytes[${end - start}]`;
    node.value = hex(this.bytes, start, end);
    leaf(node.value);
  }

  formatVarint(raw, field, type, kind) {
    if (kind === "enum") {
      const e = this.schema.enums.get(type);
      const signed = BigInt.asIntN(32, raw);
      const name = e && e.values.get(Number(signed));
      return name ? `${name} (${signed})` : String(signed);
    }
    switch (type) {
      case "int32": return String(BigInt.asIntN(32, raw));
      case "int64": return String(BigInt.asIntN(64, raw));
      case "sint32":
      case "sint64": return String((raw >> 1n) ^ -(raw & 1n));
      case "bool": return raw ? "true" : "false";
      default: return String(raw);
    }
  }
}

function expectedWire(field) {
  if (field.kind === "message") return 2;
  if (field.kind === "enum") return 0;
  if (field.kind !== "scalar") return undefined;
  if (VARINT_TYPES.has(field.type)) return 0;
  if (I64_TYPES.has(field.type)) return 1;
  if (I32_TYPES.has(field.type)) return 5;
  return 2;
}

function isPackable(field) {
  return field.repeated && field.packed !== false && (field.kind === "enum" || (field.kind === "scalar" && expectedWire(field) !== 2));
}

function errorNode(message, start, end) {
  return { name: "error", kind: "error", start, end, value: message, problem: message };
}

function decode(bytes, schema, spec) {
  return new Decoder(bytes, schema, spec).decodeFile();
}

module.exports = { decode, crc32 };
