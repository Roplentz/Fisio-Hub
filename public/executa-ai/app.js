const $ = id => document.getElementById(id);
const storeKey = 'executa-ai-sessions-v1';
const cfg = window.EXECUTA_AI_CONFIG || { apiUrl:'', mode:'hybrid' };
const allowedBarriers = new Set(['clarity','size','judgment','boredom','energy','options','other']);
let current = null, timerHandle = null, secondsLeft = 300, lastQuestion = null, requestSeq = 0;

const actionMap = {
  clarity:(t,l=1)=>l===1?`Abra o material de “${t}” e escreva apenas 3 próximos passos possíveis.`:`Abra o material de “${t}”. Só isso.`,
  size:(t,l=1)=>l===1?`Trabalhe em “${t}” por apenas 5 minutos, escolhendo uma única parte.`:`Escolha somente 1 item de “${t}” e deixe-o visível.`,
  judgment:(t,l=1)=>l===1?`Crie um rascunho deliberadamente imperfeito de uma parte de “${t}”.`:`Escreva uma única frase ruim sobre “${t}”.`,
  boredom:(t,l=1)=>l===1?`Faça a parte mais mecânica de “${t}” por 5 minutos, sem tentar terminar.`:`Abra “${t}” e conclua apenas 1 campo/item.`,
  energy:(t,l=1)=>l===1?`Faça a menor ação física possível ligada a “${t}” por 2 minutos.`:`Deixe o material de “${t}” pronto para a próxima sessão.`,
  options:(t,l=1)=>l===1?`Escolha uma única próxima ação para “${t}” e ignore as outras por 10 minutos.`:`Escolha a opção mais reversível e teste por 2 minutos.`,
  other:t=>`Abra o material de “${t}” e faça uma única ação de até 2 minutos.`
};
const rationaleMap = {
  clarity:'A barreira parece ser falta de entrada clara.', size:'A tarefa parece grande demais; vamos reduzir o escopo.',
  judgment:'O custo de errar parece alto; vamos criar um rascunho seguro.', boredom:'A burocracia fica menor quando vira bloco curto e mecânico.',
  energy:'Com energia baixa, preservamos continuidade com ação mínima.', options:'Muitas opções travam; uma escolha reversível destrava.',
  other:'Vamos reduzir até existir uma ação observável.'
};

function unsafeTask(text=''){return /(me matar|suicid|machucar alguém|matar alguém|explosiv|fraude|invadir conta|emergência médica|overdose)/i.test(text.toLowerCase())}
function cleanBarrier(v){return allowedBarriers.has(v)?v:'other'}
function safeMinutes(v,fallback=5){const n=Number(v);return Number.isFinite(n)?Math.max(2,Math.min(20,Math.round(n))):fallback}
function setMode(t){$('ai-mode').textContent=t}
function labels(){$('resistance-value').textContent=$('resistance').value;$('resistance-after-value').textContent=$('resistance-after').value}
function snapshot(extra='',questionAlreadyAsked=false){return {task:$('task').value.trim(),context:[$('context').value.trim(),extra].filter(Boolean).join('\n'),resistance:Number($('resistance').value),barrier:$('barrier').value,question_already_asked:questionAlreadyAsked}}

async function askAI(extra='',questionAlreadyAsked=false){
  if(!cfg.apiUrl) return null;
  const seq=++requestSeq, input=snapshot(extra,questionAlreadyAsked);
  setMode('IA ANALISANDO…');
  try{
    const r=await fetch(cfg.apiUrl,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});
    if(seq!==requestSeq) return null;
    if(!r.ok) throw new Error('backend');
    const d=await r.json(); setMode('IA ATIVA'); return {data:d,input};
  }catch(e){ if(seq===requestSeq)setMode('MOTOR LOCAL • FALLBACK'); return null; }
}

function showSafety(){
  current=null; $('question-card').classList.add('hidden'); $('action-card').classList.remove('hidden');
  $('micro-action').textContent='Esta situação precisa sair do fluxo de execução.';
  $('micro-rationale').textContent='O EXECUTA AI não transforma situações perigosas, ilegais ou de crise em microações. Procure suporte humano ou serviço apropriado antes de continuar.';
  $('begin-btn').classList.add('hidden'); $('smaller-btn').classList.add('hidden'); $('finish-btn').classList.add('hidden');
}
function showQuestion(q){lastQuestion=q;$('agent-question').textContent=q;$('question-card').classList.remove('hidden');$('action-card').classList.add('hidden');$('question-answer').value='';$('question-answer').focus()}
function showAction(result,input,level=1){
  const task=input?.task||$('task').value.trim(); const barrier=cleanBarrier(result?.barrier||input?.barrier||$('barrier').value);
  const resistance=Number(input?.resistance??$('resistance').value); const micro=result?.micro_action||actionMap[barrier]?.(task,level)||actionMap.other(task);
  current={id:crypto.randomUUID?crypto.randomUUID():String(Date.now()),task,context:input?.context||$('context').value.trim(),barrier,resistance_before:resistance,created_at:new Date().toISOString(),action_level:level,micro_action:micro,ai_used:!!result,ai_confidence:result?.confidence??null,evidence:result?.evidence||'',attempts:[]};
  $('question-card').classList.add('hidden'); $('micro-action').textContent=micro; $('micro-rationale').textContent=result?.rationale||rationaleMap[barrier];
  $('state-badge').textContent=result?'MICROAÇÃO PERSONALIZADA':(level===1?'MICROAÇÃO':'MICROAÇÃO REDUZIDA'); $('action-card').classList.remove('hidden'); $('checkin-card').classList.add('hidden');
  $('begin-btn').classList.remove('hidden'); $('begin-btn').disabled=false; $('begin-btn').textContent='Começar agora'; $('smaller-btn').classList.remove('hidden'); $('finish-btn').classList.add('hidden');
  secondsLeft=safeMinutes(result?.minutes,level>1?2:5)*60; renderTimer();
}
async function buildAction(level=1,extra='',questionAlreadyAsked=false){
  const input=snapshot(extra,questionAlreadyAsked); if(!input.task)return alert('Descreva a tarefa.'); if(unsafeTask(`${input.task} ${input.context}`))return showSafety();
  const ai=await askAI(extra,questionAlreadyAsked); if(ai?.data?.mode==='safety')return showSafety(); if(ai?.data?.mode==='question'&&ai.data.question&&!questionAlreadyAsked)return showQuestion(ai.data.question);
  showAction(ai?.data?.mode==='action'?ai.data:null,ai?.input||input,level);
}

function startTimer(){if(!current)return;current.attempts.push({started_at:new Date().toISOString(),completed_at:null,outcome:null});renderTimer();clearInterval(timerHandle);timerHandle=setInterval(()=>{secondsLeft--;renderTimer();if(secondsLeft<=0)finishTimer()},1000);$('begin-btn').textContent='Sessão em andamento…';$('begin-btn').disabled=true;$('smaller-btn').classList.add('hidden');$('finish-btn').classList.remove('hidden')}
function finishTimer(){clearInterval(timerHandle);timerHandle=null;$('finish-btn').classList.add('hidden');$('checkin-card').classList.remove('hidden');$('resistance-after').value=$('resistance').value;labels()}
function renderTimer(){const m=String(Math.floor(Math.max(0,secondsLeft)/60)).padStart(2,'0'),s=String(Math.max(0,secondsLeft)%60).padStart(2,'0');$('timer').textContent=`${m}:${s}`}
function markStarted(ok){if(!current)return;const a=current.attempts[current.attempts.length-1]||{started_at:null};a.completed_at=new Date().toISOString();a.outcome=ok?'started':'not_started';if(ok){$('post-checkin').classList.remove('hidden')}else{current.reentry_at=new Date().toISOString();current.action_level=2;current.micro_action=actionMap[current.barrier]?.(current.task,2)||actionMap.other(current.task);$('micro-action').textContent=current.micro_action;$('micro-rationale').textContent='A primeira ação ainda estava grande. Reduzimos novamente para facilitar a reentrada.';$('state-badge').textContent='RECUPERAÇÃO';$('checkin-card').classList.add('hidden');$('begin-btn').disabled=false;$('begin-btn').textContent='Começar ação mínima';secondsLeft=120;renderTimer()}}
function saveSession(){current.resistance_after=Number($('resistance-after').value);current.result=$('result').value.trim();current.saved_at=new Date().toISOString();const sessions=JSON.parse(localStorage.getItem(storeKey)||'[]');sessions.unshift(current);localStorage.setItem(storeKey,JSON.stringify(sessions.slice(0,50)));renderHistory();$('post-checkin').classList.add('hidden');$('checkin-card').classList.add('hidden');$('action-card').classList.add('hidden');$('task').value='';$('context').value='';current=null}
function escapeHtml(v=''){return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function renderHistory(){const sessions=JSON.parse(localStorage.getItem(storeKey)||'[]');$('history-empty').style.display=sessions.length?'none':'block';$('history-list').innerHTML=sessions.map(s=>{const d=(s.resistance_before??0)-(s.resistance_after??s.resistance_before??0);return`<article class="history-item"><strong>${escapeHtml(s.task)}</strong><div class="history-meta">${new Date(s.saved_at||s.created_at).toLocaleString('pt-BR')} • ${s.ai_used?'IA':'local'} • barreira: ${escapeHtml(cleanBarrier(s.barrier))} • tentativas: ${(s.attempts||[]).length}</div><div class="delta ${d>=0?'good':'bad'}">Resistência: ${s.resistance_before}/10 → ${s.resistance_after??'—'}/10</div>${s.result?`<div>${escapeHtml(s.result)}</div>`:''}</article>`}).join('')}

$('resistance').addEventListener('input',labels);$('resistance-after').addEventListener('input',labels);$('start-btn').addEventListener('click',()=>buildAction(1));
$('answer-btn').addEventListener('click',()=>{const a=$('question-answer').value.trim();if(!a)return;buildAction(1,`Pergunta do agente: ${lastQuestion}\nResposta do usuário: ${a}`,true)});
$('smaller-btn').addEventListener('click',()=>buildAction(2,'A microação anterior ainda parece grande. Reduza novamente.',true));$('begin-btn').addEventListener('click',startTimer);$('finish-btn').addEventListener('click',finishTimer);$('done-btn').addEventListener('click',()=>markStarted(true));$('not-done-btn').addEventListener('click',()=>markStarted(false));$('save-btn').addEventListener('click',saveSession);$('clear-btn').addEventListener('click',()=>{if(confirm('Limpar histórico local?')){localStorage.removeItem(storeKey);renderHistory()}});
setMode(cfg.apiUrl?'IA DISPONÍVEL':'MOTOR LOCAL');renderHistory();labels();
