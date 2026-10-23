// Static network explorer: the controls of pypowsybl-jupyter's network_explorer
// rebuilt in the page, driving its own NAD, SLD and map widget scripts through a
// stand-in for the anywidget model. Diagrams come from the gzip JSON that
// gfm6w/explorer.py recorded, fetched when first shown. Each widget renders when
// its tab is first opened, since the map cannot lay out while hidden.

const WIDGETS = "assets/js/pypowsybl-jupyter/";
const HISTORY = 10;
const scripts = {};
const sheets = new Set();

const STYLE = `
.pje { display: flex; flex-wrap: wrap; gap: 4px 12px; font: 13px system-ui, sans-serif;
  color: #1b2a3a; margin: 0.5rem 0 1rem; }
.pje-left { display: flex; flex-direction: column; width: 300px; height: 700px;
  flex: none; gap: 4px; padding-top: 26px; }
.pje-title { position: absolute; margin-top: -26px; font-weight: 600; }
.pje-row { display: flex; align-items: flex-start; gap: 6px; }
.pje-row > span { width: 52px; text-align: right; padding-top: 4px; flex: none; }
.pje-row input, .pje-row select { flex: 1; min-width: 0; font: inherit;
  border: 1px solid #c4d0dc; border-radius: 3px; }
.pje-row input { padding: 3px 6px; }
.pje-found { flex: 80; } .pje-history { flex: 18; }
.pje-found select, .pje-history select { height: 100%; }
.pje-right { flex: 1 1 520px; min-width: 0; height: 700px; display: flex;
  flex-direction: column; padding-top: 26px; }
.pje-tabs { display: flex; border-bottom: 1px solid #c4d0dc; }
.pje-tabs button { font: inherit; background: #f6f8fa; border: 1px solid #c4d0dc;
  border-bottom: none; margin-right: 2px; padding: 5px 14px; cursor: pointer;
  min-width: 140px; text-align: left; }
.pje-tabs button.on { background: #ffffff; border-top: 2px solid #1486c2;
  margin-bottom: -1px; }
.pje-panel { display: none; flex: 1; border: 1px solid #c4d0dc; border-top: none;
  padding: 6px; overflow: auto; }
.pje-panel.on { display: flex; flex-direction: column; }
.pje-panel > div:last-child { flex: 1; min-height: 0; }
.pje-panel :is(.svg-nad-viewer-widget, .svg-sld-viewer-widget, .network-map-viewer-widget) {
  display: block; height: 100%; box-sizing: border-box; }
.pje-panel :is(.svg-nad-viewer-widget, .network-map-viewer-widget) > div,
.pje-panel :is(.svg-nad-viewer-widget, .svg-sld-viewer-widget) :is(div:has(> svg), div > svg) {
  width: 100% !important; height: 100% !important; display: block; }
.pje-depth { display: flex; align-items: center; gap: 8px; height: 28px; }
.pje-depth input { width: 160px; }
.pje-note { color: #5a6b7e; font-size: 12px; margin-left: auto; }
`;

function style(root) {
  if (!sheets.has("pje")) {
    const tag = document.createElement("style");
    tag.textContent = STYLE;
    document.head.appendChild(tag);
    sheets.add("pje");
  }
  for (const name of ["nadwidget", "sldwidget", "networkmapwidget"]) {
    if (sheets.has(name)) continue;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${root}${WIDGETS}${name}.css`;
    document.head.appendChild(link);
    sheets.add(name);
  }
}

function script(root, name) {
  scripts[name] ??= import(`${root}${WIDGETS}${name}.js`).then((m) => m.default);
  return scripts[name];
}

async function load(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: ${response.status}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return JSON.parse(await new Response(stream).text());
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}

class Model {
  constructor(state, onSend) {
    this.state = { ...state };
    this.handlers = {};
    this.onSend = onSend;
  }
  get(name) {
    return this.state[name];
  }
  set(name, value) {
    this.state[name] = value;
    this.emit(`change:${name}`, value);
  }
  on(event, handler) {
    (this.handlers[event] ??= []).push(handler);
  }
  off(event, handler) {
    if (!event) this.handlers = {};
    else if (!handler) delete this.handlers[event];
    else this.handlers[event] = (this.handlers[event] ?? []).filter((h) => h !== handler);
  }
  emit(event, ...args) {
    for (const handler of this.handlers[event] ?? []) handler(...args);
  }
  save_changes() {}
  send(content) {
    this.onSend(content, this);
  }
}

function element(tag, props = {}, children = []) {
  const node = Object.assign(document.createElement(tag), props);
  for (const child of children) node.append(child);
  return node;
}

function fill(select, options, value) {
  select.replaceChildren(
    ...options.map(([label, id]) => element("option", { value: id, textContent: label })),
  );
  select.value = value ?? "";
  if (value == null) select.selectedIndex = -1;
}

async function explorer(root, host) {
  const base = `${root}${host.dataset.explorer}/`;
  const data = await load(`${base}index.json.gz`);
  const labels = Object.fromEntries(data.options.map(([label, id]) => [id, label]));
  const nads = {};
  const slds = {};
  const nadData = (key) => (nads[key] ??= load(`${base}nad/${key}.json.gz`));
  const sldData = (vl) => (slds[vl] ??= load(`${base}sld/${data.sld[vl]}.json.gz`));
  const hover = (type, id) => {
    const table = data.hover[type];
    if (table && id in table) return table[id];
    return `Equipment of type '${type}' with id '${id}'`;
  };
  const enabled = Object.keys(data.hover).length > 0;

  const state = {
    selected: data.start,
    depth: data.depth,
    history: [data.start],
    filtered: data.options,
    tab: 0,
    nadShown: null,
  };

  const filter = element("input", { type: "text", placeholder: "Voltage level Name" });
  const found = element("select", { size: 2 });
  const history = element("select", { size: 2 });
  const slider = element("input", { type: "range", min: 0, max: data.max_depth, step: 1 });
  const readout = element("span");
  const note = element("span", {
    className: "pje-note",
    textContent: "Static copy: diagrams were computed when the page was built.",
  });
  const hosts = [element("div"), element("div"), element("div")];
  const titles = ["Network Area", "Single Line", "Network map"];
  const buttons = titles.map((title) => element("button", { type: "button", textContent: title }));
  const panels = [
    element("div", { className: "pje-panel" }, [
      element("div", { className: "pje-depth" }, ["depth:", slider, readout, note]),
      hosts[0],
    ]),
    element("div", { className: "pje-panel" }, [hosts[1]]),
    element("div", { className: "pje-panel" }, [hosts[2]]),
  ];
  host.replaceChildren(
    element("div", { className: "pje" }, [
      element("div", { className: "pje-left" }, [
        element("div", { className: "pje-title", textContent: "Voltage levels" }),
        element("label", { className: "pje-row" }, [element("span", { textContent: "Filter" }), filter]),
        element("label", { className: "pje-row pje-found" }, [element("span", { textContent: "Found" }), found]),
        element("label", { className: "pje-row pje-history" }, [
          element("span", { textContent: "History" }),
          history,
        ]),
      ]),
      element("div", { className: "pje-right" }, [element("div", { className: "pje-tabs" }, buttons), ...panels]),
    ]),
  );

  const models = [];
  const rendered = [false, false, false];
  const historyOptions = () => state.history.map((id) => [labels[id], id]);
  const inFiltered = () => state.filtered.some(([, id]) => id === state.selected);
  slider.value = state.depth;
  readout.textContent = state.depth;
  fill(found, state.filtered, state.selected);
  fill(history, historyOptions(), state.selected);

  async function showNad() {
    if (!models[0]) return;
    const keys = data.nad[state.selected];
    const key = keys[Math.min(state.depth, keys.length - 1)];
    const diagram = await nadData(key);
    state.nadShown = state.selected;
    models[0].set("diagram_data", {
      svg_data: diagram.svg_data,
      metadata: diagram.metadata,
      invalid_lf: false,
      drag_enabled: true,
      grayout: false,
      keep_viewbox: false,
    });
  }

  async function showSld() {
    if (!models[1]) return;
    const diagram = await sldData(state.selected);
    models[1].set("diagram_data", {
      value: diagram.value,
      value_meta: diagram.value_meta,
      keep_viewbox: false,
      invalid_lf: false,
    });
  }

  function centerMap() {
    const sub = data.vl_subs[state.selected];
    if (models[2] && sub != null) models[2].set("params", { subId: sub });
  }

  function refresh() {
    if (state.tab === 0) showNad();
    if (rendered[1]) showSld();
    if (rendered[2]) centerMap();
  }

  function addHistory(id) {
    if (state.history[0] === id) return;
    state.history = [id, ...state.history].slice(0, HISTORY);
  }

  function select(id, { toHistory = true, sld = false } = {}) {
    if (!(id in labels)) return;
    if (sld) open(1);
    if (id === state.selected) return;
    state.selected = id;
    if (toHistory) addHistory(id);
    fill(history, historyOptions(), id);
    fill(found, state.filtered, inFiltered() ? id : null);
    refresh();
  }

  function onSend(content, model) {
    if (content.event === "select_menu") {
      select(String(model.get("selected_menu").equipment_id), { sld: true });
    } else if (content.event === "click_nextvl") {
      select(String(model.get("clicked_nextvl")));
    } else if (content.event === "select_vl") {
      select(String(model.get("selected_vl")), { sld: true });
    }
  }

  const experimental = (kind) => ({
    invoke: async (name, message) => [kind === "map" ? hover("LINE", message.id) : hover(message.type, message.id), []],
  });

  async function render(index) {
    if (rendered[index]) return;
    rendered[index] = true;
    const [name, kind] = [
      ["nadwidget", "nad"],
      ["sldwidget", "sld"],
      ["networkmapwidget", "map"],
    ][index];
    if (index === 0) {
      const keys = data.nad[state.selected];
      const diagram = await nadData(keys[Math.min(state.depth, keys.length - 1)]);
      state.nadShown = state.selected;
      models[0] = new Model(
        {
          diagram_data: { svg_data: diagram.svg_data, metadata: diagram.metadata, invalid_lf: false, drag_enabled: true, grayout: false },
          popup_menu_items: ["Open in SLD tab"],
          hover_enabled: enabled,
          branch_states: [],
          current_nad_metadata: "",
        },
        onSend,
      );
    } else if (index === 1) {
      const diagram = await sldData(state.selected);
      models[1] = new Model(
        { diagram_data: { value: diagram.value, value_meta: diagram.value_meta, invalid_lf: false }, hover_enabled: enabled },
        onSend,
      );
    } else {
      const sub = data.vl_subs[state.selected];
      models[2] = new Model(
        { ...data.map, params: { subId: sub ?? null }, selected_vl: "", enable_callbacks: true, hover_enabled: enabled },
        onSend,
      );
    }
    const widget = await script(root, name);
    await widget.initialize?.({ model: models[index] });
    await widget.render({ model: models[index], el: hosts[index], experimental: experimental(kind) });
  }

  function open(index) {
    state.tab = index;
    buttons.forEach((button, i) => button.classList.toggle("on", i === index));
    panels.forEach((panel, i) => panel.classList.toggle("on", i === index));
    if (!rendered[index]) render(index);
    else if (index === 0 && state.nadShown !== state.selected) showNad();
    else if (index === 1) showSld();
    else if (index === 2) centerMap();
  }

  buttons.forEach((button, i) => button.addEventListener("click", () => open(i)));
  found.addEventListener("change", () => {
    if (!found.value) return;
    state.selected = found.value;
    addHistory(found.value);
    fill(history, historyOptions(), null);
    refresh();
  });
  history.addEventListener("change", () => {
    if (!history.value) return;
    state.selected = history.value;
    fill(found, state.filtered, inFiltered() ? state.selected : null);
    refresh();
  });
  filter.addEventListener("input", () => {
    const text = filter.value.toLowerCase();
    state.filtered = text ? data.options.filter(([label]) => label.toLowerCase().includes(text)) : data.options;
    fill(found, state.filtered, inFiltered() ? state.selected : null);
  });
  slider.addEventListener("change", () => {
    state.depth = Number(slider.value);
    readout.textContent = slider.value;
    if (state.tab === 0) showNad();
  });
  slider.addEventListener("input", () => {
    readout.textContent = slider.value;
  });
  open(0);
}

export function mount(root) {
  style(root);
  for (const host of document.querySelectorAll(".static-explorer:not([data-mounted])")) {
    host.dataset.mounted = "true";
    explorer(root, host).catch((error) => {
      host.textContent = `The network explorer could not load: ${error}`;
    });
  }
}
