
const base='';let archiveItems=[];const select=document.getElementById('archive-select');
function renderArchive(){const chosen=select.value||'独立分镜-v6/index.html';select.replaceChildren();for(const item of archiveItems){const o=document.createElement('option');o.value=item.path;o.textContent=document.body.classList.contains('english')?item.en:item.label;select.append(o)}select.value=chosen;if(!select.value&&archiveItems.length)select.selectedIndex=0;document.getElementById('archive-note').textContent=document.body.classList.contains('english')?`${archiveItems.length} preserved pages, including design iterations, clip studies and workflow records.`:`共 ${archiveItems.length} 个留存页面，含设计迭代、片段实验与工作流记录。`;}
fetch('/assets/archive-catalog.json').then(r=>{if(!r.ok)throw Error('Archive unavailable');return r.json()}).then(data=>{archiveItems=data;renderArchive()}).catch(()=>{document.getElementById('archive-note').textContent='目录暂未载入，可使用“展开原稿”。'});
select.onchange=()=>{const url=base+'/archive/'+select.value.split('/').map(encodeURIComponent).join('/');document.getElementById('archive-frame').src=url;document.getElementById('archive-full').href=url;};
document.getElementById('language').onclick=()=>{document.body.classList.toggle('english');document.documentElement.lang=document.body.classList.contains('english')?'en':'zh-CN';renderArchive()};
document.getElementById('watch').onclick=()=>{const film=document.getElementById('film-player');document.getElementById('film').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});film.play().catch(()=>{const e=document.getElementById('play-error');e.hidden=false;e.textContent=document.body.classList.contains('english')?'Use the player controls to start playback.':'请点击播放器中的播放按钮。'})};

const reduced=matchMedia('(prefers-reduced-motion:reduce)').matches;
if(!reduced && 'IntersectionObserver' in window){
 const io=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){e.target.classList.add('revealed');io.unobserve(e.target)}},{threshold:.08});
 for(const el of document.querySelectorAll('.section h2,.portrait-row img,.production-media,.edit-proof')){el.classList.add('reveal');io.observe(el)}
}
document.getElementById('film-player').addEventListener('play',()=>{document.querySelector('.hero').classList.add('film-playing')});
document.getElementById('film-player').addEventListener('pause',()=>{document.querySelector('.hero').classList.remove('film-playing')});
