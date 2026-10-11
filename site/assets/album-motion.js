// Shared motion controls. Core content stays readable without this script or GSAP.
const motionPreference=matchMedia('(prefers-reduced-motion:reduce)');
let userPausedMotion=false;
const motionAllowed=()=>!motionPreference.matches&&!userPausedMotion;
const tabs=[...document.querySelectorAll('.studio-tabs [role="tab"]')];
function choosePanel(tab,focus=false){
 for(const item of tabs){const active=item===tab;item.setAttribute('aria-selected',String(active));item.tabIndex=active?0:-1;document.getElementById(item.getAttribute('aria-controls')).hidden=!active;}
 if(focus)tab.focus();
 const panel=document.getElementById(tab.getAttribute('aria-controls'));
 if(window.gsap&&motionAllowed()){gsap.killTweensOf(panel.children);gsap.fromTo(panel.children,{opacity:.3,y:12},{opacity:1,y:0,duration:.45,stagger:.05,ease:'power3.out',clearProps:'opacity,transform'});}
}
tabs.forEach((tab,i)=>{tab.addEventListener('click',()=>choosePanel(tab));tab.addEventListener('keydown',event=>{
 let next;if(event.key==='ArrowRight')next=(i+1)%tabs.length;else if(event.key==='ArrowLeft')next=(i+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;
 if(next!==undefined){event.preventDefault();choosePanel(tabs[next],true);}
});});
let entranceObserver,entranceContext;
function initEntrances(){
 entranceObserver?.disconnect();entranceContext?.revert();
 if(!window.gsap||!motionAllowed()||!('IntersectionObserver' in window))return;
 entranceContext=gsap.context(()=>{});
 entranceObserver=new IntersectionObserver(entries=>{for(const entry of entries){
  if(!entry.isIntersecting)continue;entranceObserver.unobserve(entry.target);
  entranceContext.add(()=>{
   const section=entry.target;
   if(section.id==='production')gsap.to(section.querySelector('.process-flow'),{'--flow-progress':1,duration:1.8,ease:'power2.inOut'});
   const items=section.querySelectorAll('.specs>div,.journey>span,.story-contact figure,.process-flow>div,.production-media img,.studio-intro>*,.author-link>*');
   if(items.length)gsap.from(items,{y:22,opacity:.2,duration:.7,stagger:.12,ease:'power3.out',clearProps:'opacity,transform'});
  });
 }},{threshold:.16});
 document.querySelectorAll('#requirements,#concept,#storyboards,#production,#open,.author-footer').forEach(el=>entranceObserver.observe(el));
}
const beatButton=document.getElementById('beat-play');
const beatFigures=[...document.querySelectorAll('.beat-frames figure')];
const beatState={progress:0};let beatTimeline;
function showBeat(progress){
 const slot=progress<.5?0:progress<.75?1:2;
 beatFigures.forEach((el,i)=>{el.style.opacity=i===slot?'1':'.48';});
 const track=document.querySelector('.beat-track');
 document.querySelector('.beat-cursor').style.transform=`translateX(${progress*(track.clientWidth-2)}px)`;
}
function stopBeat(){
 beatTimeline?.pause();beatButton.setAttribute('aria-pressed','false');
 beatButton.innerHTML='<span class="cn">播放节奏示意</span><span class="en">Play rhythm study</span>';
}
beatButton.addEventListener('click',()=>{
 if(!window.gsap||!motionAllowed())return;
 if(beatButton.getAttribute('aria-pressed')==='true'){stopBeat();return;}
 if(!beatTimeline)beatTimeline=gsap.to(beatState,{progress:1,duration:6,repeat:-1,ease:'none',paused:true,onUpdate:()=>showBeat(beatState.progress)});
 beatTimeline.play();beatButton.setAttribute('aria-pressed','true');beatButton.innerHTML='<span class="cn">暂停示意</span><span class="en">Pause study</span>';
});
const beatObserver=new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)stopBeat();},{threshold:.08});
beatObserver.observe(document.querySelector('.beat-demo'));
document.addEventListener('visibilitychange',()=>{if(document.hidden)stopBeat();});
window.addEventListener('resize',()=>showBeat(beatState.progress));
function syncMotion(){
 const enabled=motionAllowed();document.body.classList.toggle('motion-off',!enabled);
 beatButton.disabled=!enabled||!window.gsap;
 if(!enabled){stopBeat();showBeat(0);if(window.gsap){gsap.killTweensOf('.studio-panel>*');gsap.set('.studio-panel>*',{clearProps:'opacity,transform'});}}initEntrances();
}
motionPreference.addEventListener('change',syncMotion);syncMotion();
