document.querySelectorAll('.submenu-toggle').forEach(button=>{button.addEventListener('click',()=>{const open=button.parentElement.classList.toggle('open');button.setAttribute('aria-expanded',String(open));});});
const viewer=document.querySelector('#photo-view');
document.querySelectorAll('.migration-gallery a').forEach(link=>{link.addEventListener('click',event=>{event.preventDefault();viewer.querySelector('img').src=link.href;viewer.showModal();});});
viewer.querySelector('button').addEventListener('click',()=>viewer.close());
viewer.addEventListener('click',event=>{if(event.target===viewer)viewer.close();});
