// extension.js
//
// A read-only custom editor that shows a binary file as hex, colored by its protobuf fields.

const vscode = require("vscode");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { loadSchema } = require("./proto");
const { decode } = require("./decode");

const VIEW_TYPE = "protohex.viewer";
// Per-file spec choices live here, keyed by file URI. "none" means decode without a schema.
const OVERRIDES_KEY = "protohex.overrides";

function activate(context) {
  const provider = new ProtoHexProvider(context);
  context.subscriptions.push(
    vscode.window.registerCustomEditorProvider(VIEW_TYPE, provider, {
      webviewOptions: { retainContextWhenHidden: true },
      supportsMultipleEditorsPerDocument: true,
    }),
    vscode.commands.registerCommand("protohex.open", async (uri) => {
      uri = uri || (vscode.window.activeTextEditor && vscode.window.activeTextEditor.document.uri);
      if (!uri) {
        const picked = await vscode.window.showOpenDialog({ canSelectMany: false });
        if (!picked) return;
        uri = picked[0];
      }
      await vscode.commands.executeCommand("vscode.openWith", uri, VIEW_TYPE);
    }),
    vscode.commands.registerCommand("protohex.pickSpec", () => provider.active && provider.active.pickSpec()),
    vscode.commands.registerCommand("protohex.reload", () => provider.active && provider.active.render()),
  );
}

class ProtoHexProvider {
  constructor(context) {
    this.context = context;
    this.active = undefined;
  }

  openCustomDocument(uri) {
    return { uri, dispose() {} };
  }

  resolveCustomEditor(document, panel) {
    const view = new HexView(this, document.uri, panel);
    panel.onDidChangeViewState(() => { if (panel.active) this.active = view; });
    panel.onDidDispose(() => { view.dispose(); if (this.active === view) this.active = undefined; });
    this.active = view;
  }
}

class HexView {
  constructor(provider, uri, panel) {
    this.provider = provider;
    this.context = provider.context;
    this.uri = uri;
    this.panel = panel;
    this.watchers = [];
    const media = vscode.Uri.joinPath(this.context.extensionUri, "media");
    panel.webview.options = { enableScripts: true, localResourceRoots: [media] };
    panel.webview.html = this.html(media);
    panel.webview.onDidReceiveMessage((msg) => {
      if (msg.type === "ready" || msg.type === "reload") this.render();
      else if (msg.type === "pickSpec") this.pickSpec();
      else if (msg.type === "openSpec" && this.specPath) vscode.window.showTextDocument(vscode.Uri.file(this.specPath));
    });
  }

  dispose() {
    this.watchers.forEach((w) => w.dispose());
    clearTimeout(this.timer);
  }

  html(media) {
    const webview = this.panel.webview;
    const nonce = crypto.randomBytes(16).toString("base64");
    const script = webview.asWebviewUri(vscode.Uri.joinPath(media, "view.js"));
    const style = webview.asWebviewUri(vscode.Uri.joinPath(media, "view.css"));
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="${style}" rel="stylesheet">
</head>
<body>
<div id="toolbar">
  <button id="spec" title="Choose a different spec for this file"></button>
  <span id="status"></span>
  <span class="spacer"></span>
  <button id="nextProblem" title="Jump to the next problem">Next problem</button>
  <button id="reload" title="Decode the file again">Reload</button>
</div>
<div id="main">
  <div id="hex"><div id="hexHeader"></div><div id="hexScroll" tabindex="0"><div id="hexSpacer"></div></div></div>
  <div id="side">
    <div id="tree"></div>
    <div id="details"></div>
  </div>
</div>
<div id="tooltip"></div>
<script nonce="${nonce}" src="${script}"></script>
</body>
</html>`;
  }

  async render() {
    const message = { type: "data", fileName: path.basename(this.uri.fsPath) };
    let watchPaths = [];
    try {
      const bytes = await vscode.workspace.fs.readFile(this.uri);
      message.bytes = Buffer.from(bytes).toString("base64");
      // First, find the spec, then load the .proto files it names, then decode.
      const found = await this.findSpec();
      this.specPath = found && found.path;
      let schema;
      let spec = {};
      if (found) {
        spec = found.spec;
        const protoPaths = (spec.proto || []).map((p) => path.resolve(path.dirname(found.path), p));
        watchPaths = [found.path, ...protoPaths];
        schema = loadSchema(protoPaths);
        message.specName = spec.name || path.basename(found.path);
      } else {
        message.specName = "No spec (guessing fields)";
      }
      message.tree = decode(new Uint8Array(bytes), schema, spec);
    } catch (e) {
      message.error = e.message;
    }
    this.watch(watchPaths);
    this.panel.webview.postMessage(message);
  }

  // Re-render when the file, its spec, or its .proto files change on disk.
  watch(paths) {
    this.watchers.forEach((w) => w.dispose());
    this.watchers = [this.uri.fsPath, ...paths].map((p) => {
      const w = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(vscode.Uri.file(path.dirname(p)), path.basename(p)));
      const again = () => {
        // Saves often fire several events, so wait for them to settle.
        clearTimeout(this.timer);
        this.timer = setTimeout(() => this.render(), 150);
      };
      w.onDidChange(again);
      w.onDidCreate(again);
      return w;
    });
  }

  async findSpec() {
    const overrides = this.context.workspaceState.get(OVERRIDES_KEY, {});
    const chosen = overrides[this.uri.toString()];
    if (chosen === "none") return undefined;
    if (chosen && fs.existsSync(chosen)) return readSpec(chosen);
    // Otherwise use the first spec whose filePatterns match this file.
    const rel = vscode.workspace.asRelativePath(this.uri, false).replace(/\\/g, "/");
    const base = path.basename(this.uri.fsPath);
    for (const specPath of await allSpecPaths()) {
      const found = readSpec(specPath);
      const patterns = found.spec.filePatterns || [];
      if (patterns.some((p) => globToRegex(p).test(p.includes("/") ? rel : base))) return found;
    }
    return undefined;
  }

  async pickSpec() {
    const paths = await allSpecPaths();
    const items = paths.map((p) => {
      let name;
      try { name = readSpec(p).spec.name; } catch { name = "(can't read this spec)"; }
      return { label: name || path.basename(p), description: vscode.workspace.asRelativePath(p), value: p };
    });
    items.push({ label: "No spec", description: "Guess the fields from the wire format", value: "none" });
    items.push({ label: "Match automatically", description: "Use filePatterns to pick a spec", value: undefined });
    const pick = await vscode.window.showQuickPick(items, { placeHolder: "Which spec should decode this file?" });
    if (!pick) return;
    const overrides = { ...this.context.workspaceState.get(OVERRIDES_KEY, {}) };
    if (pick.value === undefined) delete overrides[this.uri.toString()];
    else overrides[this.uri.toString()] = pick.value;
    await this.context.workspaceState.update(OVERRIDES_KEY, overrides);
    this.render();
  }
}

// Find every *.protohex.json in the workspace, plus any listed in the protohex.specFiles setting.
async function allSpecPaths() {
  const found = await vscode.workspace.findFiles("**/*.protohex.json", "**/node_modules/**");
  const paths = found.map((u) => u.fsPath);
  const folder = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0];
  for (const p of vscode.workspace.getConfiguration("protohex").get("specFiles", [])) {
    const full = path.isAbsolute(p) || !folder ? p : path.join(folder.uri.fsPath, p);
    if (fs.existsSync(full) && !paths.includes(full)) paths.push(full);
  }
  return paths.sort();
}

function readSpec(specPath) {
  try {
    return { path: specPath, spec: JSON.parse(fs.readFileSync(specPath, "utf8")) };
  } catch (e) {
    throw new Error(`Couldn't read spec ${specPath}: ${e.message}`);
  }
}

// Turn a simple glob into a regex. Supports *, **, ?, and {a,b}.
function globToRegex(glob) {
  let re = "";
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];
    if (c === "*" && glob[i + 1] === "*") { re += ".*"; i++; if (glob[i + 1] === "/") i++; }
    else if (c === "*") re += "[^/]*";
    else if (c === "?") re += "[^/]";
    else if (c === "{") re += "(?:";
    else if (c === "}") re += ")";
    else if (c === ",") re += "|";
    else re += c.replace(/[.+^$()|[\]\\]/g, "\\$&");
  }
  return new RegExp(`^${re}$`, "i");
}

function deactivate() {}

module.exports = { activate, deactivate, globToRegex };
