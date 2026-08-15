import React, { useEffect, useMemo, useState } from 'react';
import { Brain, ChevronLeft, CircleAlert, CircleCheck, FlaskConical, Lightbulb, Plus, Save, Sparkles, Target, Trash2 } from 'lucide-react';
import { addEvidence, applyValidatedAgentOutput, createProjectState, orchestrate, removeEvidence } from './core.js';
import { listProjects, saveProject } from './repository.js';
import { supabase, persistenceMode } from '../lib/supabase.js';

const steps = ['Problema','Usuário','Evidências','Oportunidade','Valor','Solução','MVP','Modelo','Experimento','Métricas','Pitch','Projeto final'];
const emptyEvidence = () => ({ type:'interview', source:'', description:'', hypothesis:'', date:new Date().toISOString().slice(0,10) });

function Badge({ children, tone='neutral' }) {
  return <span className={`ventureBadge ${tone}`}>{children}</span>;
}

export default function VentureWorkspace({ setPage }) {
  const [state, setState] = useState(() => createProjectState({ project_name: 'Projeto Venture Copilot' }));
  const [input, setInput] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [evidenceDraft, setEvidenceDraft] = useState(emptyEvidence());
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');

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
      } catch (err) {
        if (mounted) setError(err.message || 'Não foi possível restaurar o projeto.');
      } finally {
        if (mounted) setLoaded(true);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const criticalRisk = state.risks?.[0] || 'Ainda não identificado';
  const progress = useMemo(() => Math.max(4, Math.min(100, state.opportunity_score || 0)), [state.opportunity_score]);
  const breakdown = state.score_breakdown || {};

  async function commit(next) {
    setState(next);
    const persisted = await saveProject(next, supabase);
    setState(persisted);
    setSaved(true);
  }

  async function analyze() {
    setBusy(true); setSaved(false); setError('');
    try {
      const output = orchestrate({ action: 'DISCOVERY', input, state });
      const next = applyValidatedAgentOutput(state, output);
      setAnalysis(output);
      await commit(next);
    } catch (err) {
      setError(err.message || 'Falha ao analisar o projeto.');
    } finally {
      setBusy(false);
    }
  }

  async function persist() {
    setBusy(true); setError('');
    try { await commit(state); }
    catch (err) { setError(err.message || 'Falha ao salvar o projeto.'); }
    finally { setBusy(false); }
  }

  async function handleAddEvidence(event) {
    event.preventDefault(); setError(''); setSaved(false);
    try {
      const next = addEvidence(state, evidenceDraft);
      await commit(next);
      setEvidenceDraft(emptyEvidence());
    } catch (err) {
      setError(err.message || 'Não foi possível registrar a evidência.');
    }
  }

  async function handleRemoveEvidence(id) {
    setError(''); setSaved(false);
    try { await commit(removeEvidence(state, id)); }
    catch (err) { setError(err.message || 'Não foi possível remover a evidência.'); }
  }

  return (
    <main className="ventureShell">
      <aside className="ventureJourney">
        <button className="ventureBack" onClick={() => setPage('student')}><ChevronLeft size={17}/> Voltar ao FisioHub</button>
        <div className="ventureBrand"><Brain size={22}/><div><b>Venture Copilot</b><small>Sprints 2–3 · Discovery + Evidence</small></div></div>
        <div className="journeyList">
          {steps.map((step, index) => {
            const active = index <= 2;
            const done = index === 0 && state.problem?.statement;
            return <div key={step} className={`journeyStep ${active ? 'active' : ''} ${done ? 'done' : ''}`}><span>{index + 1}</span><p>{step}</p></div>;
          })}
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

        {error && <div className="ventureError"><CircleAlert size={17}/>{error}</div>}

        <div className="ventureGrid">
          <div className="ventureCanvas">
            <section className="ventureIntro">
              <Badge tone="blue"><Sparkles size={13}/> Discovery Agent</Badge>
              <h2>{loaded ? 'Descreva o problema do seu jeito.' : 'Carregando seu projeto…'}</h2>
              <p>Inclua, se souber: quem vive o problema, quando acontece, frequência, consequência, como é resolvido hoje e o que acontece se nada for feito. Não precisa escrever como projeto.</p>
              <textarea value={input} onChange={e => { setInput(e.target.value); setSaved(false); }} placeholder="Ex.: Pacientes recebem alta hospitalar com muitas orientações. Isso acontece diariamente no serviço e familiares ligam depois porque não entenderam medicação, sinais de alerta ou cuidados..." disabled={!loaded} />
              <div className="venturePromptHints"><span>Quem?</span><span>Quando?</span><span>Frequência?</span><span>Consequência?</span><span>Como resolve hoje?</span></div>
              <div className="ventureActions"><button className="btn primary" disabled={!loaded || busy || input.trim().length < 20} onClick={analyze}>{busy ? 'Analisando...' : 'Executar Discovery'} <Target size={17}/></button></div>
            </section>

            {(analysis || state.problem?.statement) && <section className="analysisCard">
              <div className="analysisTitle"><Lightbulb size={20}/><div><small>Problem framing</small><h3>{state.problem.statement || 'Problema em formulação'}</h3></div></div>
              <p>{analysis?.analysis || 'Project State restaurado. Reanalise quando tiver novas informações.'}</p>
              <div className="analysisColumns three">
                <div><b>Público</b><p>{state.audience?.primary || 'Ainda não definido'}</p></div>
                <div><b>Frequência</b><p>{state.problem?.frequency || 'Não medida'}</p></div>
                <div><b>Solução atual</b><p>{state.problem?.current_solution || 'Não informada'}</p></div>
              </div>
              <div className="analysisColumns">
                <div><b>Consequência</b><p>{state.problem?.consequences || 'Não explicitada'}</p></div>
                <div><b>JTBD</b><p>{state.jtbd || 'Ainda não formulado'}</p></div>
              </div>
              <div className="criticalHypothesis"><small>HIPÓTESE MAIS ARRISCADA</small><strong>{state.critical_hypothesis || 'Ainda não identificada'}</strong></div>
              {!!state.unknowns?.length && <div className="unknownBox"><b>O que ainda não sabemos</b>{state.unknowns.slice(0,5).map(item => <p key={item}>• {item}</p>)}</div>}
              <div className="hypothesisBox"><b>Hipóteses explícitas</b>{state.assumptions?.slice(-4).map(item => <p key={item}><CircleAlert size={15}/>{item}</p>)}</div>
              <div className="gateRow"><div><small>Problem Gate</small><strong>{state.gate_status}</strong></div><div><small>Próxima melhor ação</small><strong>{state.next_action}</strong></div></div>
            </section>}

            <section className="evidenceSection">
              <div className="sectionHeading"><div><Badge tone="blue"><FlaskConical size={13}/> Evidence Engine</Badge><h2>Transforme opinião em evidência.</h2></div><span>{state.evidence?.length || 0} registradas</span></div>
              <p className="sectionLead">Registre entrevistas, observações, questionários, dados administrativos ou comportamento real. O sistema classifica a força da evidência, mas não chama isso de validação automaticamente.</p>

              <form className="evidenceForm" onSubmit={handleAddEvidence}>
                <label>Tipo<select value={evidenceDraft.type} onChange={e=>setEvidenceDraft({...evidenceDraft,type:e.target.value})}><option value="interview">Entrevista</option><option value="observation">Observação</option><option value="survey">Questionário</option><option value="behavior">Comportamento real</option><option value="data">Dado administrativo</option><option value="pre-sale">Pré-venda</option><option value="other">Outro</option></select></label>
                <label>Fonte<input value={evidenceDraft.source} onChange={e=>setEvidenceDraft({...evidenceDraft,source:e.target.value})} placeholder="Ex.: entrevista com paciente P03" /></label>
                <label>Data<input type="date" value={evidenceDraft.date} onChange={e=>setEvidenceDraft({...evidenceDraft,date:e.target.value})} /></label>
                <label className="span2">Descrição<textarea value={evidenceDraft.description} onChange={e=>setEvidenceDraft({...evidenceDraft,description:e.target.value})} placeholder="O que foi observado ou medido? Evite conclusões; registre o dado ou comportamento." /></label>
                <label className="span2">Hipótese relacionada<input value={evidenceDraft.hypothesis} onChange={e=>setEvidenceDraft({...evidenceDraft,hypothesis:e.target.value})} placeholder={state.critical_hypothesis || 'Qual hipótese esta evidência testa?'} /></label>
                <div className="span2"><button className="btn primary" type="submit"><Plus size={16}/> Adicionar evidência</button></div>
              </form>

              <div className="evidenceBoard">
                {!state.evidence?.length && <div className="emptyEvidence">Nenhuma evidência registrada ainda. Seu score não deve subir só porque o texto ficou bonito.</div>}
                {state.evidence?.map(item => <article className="evidenceCard" key={item.id}>
                  <div className="evidenceCardTop"><Badge tone={item.strength === 'strong' ? 'success' : item.strength === 'moderate' ? 'blue' : 'neutral'}>{item.strength === 'strong' ? 'FORTE' : item.strength === 'moderate' ? 'MODERADA' : 'FRACA'}</Badge><button onClick={()=>handleRemoveEvidence(item.id)} title="Remover"><Trash2 size={15}/></button></div>
                  <h4>{item.description}</h4><p><b>Fonte:</b> {item.source}</p><p><b>Hipótese:</b> {item.hypothesis || 'Não relacionada'}</p><small>{item.rationale}</small>
                </article>)}
              </div>
            </section>
          </div>

          <aside className="copilotPanel">
            <div className="copilotTop"><Brain size={20}/><div><b>Venture Copilot</b><small>Orchestrator ativo</small></div></div>
            <div className="scoreBox"><div><span>Innovation Score</span><b>{state.opportunity_score || 0}<small>/100</small></b></div><div className="scoreTrack"><i style={{width:`${progress}%`}}/></div><small>Indicador diagnóstico; não é validação científica.</small></div>
            <div className="scoreBreakdown"><p><span>Problema</span><b>{breakdown.problem || 0}/20</b></p><p><span>Evidência</span><b>{breakdown.evidence || 0}/20</b></p><p><span>Valor</span><b>{breakdown.value || 0}/20</b></p><p><span>Viabilidade</span><b>{breakdown.feasibility || 0}/20</b></p><p><span>Validação</span><b>{breakdown.validation || 0}/20</b></p></div>
            <div className="copilotStat"><span>Fase atual</span><b>Discovery + Evidence</b></div>
            <div className="copilotStat"><span>Gate</span><b>{state.gate_status || 'INVESTIGATE'}</b></div>
            <div className="copilotMiniGrid"><div><b>{state.facts?.length || 0}</b><span>Fatos</span></div><div><b>{state.assumptions?.length || 0}</b><span>Hipóteses</span></div><div><b>{state.evidence?.length || 0}</b><span>Evidências</span></div></div>
            <div className="riskBox"><CircleAlert size={18}/><div><small>Risco principal</small><p>{criticalRisk}</p></div></div>
            <div className="nextBox"><FlaskConical size={18}/><div><small>Próxima ação</small><p>{state.next_action}</p></div></div>
            {saved && <p className="savedSignal"><CircleCheck size={16}/> Project State persistido.</p>}
          </aside>
        </div>
      </section>
    </main>
  );
}
