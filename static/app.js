(function(){
  const $=(s)=>document.querySelector(s);
  const body=document.body;
  const theme=localStorage.getItem('regional-theme');
  if(theme==='dark') body.classList.add('dark');
  $('#themeBtn')?.addEventListener('click',()=>{body.classList.toggle('dark');localStorage.setItem('regional-theme',body.classList.contains('dark')?'dark':'light')});
  $('#mobileToggle')?.addEventListener('click',()=>$('#navMenu')?.classList.toggle('open'));

  const text=$('#text');
  if(text){
    const counter=$('#counter');
    const update=()=>{counter.textContent=`${text.value.length} / 5000`};
    text.addEventListener('input',update); update();
    document.querySelectorAll('[data-example]').forEach(b=>b.addEventListener('click',()=>{text.value=b.dataset.example;update();text.focus()}));
    text.addEventListener('input', async ()=>{
      if(text.value.trim().length<3) return;
      try{const r=await fetch('/api/detect?text='+encodeURIComponent(text.value));const j=await r.json();$('#detectHint').textContent=`Auto detection: ${j.dialect} · confidence ${j.confidence}%`;}catch(e){}
    });
    $('#speakBtn')?.addEventListener('click',()=>{
      const R=window.SpeechRecognition||window.webkitSpeechRecognition;
      if(!R){alert('Voice input is not supported in this browser. Try Chrome or Edge.');return;}
      const rec=new R();rec.lang='en-IN';rec.interimResults=false;rec.onresult=(e)=>{text.value+=(text.value?' ':'')+e.results[0][0].transcript;update()};rec.start();
    });
    $('#readBtn')?.addEventListener('click',()=>speakText(text.value));
  }
  window.speakText=(value)=>{if(!('speechSynthesis' in window)){alert('Text-to-speech is not supported.');return;}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(value);u.lang='en-IN';speechSynthesis.speak(u)};
  $('#copyBtn')?.addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('#copyBtn').dataset.copy);$('#copyBtn').textContent='✓ Copied';setTimeout(()=>$('#copyBtn').textContent='📋 Copy',1600)}catch(e){alert('Copy failed.')}});
  window.sendFeedback=async(useful)=>{const csrf=document.querySelector('input[name=csrf_token]')?.value||'';const id=window.CHECK_RESULT?.check_id;try{await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({useful,check_id:id})});$('#feedbackMsg').textContent='Thank you for your feedback!';}catch(e){}};
  $('#clearHistoryBtn')?.addEventListener('click',async()=>{if(!confirm('Delete all your analysis history?'))return;const csrf=document.querySelector('input[name=csrf_token]')?.value||'';const r=await fetch('/history/clear',{method:'POST',headers:{'X-CSRF-Token':csrf}});if(r.ok)location.reload();});
  const practice=$('#practiceBtn');
  if(practice){
    const questions=['Convert this idea into your regional mix: “I have to go home now.”','Write this casually: “What are you doing?”','Write this naturally: “Please wait a little.”'];let i=0;
    $('#nextQuestion')?.addEventListener('click',()=>{i=(i+1)%questions.length;$('#question').innerHTML=questions[i];$('#practiceText').value='';$('#practiceResult').classList.add('hidden')});
    practice.addEventListener('click',async()=>{const value=$('#practiceText').value.trim();if(!value){alert('Write an answer first.');return;}const csrf=document.querySelector('input[name=csrf_token]')?.value||'';const r=await fetch('/api/check',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({text:value,dialect:'Auto'})});const j=await r.json();const box=$('#practiceResult');box.classList.remove('hidden');if(j.error){box.textContent=j.error;return;}box.innerHTML=`<b>Detected:</b> ${escapeHtml(j.dialect)}<br><b>Score:</b> ${escapeHtml(j.overall_score)}%<br><b>Correction:</b> ${escapeHtml(j.correction)}`});
  }
  function escapeHtml(x){return String(x).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
})();
