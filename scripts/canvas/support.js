// A minimal stand-in for the design canvas runtime, enough to render a frame statically:
// {{expr}} in text and attributes, <sc-if value>, <sc-for list as>, <dc-import name ...props>,
// <helmet> (moved to <head>), and a `class Component extends DCLogic` with renderVals().
// Event handlers are dropped: the render is a picture, not the app.
(function () {
  class DCLogic {
    constructor(props) { this.props = props; this.state = {}; }
    setState(next) { Object.assign(this.state, typeof next === 'function' ? next(this.state) : next); }
  }
  window.DCLogic = DCLogic;

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const EXPR = /\{\{([\s\S]+?)\}\}/g;
  const ONLY = /^\{\{([\s\S]+?)\}\}$/;

  function evaluate(expr, scope) {
    const names = Object.keys(scope);
    try { return new Function(...names, `return (${expr});`)(...names.map((n) => scope[n])); }
    catch (error) { console.warn('expr failed', expr, error.message); return undefined; }
  }

  function interpolate(text, scope) {
    return text.replace(EXPR, (_, expr) => { const v = evaluate(expr, scope); return v == null ? '' : String(v); });
  }

  function camel(name) { return name.replace(/-([a-z])/g, (_, c) => c.toUpperCase()); }

  async function load(name) {
    const html = await (await fetch(`./${name}.dc.html`)).text();
    return new DOMParser().parseFromString(html, 'text/html');
  }

  function component(doc, props) {
    const script = doc.querySelector('script[type="text/x-dc"]');
    const declared = JSON.parse(script?.dataset.props || '{}');
    const merged = {};
    for (const [key, spec] of Object.entries(declared)) if (key[0] !== '$' && spec && 'default' in spec) merged[key] = spec.default;
    Object.assign(merged, props);
    const Component = new Function('DCLogic', `${script.textContent}; return Component;`)(DCLogic);
    const instance = new Component(merged);
    return { ...merged, ...(instance.renderVals ? instance.renderVals() : {}) };
  }

  async function renderChildren(source, target, scope) {
    for (const node of [...source.childNodes]) await renderNode(node, target, scope);
  }

  async function renderNode(node, target, scope) {
    if (node.nodeType === Node.TEXT_NODE) { target.appendChild(document.createTextNode(interpolate(node.textContent, scope))); return; }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const tag = node.tagName.toLowerCase();
    if (tag === 'helmet') { for (const child of [...node.children]) document.head.appendChild(child.cloneNode(true)); return; }
    if (tag === 'sc-if') { if (evaluate(node.getAttribute('value').match(ONLY)[1], scope)) await renderChildren(node, target, scope); return; }
    if (tag === 'sc-for') {
      const list = evaluate(node.getAttribute('list').match(ONLY)[1], scope) || [];
      const as = node.getAttribute('as');
      for (const [index, item] of list.entries()) await renderChildren(node, target, { ...scope, [as]: item, index });
      return;
    }
    if (tag === 'dc-import') {
      const props = {};
      for (const attr of node.attributes) {
        if (attr.name === 'name' || attr.name.startsWith('hint-')) continue;
        const only = attr.value.match(ONLY);
        props[camel(attr.name)] = only ? evaluate(only[1], scope) : attr.value;
      }
      const doc = await load(node.getAttribute('name'));
      const root = doc.querySelector('x-dc');
      await renderChildren(root, target, component(doc, props));
      return;
    }
    const svg = tag === 'svg' || target.namespaceURI === SVG_NS;
    const element = svg ? document.createElementNS(SVG_NS, node.tagName) : document.createElement(tag);
    for (const attr of node.attributes) {
      if (/^on[a-z]/i.test(attr.name)) continue;
      const only = attr.value.match(ONLY);
      if (only) {
        const value = evaluate(only[1], scope);
        if (value === false || value == null) continue;
        element.setAttribute(attr.name, value === true ? '' : String(value));
      } else element.setAttribute(attr.name, interpolate(attr.value, scope));
    }
    await renderChildren(tag === 'template' ? node.content : node, element, scope);
    target.appendChild(element);
  }

  window.addEventListener('DOMContentLoaded', async () => {
    const root = document.querySelector('x-dc');
    const scope = component(document, {});
    const out = document.createElement('div');
    await renderChildren(root, out, scope);
    root.replaceWith(...out.childNodes);
    await document.fonts.ready;
    document.body.dataset.rendered = 'true';
  });
})();
