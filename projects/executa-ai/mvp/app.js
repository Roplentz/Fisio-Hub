const $ = (id) => document.getElementById(id);
const storeKey = 'executa-ai-sessions-v1';
let current = null;
let timerHandle = null;
let secondsLeft = 300;

const actionMap = {
  clarity: (task, level=1) => level === 1 ? `Abra o material de “${task}” e escreva apenas 3 próximos passos possíveis.` : `Abra o material de “${task}”. Só isso.`,
  size: (task, level=1) => level === 1 ? `Trabalhe em “${task}” por apenas 5 minutos, escolhendo uma única parte.` : `Escolha somente 1 item de “${task}” e deixe-o visível.`,
  judgment: (task, level=1) => level === 1 ? `Crie uma versão rascunho deliberadamente imperfeita de uma parte de “${task}”.` : `Escreva uma única frase ruim sobre “${task}”.`,
  boredom: (task, level=1) => level === 1 ? `Faça a parte mais mecânica de “${task}” por 5 minutos, sem tentar terminar.` : `Abra “${task}” e conclua apenas 1 campo/item.`,
  energy: (task, level=1) => level === 1 ? `Faça a menor ação física possível ligada a “${task}” por 2 minutos.` : `Deixe o material de “${task}” pronto para a próxima sessão.`,
  options: (task, level=1) => level === 1 ? `Escolha uma única próxima ação para “${task}” e ignore as outras por 10 minutos.` : `Escolha a opção mais reversível e teste por 2 minutos.`
};

const rationaleMap = {
  clarity: 'A barreira parece ser falta de entrada clara. Primeiro criamos um ponto de partida observável.',
  size: 'A tarefa está sendo percebida como grande. Vamos reduzir o escopo, não aumentar a motivação.',
  judgment: 'O objetivo agora é diminuir o custo de errar, não produzir a versão final.',
  boredom: 'Burocracia melhora quando vira bloco curto e mecânico.',
  energy: 'Com energia baixa, a meta é preservar continuidade com uma ação mínima.',
  options: 'Muitas opções travam a decisão. Escolher uma opção reversível destrava o movimento.'
};

function unsafeTask(text='') {
  const t = text.toLowerCase();
  return /(me matar|suicid|machucar alguém|matar alguém|explosiv|fraude|invadir conta|emergência médica|overdose)/i.test(t);
}

function updateResistanceLabels(){
  $('resistance-value').textContent = $('resistance').value;
  $('resistance-after-value').textContent = $('resistance-after').value;
}

function buildAction(level=1){
  const task = $('task').value.trim();
  if (!task) return alert('Descreva a tarefa.');
  if (unsafeTask(task)) {
    $('action-card').classList.remove('hidden');
    $('micro-action').textContent = 'Esta tarefa precisa sair do fluxo de execução.';
    $('micro-rationale').textContent = 'O EXECUTA AI não transforma situações perigosas, ilegais ou de crise em microações. Procure apoio humano ou serviço apropriado antes de continuar.';
    $('begin-btn').classList.add('hidden');
    $('smaller-btn').classList.add('hidden');
    return;
  }
  const barrier = $('barrier').value;
  const resistance = Number($('resistance').value);
  current = {
    id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
    task,
    barrier,
    resistance_before: resistance,
    created_at: new Date().toISOString(),
    action_level: level,
    micro_action: actionMap[barrier](task, level),
    attempts: []
  };
  $('micro-action').textContent = current.micro_action;
  $('micro-rationale').textContent = rationaleMap[barrier];
  $('state-badge').textContent = level === 1 ? 'MICROAÇÃO' : 'MICROAÇÃO REDUZIDA';
  $('action-card').classList.remove('hidden');
  $('checkin-card').classList.add('hidden');
  $('begin-btn').classList.remove('hidden');
  $('smaller-btn').classList.remove('hidden');
  window.scrollTo({top:$('action-card').offsetTop - 20, behavior:'smooth'});
}

function startTimer(){
  if (!current) return;
  const attempt = {started_at:new Date().toISOString(), completed_at:null, outcome:null};
  current.attempts.push(attempt);
  secondsLeft = current.action_level > 1 ? 120 : 300;
  renderTimer();
  clearInterval(timerHandle);
  timerHandle = setInterval(()=>{
    secondsLeft -= 1; renderTimer();
    if(secondsLeft <= 0){ clearInterval(timerHandle); showCheckin(); }
  },1000);
  $('begin-btn').textContent = 'Sessão em andamento…';
  $('begin-btn').disabled = true;
}

function renderTimer(){
  const m=String(Math.floor(secondsLeft/60)).padStart(2,'0');
  const s=String(secondsLeft%60).padStart(2,'0');
  $('timer').textContent=`${m}:${s}`;
}

function showCheckin(){
  $('checkin-card').classList.remove('hidden');
  $('resistance-after').value = $('resistance').value;
  updateResistanceLabels();
  window.scrollTo({top:$('checkin-card').offsetTop - 20, behavior:'smooth'});
}

function markStarted(success){
  if(!current) return;
  const a=current.attempts[current.attempts.length-1] || {started_at:null};
  a.completed_at=new Date().toISOString();
  a.outcome=success?'started':'not_started';
  if(success){
    $('post-checkin').classList.remove('hidden');
  } else {
    current.reentry_at=new Date().toISOString();
    current.action_level=2;
    current.micro_action=actionMap[current.barrier](current.task,2);
    $('micro-action').textContent=current.micro_action;
    $('micro-rationale').textContent='A primeira ação ainda estava grande. Reduzimos de novo para facilitar a reentrada.';
    $('state-badge').textContent='RECUPERAÇÃO';
    $('action-card').classList.remove('hidden');
    $('checkin-card').classList.add('hidden');
    $('begin-btn').disabled=false;
    $('begin-btn').textContent='Começar ação mínima';
    secondsLeft=120; renderTimer();
  }
}

function saveSession(){
  current.resistance_after=Number($('resistance-after').value);
  current.result=$('result').value.trim();
  current.saved_at=new Date().toISOString();
  const sessions=JSON.parse(localStorage.getItem(storeKey)||'[]');
  sessions.unshift(current);
  localStorage.setItem(storeKey,JSON.stringify(sessions.slice(0,50)));
  renderHistory();
  $('post-checkin').classList.add('hidden');
  $('checkin-card').classList.add('hidden');
  $('action-card').classList.add('hidden');
  $('task').value='';
  current=null;
}

function renderHistory(){
  const sessions=JSON.parse(localStorage.getItem(storeKey)||'[]');
  $('history-empty').style.display=sessions.length?'none':'block';
  $('history-list').innerHTML=sessions.map(s=>{
    const delta=(s.resistance_before??0)-(s.resistance_after??s.resistance_before??0);
    const cls=delta>=0?'good':'bad';
    return `<article class="history-item"><strong>${escapeHtml(s.task)}</strong><div class="history-meta">${new Date(s.saved_at||s.created_at).toLocaleString('pt-BR')} • barreira: ${s.barrier} • tentativas: ${(s.attempts||[]).length}</div><div class="delta ${cls}">Resistência: ${s.resistance_before}/10 → ${s.resistance_after ?? '—'}/10 ${Number.isFinite(delta)?`(Δ ${delta>=0?'-':'+'}${Math.abs(delta)})`:''}</div>${s.result?`<div>${escapeHtml(s.result)}</div>`:''}</article>`;
  }).join('');
}

function escapeHtml(v=''){return v.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}

$('resistance').addEventListener('input',updateResistanceLabels);
$('resistance-after').addEventListener('input',updateResistanceLabels);
$('start-btn').addEventListener('click',()=>buildAction(1));
$('smaller-btn').addEventListener('click',()=>buildAction(2));
$('begin-btn').addEventListener('click',startTimer);
$('done-btn').addEventListener('click',()=>markStarted(true));
$('not-done-btn').addEventListener('click',()=>markStarted(false));
$('save-btn').addEventListener('click',saveSession);
$('clear-btn').addEventListener('click',()=>{if(confirm('Limpar histórico local?')){localStorage.removeItem(storeKey);renderHistory();}});

renderHistory(); updateResistanceLabels();