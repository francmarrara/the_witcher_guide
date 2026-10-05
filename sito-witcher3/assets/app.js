// Navigazione, ricerca, progressi (localStorage). Nessuna dipendenza esterna.
(function(){
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  // Ricerca nelle sezioni (index)
  const q=$("#q"), idx=$("#index-list");
  if(q){
    q.addEventListener("input",()=>{
      const t=q.value.trim().toLowerCase();
      $$(".section[data-title]").forEach(sec=>{
        const hit=!t||sec.dataset.title.toLowerCase().includes(t)||sec.textContent.toLowerCase().includes(t);
        sec.style.display=hit?"":"none";
      });
      if(idx){ $$("li",idx).forEach(li=>{
        const hit=!t||li.textContent.toLowerCase().includes(t);
        li.style.display=hit?"":"none";
      });}
      // evidenzia in obiettivi
      $$(".ob-row").forEach(r=>{
        const hit=!t||r.textContent.toLowerCase().includes(t);
        r.style.display=hit?"":"none";
      });
    });
  }
  // Progresso sequenze
  const KEY="tw3-seq-done", KEYOB="tw3-ob-done";
  const get=(k)=>{try{return JSON.parse(localStorage.getItem(k)||"[]")}catch{return[]}};
  const set=(k,v)=>localStorage.setItem(k,JSON.stringify(v));
  const done=new Set(get(KEY));
  const boxes=$$("input.seq-check");
  const bar=$("#seq-bar"), lbl=$("#seq-label"), tocLinks=$$(".toc a");
  function refresh(){
    const total=boxes.length||$$(".section").length;
    const n=done.size;
    if(bar)bar.style.width=(total?Math.round(n/total*100):0)+"%";
    if(lbl)lbl.textContent=`${n} / ${total} sequenze completate`;
    tocLinks.forEach(a=>{const id=a.getAttribute("href").slice(1);a.classList.toggle("done",done.has(id));});
  }
  boxes.forEach(b=>{ if(done.has(b.dataset.sec))b.checked=true;
    b.addEventListener("change",()=>{ b.checked?done.add(b.dataset.sec):done.delete(b.dataset.sec); set(KEY,[...done]); refresh(); });
  });
  refresh();
  // Obiettivi checklist
  const obdone=new Set(get(KEYOB));
  const obboxes=$$("input.ob-check"), obbar=$("#ob-bar"), oblbl=$("#ob-label");
  function refreshOb(){
    if(obbar)obbar.style.width=(obboxes.length?Math.round(obdone.size/obboxes.length*100):0)+"%";
    if(oblbl)oblbl.textContent=`${obdone.size} / ${obboxes.length} obiettivi`;
    $$(".ob-filter-count").forEach(e=>e.textContent=`${obdone.size}/${obboxes.length}`);
  }
  obboxes.forEach(b=>{ if(obdone.has(b.dataset.ob)) {b.checked=true; b.closest(".ob-row").classList.add("done");}
    b.addEventListener("change",()=>{ b.checked?(obdone.add(b.dataset.ob),b.closest(".ob-row").classList.add("done")):(obdone.delete(b.dataset.ob),b.closest(".ob-row").classList.remove("done")); set(KEYOB,[...obdone]); refreshOb(); });
  });
  refreshOb();
  const fT=$("#f-tipo");
  if(fT){ fT.addEventListener("change",()=>{ const v=fT.value;
    $$(".ob-row").forEach(r=>{ r.style.display=(!v||r.dataset.tipo===v)?"":"none"; });
  });}
  const btnAll=$("#btn-all"), btnNone=$("#btn-none");
  if(btnAll)btnAll.onclick=()=>{obboxes.forEach(b=>{b.checked=true;b.closest(".ob-row").classList.add("done");obdone.add(b.dataset.ob)});set(KEYOB,[...obdone]);refreshOb();};
  if(btnNone)btnNone.onclick=()=>{obboxes.forEach(b=>{b.checked=false;b.closest(".ob-row").classList.remove("done")});obdone.clear();set(KEYOB,[]);refreshOb();};
  // Back to top
  const bt=$("#backtop");
  if(bt){ addEventListener("scroll",()=>{bt.style.display=scrollY>600?"block":"none"}); bt.onclick=()=>scrollTo({top:0,behavior:"smooth"}); }
})();
