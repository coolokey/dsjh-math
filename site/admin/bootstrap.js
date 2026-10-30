/* Do not offer an unauthenticated write backend while account setup is pending. */
(() => {
  'use strict';
  window.CMS_MANUAL_INIT = true;
  const setup = document.getElementById('setup');
  const title = document.getElementById('status-title');
  const message = document.getElementById('status-message');
  const steps = document.getElementById('setup-steps');
  const retry = document.getElementById('retry');
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = () => reject(new Error('編輯器檔案載入失敗，請檢查網路後重試。'));
      document.head.appendChild(script);
    });
  }
  async function start() {
    retry.hidden = true;
    try {
      const response = await fetch('config.yml', {cache:'no-store'});
      if (!response.ok) throw new Error('無法讀取後臺設定，請稍後重試。');
      const config = await response.text();
      const id = config.match(/^\s*turbo_site_id:\s*["']?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})["']?\s*$/im);
      if (!id) {
        title.textContent = '尚未啟用登入';
        message.textContent = '網站編輯程式已準備好，請先完成擁有者帳號與網站授權。';
        steps.hidden = false;
        return;
      }
      steps.hidden = true;
      title.textContent = '正在開啟內容管理室';
      message.textContent = '載入完成後，請使用你的 Decap Turbo 帳號登入。';
      if (!window.CMS) await loadScript('https://cdn.jsdelivr.net/npm/decap-cms@3.17.1/dist/decap-cms.js');
      if (!window.DSJHEditorRegistered) await loadScript('editor.js');
      window.CMS.init();
      setup.hidden = true;
    } catch (error) {
      setup.hidden = false;
      title.textContent = '暫時無法開啟後臺';
      message.textContent = error.message;
      retry.hidden = false;
    }
  }
  retry.addEventListener('click', start);
  start();
})();
