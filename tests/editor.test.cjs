const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('site/admin/editor.js', 'utf8');
function load() {
  const widgets = {};
  const window = { CMS: { registerWidget: (name, control, preview) => { widgets[name] = { control, preview }; } },
    h: (tag, props, ...children) => ({tag, props, children}), createClass: x => x };
  vm.runInNewContext(source, { window, URL, Date, Uint32Array });
  return { window, widgets };
}
test('registers supported HTML and immutable ID widgets', () => {
  const { widgets } = load();
  assert.ok(widgets['dsjh-html'].control);
  assert.ok(widgets['dsjh-stable-id'].control);
});
test('preview redraws sanitized markup when CMS passes updated props', () => {
  const preview = load().widgets['dsjh-html'].preview;
  const events = [];
  const doc = {
    body:{innerHTML:''},
    addEventListener:name=>events.push(name),
    createElement:()=>({innerHTML:'',content:{querySelectorAll:()=>[]}})
  };
  const instance = {...preview, props:{value:'<p>第一版</p>'},frame:{contentDocument:doc}};
  instance.loadFrame();
  assert.equal(doc.body.innerHTML,'<p>第一版</p>');
  instance.props={value:'<p>第二版</p>'};
  instance.componentDidUpdate();
  assert.equal(doc.body.innerHTML,'<p>第二版</p>');
  assert.deepEqual(events,['click','auxclick','submit']);
  instance.props={value:''};
  instance.componentDidUpdate();
  assert.equal(doc.body.innerHTML,'');
});
test('existing IDs are untouched; new IDs are generated only on mount', () => {
  const control = load().widgets['dsjh-stable-id'].control;
  const changes = [];
  control.componentDidMount.call({props:{value:'123456', onChange:x=>changes.push(x)}});
  assert.deepEqual(changes, []);
  control.componentDidMount.call({props:{value:'', onChange:x=>changes.push(x)}});
  assert.match(changes[0], /^\d{17,25}$/);
});
test('loading and toggling HTML mode never rewrite untouched original', () => {
  const control = load().widgets['dsjh-html'].control;
  const value = '<TABLE class="old"><tr><td>A &amp; B</td></tr></TABLE>\n';
  const changes = [];
  const instance = {...control, props:{value, onChange:x=>changes.push(x)}, state:{advanced:false}, setState(x){Object.assign(this.state,x);}};
  instance.componentDidMount();
  instance.toggleAdvanced();
  instance.toggleAdvanced();
  assert.deepEqual(changes, []);
});
test('sandbox excludes script execution and preview resolves site assets', () => {
  const { window, widgets } = load();
  const html = window.DSJHEditor.frameHTML('<p>內容</p>');
  assert.match(html, /base href="[^\"]*\/dsjh-math\//);
  assert.match(html, /default-src 'none'/);
  const instance = {...widgets['dsjh-html'].control,props:{value:'',forID:'body'},state:{advanced:false}};
  const tree = instance.render();
  const frame = tree.children.flat(Infinity).find(x=>x && x.tag==='iframe');
  assert.equal(frame.props.sandbox, 'allow-same-origin');
});
