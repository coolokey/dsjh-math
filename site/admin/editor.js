/* Decap's documented window.h / window.createClass widget API; no build step. */
(function (root) {
  'use strict';
  var h = root.h, createClass = root.createClass;
  var BASE = root.location ? new URL('../', root.location.href).href : 'https://coolokey.github.io/dsjh-math/';
  function escapeAttr(value) { return value.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
  function safeURL(value) {
    var clean = value.replace(/[\u0000-\u0020\u007f]/g, '');
    return !/^(?:javascript|vbscript|data|file|blob):/i.test(clean) && !/^\/\//.test(clean);
  }
  function sanitize(value, doc) {
    var template = doc.createElement('template');
    template.innerHTML = value;
    template.content.querySelectorAll('script,style,base,meta,link,svg,math').forEach(function (node) { node.remove(); });
    template.content.querySelectorAll('*').forEach(function (node) {
      Array.from(node.attributes).forEach(function (attr) {
        var name = attr.name.toLowerCase();
        if (/^on/.test(name) || ['srcdoc', 'contenteditable', 'autofocus', 'formaction', 'action', 'srcset', 'ping'].indexOf(name) !== -1 ||
            (['href', 'src', 'data', 'poster', 'background', 'xlink:href'].indexOf(name) !== -1 && !safeURL(attr.value)) ||
            (name === 'style' && /url\s*\(|expression\s*\(|@import|behavior\s*:|-moz-binding/i.test(attr.value))) node.removeAttribute(attr.name);
      });
    });
    return template.innerHTML;
  }
  function frameHTML(value) {
    // Raw markup is sanitized by the caller. Sandbox and CSP also protect the first parse.
    return '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">' +
      '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src https: http: data: blob:; style-src \'unsafe-inline\'; frame-src \'none\'; object-src \'none\'; form-action \'none\'">' +
      '<base href="' + escapeAttr(BASE) + '"><style>body{font:17px/1.8 system-ui,sans-serif;padding:18px;color:#172c39;overflow-wrap:anywhere}img{max-width:100%;height:auto}table{max-width:100%;border-collapse:collapse}td,th{border:1px solid #aebdc5;padding:6px}a{color:#126477}iframe,object,embed{max-width:100%}body:focus{outline:2px solid #368494;outline-offset:-4px}</style></head><body>' + value + '</body></html>';
  }
  var HTMLControl = createClass({
    getInitialState: function () { return { advanced: false, error: '' }; },
    componentDidMount: function () { this.lastEmitted = this.props.value || ''; },
    componentDidUpdate: function () {
      if (this.frame && this.frame.contentDocument && this.props.value !== this.lastEmitted) {
        this.lastEmitted = this.props.value || '';
        this.frame.contentDocument.body.innerHTML = sanitize(this.lastEmitted, this.frame.contentDocument);
      }
    },
    emit: function (value) {
      if (value !== this.lastEmitted) { this.lastEmitted = value; this.props.onChange(value); }
    },
    readFrame: function () {
      var doc = this.frame.contentDocument;
      this.emit(sanitize(doc.body.innerHTML, doc));
    },
    loadFrame: function () {
      var self = this, doc = this.frame.contentDocument;
      if (!doc || !doc.body) return;
      doc.body.innerHTML = sanitize(this.props.value || '', doc);
      doc.body.contentEditable = 'true';
      doc.body.setAttribute('role', 'textbox');
      doc.body.setAttribute('aria-label', '原有網頁內容');
      doc.body.setAttribute('aria-multiline', 'true');
      doc.addEventListener('click', function (event) { if (event.target.closest('a,button,input,select,textarea')) event.preventDefault(); });
      doc.addEventListener('auxclick', function (event) { event.preventDefault(); });
      doc.addEventListener('submit', function (event) { event.preventDefault(); });
      doc.addEventListener('drop', function (event) { event.preventDefault(); });
      doc.addEventListener('dragover', function (event) { event.preventDefault(); });
      doc.body.addEventListener('input', function () { self.readFrame(); });
      doc.body.addEventListener('paste', function (event) {
        event.preventDefault();
        var data = event.clipboardData;
        if (!data) return;
        if (data.getData('text/html')) doc.execCommand('insertHTML', false, sanitize(data.getData('text/html'), doc));
        else doc.execCommand('insertText', false, data.getData('text/plain'));
        self.readFrame();
      });
    },
    command: function (command, value) {
      if (!this.frame) return;
      var doc = this.frame.contentDocument;
      doc.body.focus();
      doc.execCommand(command, false, value || null);
      this.readFrame();
    },
    addLink: function () {
      var url = root.prompt('輸入連結網址（https:// 或站內相對路徑）');
      if (!url) return;
      if (!safeURL(url)) { this.setState({ error: '不支援此連結格式。' }); return; }
      this.setState({ error: '' });
      this.command('createLink', url);
    },
    toggleAdvanced: function () {
      if (this.state.advanced) this.commitHTML();
      this.setState({ advanced: !this.state.advanced, sourceDraft: this.props.value || '' });
    },
    changeHTML: function (event) { this.setState({ sourceDraft: event.target.value }); },
    commitHTML: function () {
      var value = this.state.sourceDraft === undefined ? (this.props.value || '') : this.state.sourceDraft;
      if (value === this.lastEmitted) return;
      var doc = this.frame && this.frame.contentDocument;
      if (!doc) return;
      var cleaned = sanitize(value, doc);
      this.emit(cleaned);
      doc.body.innerHTML = cleaned;
      this.setState({ sourceDraft: cleaned, error: cleaned !== value ? '已移除不安全的程式碼或屬性。' : '' });
    },
    render: function () {
      var self = this;
      function button(label, handler) { return h('button', { type: 'button', onMouseDown: function (event) { event.preventDefault(); }, onClick: handler }, label); }
      return h('div', { className: 'dsjh-editor ' + (this.props.classNameWrapper || '') },
        h('p', { className: 'dsjh-editor-help' }, '可直接修改文字。原有表格、相簿與文件結構會保留。圖片與文件可由下方新增區塊管理。內嵌文件於正式網站檢視。'),
        h('div', { className: 'dsjh-toolbar', role: 'toolbar', 'aria-label': '文字格式' },
          button('粗體', function () { self.command('bold'); }),
          button('標題', function () { self.command('formatBlock', 'h2'); }),
          button('段落', function () { self.command('formatBlock', 'p'); }),
          button('項目清單', function () { self.command('insertUnorderedList'); }),
          button('編號清單', function () { self.command('insertOrderedList'); }),
          button('連結', this.addLink),
          h('button', { type: 'button', 'aria-expanded': this.state.advanced, onClick: this.toggleAdvanced }, '進階 HTML')),
        h('iframe', { ref: function (frame) { self.frame = frame; }, title: '原有網頁內容編輯與預覽', sandbox: 'allow-same-origin', srcDoc: this.initialFrame || (this.initialFrame = frameHTML('')), onLoad: this.loadFrame, className: 'dsjh-editor-frame', style: this.state.advanced ? { display: 'none' } : {} }),
        this.state.advanced ? h('textarea', { id: this.props.forID, 'aria-label': '進階 HTML 原始碼（離開欄位時套用）', className: 'dsjh-html-source', value: this.state.sourceDraft === undefined ? (this.props.value || '') : this.state.sourceDraft, onChange: this.changeHTML, onBlur: this.commitHTML, spellCheck: false }) : null,
        h('p', { role: 'status', className: 'dsjh-editor-status' }, this.state.error || '內容預覽不包含正式網站的導覽與版型。'));
    }
  });
  var HTMLPreview = createClass({
    componentDidUpdate: function () { this.draw(); },
    draw: function () {
      var doc = this.frame && this.frame.contentDocument;
      if (doc && doc.body) doc.body.innerHTML = sanitize(this.props.value || '', doc);
    },
    loadFrame: function () {
      this.draw();
      var doc = this.frame && this.frame.contentDocument;
      if (doc) {
        doc.addEventListener('click', function (event) { event.preventDefault(); });
        doc.addEventListener('auxclick', function (event) { event.preventDefault(); });
        doc.addEventListener('submit', function (event) { event.preventDefault(); });
      }
    },
    render: function () {
      var self = this;
      return h('iframe', { ref: function (frame) { self.frame = frame; }, title: '網頁內容預覽', sandbox: 'allow-same-origin', className: 'dsjh-editor-frame', srcDoc: frameHTML(''), onLoad: this.loadFrame });
    }
  });
  var IDControl = createClass({
    componentDidMount: function () {
      if (this.props.value) return;
      var number = new Uint32Array(1);
      if (root.crypto && root.crypto.getRandomValues) root.crypto.getRandomValues(number);
      else number[0] = Math.floor(Math.random() * 4294967296);
      this.props.onChange(String(Date.now()) + String(number[0]).padStart(10, '0'));
    },
    render: function () { return h('input', { id: this.props.forID, className: this.props.classNameWrapper, type: 'text', value: this.props.value || '', readOnly: true, 'aria-label': '固定識別碼（不可修改）' }); }
  });
  root.DSJHEditor = { sanitize: sanitize, frameHTML: frameHTML, safeURL: safeURL };
  root.CMS.registerWidget('dsjh-html', HTMLControl, HTMLPreview);
  root.CMS.registerWidget('dsjh-stable-id', IDControl);
  root.DSJHEditorRegistered = true;
})(window);
