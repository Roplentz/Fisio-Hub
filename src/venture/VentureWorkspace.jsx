import React, { useEffect, useMemo, useState } from 'react';
import { Brain, ChevronLeft, CircleAlert, CircleCheck, FlaskConical, Lightbulb, Save, Sparkles, Target } from 'lucide-react';
import { applyValidatedAgentOutput, createProjectState, orchestrate } from './core.js';
import { listProjects, saveProject } from './repository.js';
import { supabase, persistenceMode } from '../lib/supabase.js';

const steps = ['Problema','Usuário','Evidências','Oportunidade','Valor','Solução','MVP','Modelo','Experimento','Métricas','Pitch','Projeto final'];

function Badge({ children, tone='neutral' }) {
  return <span className={`ventureBadge ${tone}`}>{children}</span>;
}

export default function VentureWorkspace({ setPage }) {
  const [state, setState] = useState(() => createProjectState({ project_name: 'Projeto Venture Copilot' }));
  const [input, setInput] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const projects = await listProjects(supabase);
        const latest = projects?.[0];
        if (mounted && latest?.project_id) {
          setState(latest);
          setInput(latest.problem?.context || '');
          setSaved(true);
        }
      } finally {
        if (mounted) setLoaded(true);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const criticalRisk = state.risks[0] || 'Ainda não identificado';
  const progress = useMemo(() => Math.max(8, Math.min(100, state.opportunity_score)), [state.opportunity_score]);

  async function analyze() {
    setBusy(true); setSaved(false);
    try {
      const output = orchestrate({ action: 'DISCOVERY', input, state });
      const next = applyValidatedAgentOutput(state, output);
      setAnalysis(output);
      setState(next);
      const persisted = await saveProject(next, supabase);
      setState(persisted);
      setSaved(true);
    } finally {
      setBusy(false);
    }
  }

  async function persist() {
    setBusy(true);
    try {
      const persisted = await saveProject(state, supabase);
      setState(persisted);
      setSaved(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="ventureShell">
      <aside className="ventureJourney">
        <button className="ventureBack" onClick={() => setPage('student')}><ChevronLeft size={17}/> Voltar ao FisioHub</button>
        <div className="ventureBrand"><Brain size={22}/><div><b>Venture Copilot</b><small>Sprint 1 · Discovery</small></div></div>
        <div className="journeyList">
          {steps.map((step, index) => (
            <div key={step} className={`journeyStep ${index === 0 ? 'active' : ''} ${index < state.current_phase ? 'done' : ''}`}>
              <span>{index + 1}</span><p>{step}</p>
            </div>
          ))}
        </div>
      </aside>

      <section className="ventureMain">
        <header className="ventureHeader">
          <div><p className="eyebrow">FisioHub Innovation OS</p><h1>{state.project_name}</h1></div>
          <div className="ventureHeaderActions">
            <Badge tone={persistenceMode === 'supabase' ? 'success' : 'neutral'}>{persistenceMode === 'supabase' ? 'Supabase disponível' : 'Persistência local'}</Badge>
            <button className="btn ghost small" onClick={persist} disabled={busy}><Save size={16}/>{saved ? 'Salvo' : 'Salvar'}</button>
          </div>
        </header>

        <div className="ventureGrid">
          <div className="ventureCanvas">
            <div className="ventureIntro">
              <Badge tone="blue"><Sparkles size={13}/> Discovery Agent</Badge>
              <h2>{loaded ? 'O que está na sua cabeça?' : 'Carregando seu projeto…'}</h2>
              <p>Pode ser um problema, ideia, necessidade ou oportunidade. Explique como explicaria para um colega. O agente vai separar problema de solução e explicitar o que ainda é hipótese.</p>
              <textarea value={input} onChange={e => { setInput(e.target.value); setSaved(false); }} placeholder="Ex.: Pacientes recebem alta hospitalar com muitas orientações e frequentemente têm dificuldade para entender o que devem fazer em casa..." disabled={!loaded} />
              <div className="ventureActions"><button className="btn primary" disabled={!loaded || busy || input.trim().length < 5} onClick={analyze}>{busy ? 'Analisando...' : 'Analisar oportunidade'} <Target size={17}/></button></div>
            </div>

            {(analysis || state.problem?.statement) && <div className="analysisCard">
              <div className="analysisTitle"><Lightbulb size={20}/><div><small>Entendi assim</small><h3>{state.problem.statement || 'Problema em formulação'}</h3></div></div>
              <p>{analysis?.analysis || 'Este Project State foi restaurado da persistência. Reanalise quando quiser atualizar o diagnóstico.'}</p>
              <div className="analysisColumns">
                <div><b>Público</b><p>{state.audience.primary || 'Ainda não definido'}</p></div>
                <div><b>JTBD</b><p>{state.jtbd || 'Ainda não formulado'}</p></div>
              </div>
              <div className="hypothesisBox"><b>Hipóteses explícitas</b>{state.assumptions.slice(-4).map(item => <p key={item}><CircleAlert size={15}/>{item}</p>)}</div>
              <div className="gateRow"><div><small>Problem Gate</small><strong>{state.gate_status}</strong></div><div><small>Próxima melhor ação</small><strong>{state.next_action}</strong></div></div>
            </div>}
          </div>

          <aside className="copilotPanel">
            <div className="copilotTop"><Brain size={20}/><div><b>Venture Copilot</b><small>Orchestrator ativo</small></div></div>
            <div className="scoreBox"><div><span>Innovation Score</span><b>{state.opportunity_score}<small>/100</small></b></div><div className="scoreTrack"><i style={{width:`${progress}%`}}/></div><small>Indicador diagnóstico, não validação científica.</small></div>
            <div className="copilotStat"><span>Fase atual</span><b>Discovery</b></div>
            <div className="copilotStat"><span>Situação</span><b>{state.gate_status === 'ADVANCE' ? 'Promissora, não validada' : 'Precisa investigação'}</b></div>
            <div className="copilotMiniGrid"><div><b>{state.facts.length}</b><span>Fatos</span></div><div><b>{state.assumptions.length}</b><span>Hipóteses</span></div><div><b>{state.evidence.length}</b><span>Evidências</span></div></div>
            <div className="riskBox"><CircleAlert size={18}/><div><small>Risco principal</small><p>{criticalRisk}</p></div></div>
            <div className="nextBox"><FlaskConical size={18}/><div><small>Próxima ação</small><p>{state.next_action}</p></div></div>
            {saved && <p className="savedSignal"><CircleCheck size={16}/> Project State persistido.</p>}
          </aside>
        </div>
      </section>
    </main>
  );
}
