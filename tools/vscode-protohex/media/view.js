// view.js
//
// The webview side: draws the hex grid, the field tree, and the details for the selected field.

(function () {
  const vscode = acquireVsCodeApi();
  const COLS = 16;
  const ROW_H = 20;
  // Node kinds that stand for a whole field, as opposed to its tag, length, or value bytes.
  const FIELD_KINDS = new Set(["field", "header", "crc", "error", "group"]);

  const $ = (id) => document.getElementById(id);
  const hexScroll = $("hexScroll");
  const spacer = $("hexSpacer");
  const tree = $("tree");
  const details = $("details");
  const tooltip = $("tooltip");

  let bytes = new Uint8Array();
  let nodes = [];
  let leafAt = new Int32Array();
  let problems = [];
  let selected = -1;
  let hovered = -1;
  let caret = -1;
  let problemIndex = -1;
  // Which tree rows are expanded, by path, so a reload keeps them open.
  const expanded = new Set(["0"]);

  $("reload").onclick = () => vscode.postMessage({ type: "reload" });
  $("spec").onclick = () => vscode.postMessage({ type: "pickSpec" });
  $("nextProblem").onclick = () => {
    if (!problems.length) return;
    problemIndex = (problemIndex + 1) % problems.length;
    select(problems[problemIndex], true);
  };

  window.addEventListener("message", (event) => {
    const msg = event.data;
    if (msg.type !== "data") return;
    load(msg);
  });

  function load(msg) {
    $("spec").textContent = msg.specName || "Choose spec";
    if (msg.error) {
      $("status").textContent = msg.error;
      $("status").className = "bad";
    }
    bytes = msg.bytes ? Uint8Array.from(atob(msg.bytes), (c) => c.charCodeAt(0)) : new Uint8Array();
    // First, flatten the tree so every node has an id and knows its parent.
    nodes = [];
    problems = [];
    leafAt = new Int32Array(bytes.length).fill(-1);
    if (msg.tree) walk(msg.tree, -1, 0, "0");
    // Then mark each byte with the deepest node covering it. Children come after parents, so they win.
    for (const node of nodes) {
      for (let i = node.start; i < node.end && i < bytes.length; i++) leafAt[i] = node.id;
    }
    if (!msg.error) {
      const covered = leafAt.reduce((n, id) => n + (id > 0 ? 1 : 0), 0);
      $("status").textContent = `${bytes.length} bytes · ${problems.length} problem${problems.length === 1 ? "" : "s"}` +
        (covered < bytes.length ? ` · ${bytes.length - covered} bytes not covered` : "");
      $("status").className = problems.length ? "bad" : "";
    }
    $("nextProblem").disabled = !problems.length;
    problemIndex = -1;
    // Keep the selection on the same path after a reload, if it's still there.
    const oldPath = selected >= 0 && selected < nodes.length ? nodes[selected].path : undefined;
    selected = -1;
    hovered = -1;
    if (caret >= bytes.length) caret = -1;
    spacer.style.height = `${Math.ceil(bytes.length / COLS) * ROW_H}px`;
    renderTree();
    const again = oldPath && nodes.find((n) => n.path === oldPath);
    if (again) select(again.id, false);
    else { renderRows(); renderDetails(); }
  }

  function walk(node, parent, depth, path) {
    const id = nodes.length;
    const flat = { ...node, id, parent, depth, path, children: [] };
    nodes.push(flat);
    if (parent >= 0) nodes[parent].children.push(id);
    if (node.problem) problems.push(id);
    (node.children || []).forEach((child, i) => walk(child, id, depth + 1, `${path}.${i}`));
  }

  // The field a byte belongs to, skipping past its tag, length, and value leaves.
  function fieldOf(id) {
    while (id > 0 && !FIELD_KINDS.has(nodes[id].kind)) id = nodes[id].parent;
    return id;
  }

  // Same field name, same color, wherever it shows up.
  function hue(key) {
    let h = 0;
    for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0;
    return h % 360;
  }

  function colorOf(id) {
    const field = nodes[fieldOf(id)];
    if (!field) return "";
    if (field.kind === "error" || nodes[id].problem) return "var(--bad-bg)";
    const h = hue(field.key || field.name);
    const kind = nodes[id].kind;
    // Tags and lengths are dimmer, so the values stand out.
    const alpha = kind === "tag" || kind === "len" ? 0.14 : 0.38;
    return `hsla(${h}, 70%, 55%, ${alpha})`;
  }

  // Draw only the rows that are on screen, so big files stay fast.
  function renderRows() {
    const first = Math.max(0, Math.floor(hexScroll.scrollTop / ROW_H) - 5);
    const count = Math.ceil(hexScroll.clientHeight / ROW_H) + 10;
    const last = Math.min(Math.ceil(bytes.length / COLS), first + count);
    const sel = selected >= 0 ? nodes[selected] : undefined;
    const hov = hovered >= 0 ? nodes[hovered] : undefined;
    const html = [];
    for (let row = first; row < last; row++) {
      const base = row * COLS;
      let hexCells = "";
      let asciiCells = "";
      for (let c = 0; c < COLS; c++) {
        const i = base + c;
        if (i >= bytes.length) {
          hexCells += `<span class="b empty"></span>`;
          continue;
        }
        const id = leafAt[i];
        const cls = ["b"];
        if (sel && i >= sel.start && i < sel.end) cls.push("sel");
        if (hov && i >= hov.start && i < hov.end) cls.push("hov");
        if (i === caret) cls.push("caret");
        // Mark where each field starts, so neighbors with the same color stay apart.
        if (id >= 0 && nodes[fieldOf(id)].start === i) cls.push("start");
        const bg = id >= 0 ? colorOf(id) : "";
        const style = bg ? ` style="background:${bg}"` : "";
        const b = bytes[i];
        hexCells += `<span class="${cls.join(" ")}" data-i="${i}"${style}>${b.toString(16).padStart(2, "0")}</span>`;
        const ch = b >= 0x20 && b < 0x7f ? escapeHtml(String.fromCharCode(b)) : "·";
        asciiCells += `<span class="${cls.join(" ")}" data-i="${i}"${style}>${ch}</span>`;
      }
      html.push(`<div class="row" style="top:${row * ROW_H}px"><span class="off">${base.toString(16).padStart(8, "0")}</span><span class="hexcells">${hexCells}</span><span class="ascii">${asciiCells}</span></div>`);
    }
    spacer.innerHTML = html.join("");
  }

  hexScroll.addEventListener("scroll", () => requestAnimationFrame(renderRows));
  window.addEventListener("resize", () => renderRows());

  hexScroll.addEventListener("mousemove", (e) => {
    const i = byteAt(e.target);
    const id = i >= 0 && leafAt[i] >= 0 ? fieldOf(leafAt[i]) : -1;
    if (id !== hovered) {
      hovered = id;
      renderRows();
    }
    if (id > 0) {
      const leaf = nodes[leafAt[i]];
      const field = nodes[id];
      tooltip.innerHTML = `<b>${escapeHtml(pathName(id))}</b>${field.type ? ` <i>${escapeHtml(field.type)}</i>` : ""}` +
        (leaf !== field ? `<br>${escapeHtml(leaf.name)}: ${escapeHtml(leaf.value || "")}` : field.value ? `<br>${escapeHtml(field.value)}` : "") +
        (field.problem ? `<br><span class="bad">${escapeHtml(field.problem)}</span>` : "");
      tooltip.style.display = "block";
      tooltip.style.left = `${Math.min(e.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8)}px`;
      tooltip.style.top = `${e.clientY + 16}px`;
    } else {
      tooltip.style.display = "none";
    }
  });
  hexScroll.addEventListener("mouseleave", () => {
    hovered = -1;
    tooltip.style.display = "none";
    renderRows();
  });

  // Clicking a byte selects its field. Clicking the same byte again walks up to the parent.
  hexScroll.addEventListener("click", (e) => {
    const i = byteAt(e.target);
    if (i < 0) return;
    const again = i === caret;
    caret = i;
    const leaf = leafAt[i];
    if (leaf < 0) { selected = -1; renderRows(); renderDetails(); return; }
    let id = fieldOf(leaf);
    if (again && selected > 0 && isAncestorOrSelf(selected, id) && nodes[selected].parent > 0) id = nodes[selected].parent;
    select(id, false, true);
  });

  // Arrow keys move the caret a byte at a time.
  hexScroll.addEventListener("keydown", (e) => {
    const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -COLS, ArrowDown: COLS };
    if (!(e.key in moves) || !bytes.length) return;
    e.preventDefault();
    caret = Math.max(0, Math.min(bytes.length - 1, (caret < 0 ? 0 : caret) + moves[e.key]));
    const id = leafAt[caret] >= 0 ? fieldOf(leafAt[caret]) : -1;
    if (id >= 0) select(id, true, true);
    else { scrollToByte(caret); renderRows(); renderDetails(); }
  });

  function isAncestorOrSelf(a, b) {
    for (let id = b; id >= 0; id = nodes[id].parent) if (id === a) return true;
    return false;
  }

  function byteAt(el) {
    return el && el.dataset && el.dataset.i !== undefined ? parseInt(el.dataset.i, 10) : -1;
  }

  function select(id, scrollHex, keepCaret) {
    selected = id;
    if (!keepCaret && id >= 0 && !(caret >= nodes[id].start && caret < nodes[id].end)) caret = nodes[id].start;
    // Open every ancestor in the tree, so the selected row is visible.
    for (let p = nodes[id].parent; p >= 0; p = nodes[p].parent) expanded.add(nodes[p].path);
    renderTree();
    const row = tree.querySelector(`[data-id="${id}"]`);
    if (row) row.scrollIntoView({ block: "nearest" });
    if (scrollHex) scrollToByte(keepCaret ? caret : nodes[id].start);
    renderRows();
    renderDetails();
  }

  function scrollToByte(i) {
    const top = Math.floor(i / COLS) * ROW_H;
    if (top < hexScroll.scrollTop || top > hexScroll.scrollTop + hexScroll.clientHeight - ROW_H * 2) {
      hexScroll.scrollTop = Math.max(0, top - hexScroll.clientHeight / 3);
    }
  }

  function renderTree() {
    const html = [];
    const add = (id) => {
      const n = nodes[id];
      const open = expanded.has(n.path);
      const hasKids = n.children.length > 0;
      const swatch = id > 0 ? `<span class="swatch" style="background:${colorOf(id)}"></span>` : "";
      html.push(
        `<div class="node${id === selected ? " sel" : ""}${n.problem ? " problem" : ""}" data-id="${id}" style="padding-left:${n.depth * 14 + 4}px">` +
        `<span class="twisty">${hasKids ? (open ? "▾" : "▸") : ""}</span>${swatch}` +
        `<span class="name">${escapeHtml(n.name)}</span>` +
        (n.type ? ` <span class="type">${escapeHtml(n.type)}</span>` : "") +
        (n.value && !(hasKids && open) ? ` <span class="value">${escapeHtml(n.value)}</span>` : "") +
        `</div>`,
      );
      if (open) n.children.forEach(add);
    };
    if (nodes.length) add(0);
    tree.innerHTML = html.join("");
  }

  tree.addEventListener("click", (e) => {
    const row = e.target.closest(".node");
    if (!row) return;
    const id = parseInt(row.dataset.id, 10);
    const n = nodes[id];
    // The arrow toggles, and clicking an already selected row toggles too.
    if (e.target.classList.contains("twisty") || id === selected) {
      if (expanded.has(n.path)) expanded.delete(n.path);
      else expanded.add(n.path);
    }
    select(id, true);
  });

  function pathName(id) {
    const parts = [];
    for (let p = id; p > 0; p = nodes[p].parent) {
      if (FIELD_KINDS.has(nodes[p].kind)) parts.unshift(nodes[p].name);
    }
    return parts.join(" › ");
  }

  function renderDetails() {
    const rows = [];
    if (selected >= 0) {
      const n = nodes[selected];
      rows.push(["Path", pathName(selected) || n.name]);
      if (n.type) rows.push(["Type", n.type]);
      rows.push(["Range", `0x${n.start.toString(16)}–0x${n.end.toString(16)} (${n.end - n.start} bytes)`]);
      if (n.value) rows.push(["Value", n.value]);
      if (n.problem) rows.push(["Problem", n.problem, "bad"]);
    }
    // Then a small data inspector for the byte under the caret.
    if (caret >= 0 && caret < bytes.length) {
      const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
      const left = bytes.length - caret;
      rows.push(["Offset", `0x${caret.toString(16)} (${caret})`, "sep"]);
      rows.push(["u8 / i8", `${bytes[caret]} / ${view.getInt8(caret)}`]);
      if (left >= 2) rows.push(["u16 le / be", `${view.getUint16(caret, true)} / ${view.getUint16(caret, false)}`]);
      if (left >= 4) rows.push(["u32 le / be", `${view.getUint32(caret, true)} / ${view.getUint32(caret, false)}`]);
      const v = varintAt(caret);
      if (v) rows.push(["varint", `${v.value} (${v.length} byte${v.length === 1 ? "" : "s"})`]);
      rows.push(["binary", bytes[caret].toString(2).padStart(8, "0")]);
    }
    details.innerHTML = rows.map(([k, v, cls]) => `<div class="drow ${cls || ""}"><span class="k">${k}</span><span class="v">${escapeHtml(v)}</span></div>`).join("");
  }

  function varintAt(pos) {
    let value = 0n;
    let shift = 0n;
    for (let i = pos; i < bytes.length && i < pos + 10; i++) {
      value |= BigInt(bytes[i] & 0x7f) << shift;
      if (!(bytes[i] & 0x80)) return { value, length: i - pos + 1 };
      shift += 7n;
    }
    return undefined;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  // Column header for the hex grid.
  $("hexHeader").innerHTML = `<span class="off">offset</span><span class="hexcells">${[...Array(COLS).keys()].map((i) => `<span class="b">${i.toString(16).padStart(2, "0")}</span>`).join("")}</span><span class="ascii">ascii</span>`;

  vscode.postMessage({ type: "ready" });
})();
