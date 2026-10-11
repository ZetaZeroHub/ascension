
const base='';let archiveItems=[];const select=document.getElementById('archive-select');
function renderArchive(){const chosen=select.value||'独立分镜-v6/index.html';select.replaceChildren();for(const item of archiveItems){const o=document.createElement('option');o.value=item.path;o.textContent=document.body.classList.contains('english')?item.en:item.label;select.append(o)}select.value=chosen;if(!select.value&&archiveItems.length)select.selectedIndex=0;document.getElementById('archive-note').textContent=document.body.classList.contains('english')?`${archiveItems.length} preserved pages, including design iterations, clip studies and workflow records.`:`共 ${archiveItems.length} 个留存页面，含设计迭代、片段实验与工作流记录。`;}
fetch('/assets/archive-catalog.json').then(r=>{if(!r.ok)throw Error('Archive unavailable');return r.json()}).then(data=>{archiveItems=data;renderArchive()}).catch(()=>{document.getElementById('archive-note').textContent='目录暂未载入，可使用“展开原稿”。'});
select.onchange=()=>{const url=base+'/archive/'+select.value.split('/').map(encodeURIComponent).join('/');document.getElementById('archive-frame').src=url;document.getElementById('archive-full').href=url;};
document.getElementById('language').onclick=()=>{window.setAlbumLanguage(document.documentElement.lang==='zh-CN'?'en':'zh');renderArchive()};
document.addEventListener('album-language-change',renderArchive);
document.getElementById('watch').onclick=()=>{document.getElementById('film').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});};

// Keep Bilibili primary. The self-hosted source is assigned only after a WeChat user clicks.
const wechatFallback=document.getElementById('wechat-play');
if(/MicroMessenger/i.test(navigator.userAgent))wechatFallback.hidden=false;
wechatFallback.onclick=()=>{
 const player=document.createElement('video');player.id='film-player';player.className='film-embed';player.controls=true;player.playsInline=true;player.preload='none';player.poster='/assets/ascension.webp';
 player.setAttribute('webkit-playsinline','');player.setAttribute('x5-playsinline','');player.setAttribute('aria-label','飞升 / Ascension');
 player.src='/media/ascension-720p.mp4';document.getElementById('film-player').replaceWith(player);wechatFallback.hidden=true;
 const message=document.getElementById('film-error');
 player.addEventListener('error',()=>{message.hidden=false;message.textContent=document.documentElement.lang==='zh-CN'?'视频暂时无法加载，请使用下方哔哩哔哩链接。':'Video unavailable. Please use the Bilibili link below.';});
 player.play().catch(()=>{message.hidden=false;message.textContent=document.documentElement.lang==='zh-CN'?'请点击视频中的播放按钮。':'Tap play in the video controls.';});
};
