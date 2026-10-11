// Language preference stays on this device. Region lookup uses the site's own edge.
(()=>{
 const saved=()=>{try{return localStorage.getItem('ascension-language')}catch{return null}};
 const apply=lang=>{document.documentElement.lang=lang==='zh'?'zh-CN':'en';document.documentElement.classList.toggle('english',lang==='en');document.body?.classList.toggle('english',lang==='en');};
 const languages=navigator.languages?.length?navigator.languages:[navigator.language||''];
 const preferred=languages[0].toLowerCase();
 const explicit=saved();
 const detected=preferred.startsWith('zh')?'zh':preferred.startsWith('en')?'en':null;
 apply(explicit==='zh'||explicit==='en'?explicit:detected||'en');
 document.addEventListener('DOMContentLoaded',()=>apply(document.documentElement.lang==='zh-CN'?'zh':'en'));
 window.setAlbumLanguage=lang=>{apply(lang);try{localStorage.setItem('ascension-language',lang)}catch{}};
 if(!explicit&&!detected)fetch('/locale.json',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(data=>{
  if(!data||saved())return;
  apply(['CN','TW','HK','MO'].includes(data.country)?'zh':'en');
  document.dispatchEvent(new Event('album-language-change'));
 }).catch(()=>{});
})();
