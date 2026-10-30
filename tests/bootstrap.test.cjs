const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('site/admin/bootstrap.js', 'utf8');

async function open(config, ok = true) {
  const elements = Object.fromEntries(['setup','status-title','status-message','setup-steps','retry'].map(id => [id,{hidden:false, textContent:'', addEventListener(){}}]));
  const loaded = [];
  let inits = 0;
  const window = {};
  const context = {window, fetch:async () => ({ok, text:async () => config}), document:{
    getElementById:id => elements[id],
    createElement:() => ({}),
    head:{appendChild(script){loaded.push(script.src); if(script.src.includes('decap-cms')) window.CMS={init(){inits++;}}; else window.DSJHEditorRegistered=true; script.onload();}}
  }};
  vm.runInNewContext(source,context);
  await new Promise(resolve => setImmediate(resolve));
  return {elements,loaded,inits,window};
}
test('unconfigured installation has no CMS load or writable test backend',async () => {
  const result=await open('backend:\n  name: turbo-github\n  turbo_site_id: ""\n');
  assert.equal(result.inits,0);
  assert.deepEqual(result.loaded,[]);
  assert.equal(result.elements['setup-steps'].hidden,false);
  assert.equal(result.elements['status-title'].textContent,'尚未啟用登入');
});
test('configured installation registers widgets before manual CMS init',async () => {
  const result=await open('backend:\n  turbo_site_id: "12345678-abcd-4abc-8abc-123456789abc"\n');
  assert.equal(result.window.CMS_MANUAL_INIT,true);
  assert.equal(result.inits,1);
  assert.match(result.loaded[0],/decap-cms@3\.17\.1/);
  assert.equal(result.loaded[1],'editor.js');
  assert.equal(result.elements.setup.hidden,true);
});
test('configuration fetch failure preserves explanatory portal',async () => {
  const result=await open('',false);
  assert.equal(result.inits,0);
  assert.equal(result.elements.setup.hidden,false);
  assert.equal(result.elements.retry.hidden,false);
});
