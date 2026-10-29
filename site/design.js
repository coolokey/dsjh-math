const header=document.querySelector('.site-header');
const menuButton=document.querySelector('.mobile-menu-toggle');
const media=window.matchMedia('(max-width: 959px)');
function closeSubmenus(except=null){document.querySelectorAll('.submenu-toggle').forEach(button=>{if(button!==except){button.closest('li').classList.remove('open');button.setAttribute('aria-expanded','false');}});}
function closeMenu(){header.classList.remove('menu-open');menuButton.setAttribute('aria-expanded','false');menuButton.setAttribute('aria-label','開啟網站選單');closeSubmenus();}
menuButton.addEventListener('click',()=>{const open=header.classList.toggle('menu-open');menuButton.setAttribute('aria-expanded',String(open));menuButton.setAttribute('aria-label',open?'關閉網站選單':'開啟網站選單');});
document.querySelectorAll('.submenu-toggle').forEach(button=>button.addEventListener('click',()=>{closeSubmenus(button);const item=button.closest('li');const open=item.classList.toggle('open');button.setAttribute('aria-expanded',String(open));}));
document.addEventListener('click',event=>{if(!header.contains(event.target))closeMenu();});
document.addEventListener('keydown',event=>{if(event.key!=='Escape'||document.querySelector('#photo-view').open)return;const expanded=document.querySelector('.submenu-toggle[aria-expanded="true"]');if(expanded){closeSubmenus();expanded.focus();return;}if(header.classList.contains('menu-open')){closeMenu();menuButton.focus();}});
function setSidebar(){document.querySelectorAll('.page-sidebar details').forEach(details=>{details.open=!media.matches;});if(!media.matches)closeMenu();}
setSidebar();media.addEventListener('change',setSidebar);
document.querySelectorAll('.pdf-preview').forEach(details=>details.addEventListener('toggle',()=>{const embed=details.querySelector('embed');if(details.open&&!embed.hasAttribute('src'))embed.src=embed.dataset.pdfSrc;}));
const viewer=document.querySelector('#photo-view');
const image=viewer.querySelector('img');
const counter=viewer.querySelector('.photo-counter');
let photos=[];let photoIndex=0;let origin=null;
function showPhoto(index){photoIndex=(index+photos.length)%photos.length;image.src=photos[photoIndex].href;image.alt=photos[photoIndex].querySelector('img')?.alt||'活動照片原圖';counter.textContent=`${photoIndex+1} / ${photos.length}`;}
document.querySelectorAll('.migration-gallery a').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();origin=link;photos=[...link.closest('.migration-gallery').querySelectorAll('a')];showPhoto(photos.indexOf(link));viewer.showModal();}));
viewer.querySelector('.viewer-close').addEventListener('click',()=>viewer.close());
viewer.querySelector('.photo-prev').addEventListener('click',()=>showPhoto(photoIndex-1));
viewer.querySelector('.photo-next').addEventListener('click',()=>showPhoto(photoIndex+1));
viewer.addEventListener('click',event=>{if(event.target===viewer)viewer.close();});
viewer.addEventListener('keydown',event=>{if(event.key==='ArrowLeft'){event.preventDefault();showPhoto(photoIndex-1);}if(event.key==='ArrowRight'){event.preventDefault();showPhoto(photoIndex+1);}});
viewer.addEventListener('close',()=>{image.removeAttribute('src');origin?.focus();});
