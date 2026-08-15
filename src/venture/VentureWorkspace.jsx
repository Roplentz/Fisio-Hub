import React, { useEffect, useMemo, useState } from 'react';
import { Brain, ChevronLeft, CircleAlert, CircleCheck, FlaskConical, Lightbulb, Plus, Save, Sparkles, Target, Trash2, WandSparkles, Check } from 'lucide-react';
import { addEvidence, applyValidatedAgentOutput, createProjectState, orchestrate, removeEvidence, selectSolution } from './core.js';
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
  const [opportunityAnalysis, setOpportunityAnalysis] = useState(null);
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
  const canGenerateOpportunity = state.gate_status === 'ADVANCE' || (state.problem?.statement && (state.evidence?.length || 0) > 0);

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
      const next = applyValidatedAgentOutput(state, output, 'Discovery Agent');
      setAnalysis(output);
      await commit(next);
    } catch (err) {
      setError(err.message || 'Falha ao analisar o projeto.');
    } finally { setBusy(false); }
  }

  async function generateOpportunities() {
    setBusy(true); setSaved(false); setError('');
    try {
      const output = orchestrate({ action: 'OPPORTUNITY', state });
      const next = applyValidatedAgentOutput(state, output, 'Opportunity Agent');
      setOpportunityAnalysis(output);
      await commit(next);
    } catch (err) {
      setError(err.message || 'Não foi possível gerar alternativas.');
    } finally { setBusy(false); }
  }

  async function chooseSolution(id) {
    setBusy(true); setSaved(false); setError('');
    try { await commit(selectSolution(state, id)); }
    catch (err) { setError(err.message || 'Não foi possível selecionar a alternativa.'); }
    finally { setBusy(false); }
  }

  async function persist() {
    setBusy(true); setError('');
    try { await commit(state); }
    catch (err) { setError(err.message || 'Falha ao salvar o projeto.'); }
    finally { setBusy(false); }
  }

  async function handleAddEvidence(event) {
    event.preventDefault(); setError(''); setSaved(false);
    try { await commit(addEvidence(state, evidenceDraft)); setEvidenceDraft(emptyEvidence()); }
    catch (err) { setError(err.message || 'Não foi possível registrar a evidência.'); }
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
        <div className="ventureBrand"><Brain size={22}/><div><b>Venture Copilot</b><small>Sprint 4 · Opportunity Agent</small></div></div>
        <div className="journeyList">
          {steps.map((step, index) => {
            const active = index <= 5;
            const done = (index === 0 && state.problem?.statement) || (index === 2 && state.evidence?.length) || (index >= 3 && index <= 5 && state.selected_solution);
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
              <p>Inclua, se souber: quem vive o problema, quando acontece, frequência, consequência, como é resolvido hoje e o que acontece se nada for feito.</p>
              <textarea value={input} onChange={e => { setInput(e.target.value); setSaved(false); }} placeholder="Ex.: Pacientes recebem alta hospitalar com muitas orientações..." disabled={!loaded} />
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
              <div className="gateRow"><div><small>Problem Gate</small><strong>{state.gate_status}</strong></div><div><small>Próxima melhor ação</small><strong>{state.next_action}</strong></div></div>
            </section>}

            <section className="evidenceSection">
              <div className="sectionHeading"><div><Badge tone="blue"><FlaskConical size={13}/> Evidence Engine</Badge><h2>Transforme opinião em evidência.</h2></div><span>{state.evidence?.length || 0} registradas</span></div>
              <p className="sectionLead">Registre entrevistas, observações, questionários, dados administrativos ou comportamento real.</p>
              <form className="evidenceForm" onSubmit={handleAddEvidence}>
                <label>Tipo<select value={evidenceDraft.type} onChange={e=>setEvidenceDraft({...evidenceDraft,type:e.target.value})}><option value="interview">Entrevista</option><option value="observation">Observação</option><option value="survey">Questionário</option><option value="behavior">Comportamento real</option><option value="data">Dado administrativo</option><option value="pre-sale">Pré-venda</option><option value="other">Outro</option></select></label>
                <label>Fonte<input value={evidenceDraft.source} onChange={e=>setEvidenceDraft({...evidenceDraft,source:e.target.value})} placeholder="Ex.: entrevista com paciente P03" /></label>
                <label>Data<input type="date" value={evidenceDraft.date} onChange={e=>setEvidenceDraft({...evidenceDraft,date:e.target.value})} /></label>
                <label className="span2">Descrição<textarea value={evidenceDraft.description} onChange={e=>setEvidenceDraft({...evidenceDraft,description:e.target.value})} placeholder="O que foi observado ou medido?" /></label>
                <label className="span2">Hipótese relacionada<input value={evidenceDraft.hypothesis} onChange={e=>setEvidenceDraft({...evidenceDraft,hypothesis:e.target.value})} placeholder={state.critical_hypothesis || 'Qual hipótese esta evidência testa?'} /></label>
                <div className="span2"><button className="btn primary" type="submit"><Plus size={16}/> Adicionar evidência</button></div>
              </form>
              <div className="evidenceBoard">
                {!state.evidence?.length && <div className="emptyEvidence">Nenhuma evidência registrada ainda.</div>}
                {state.evidence?.map(item => <article className="evidenceCard" key={item.id}>
                  <div className="evidenceCardTop"><Badge tone={item.strength === 'strong' ? 'success' : item.strength === 'moderate' ? 'blue' : 'neutral'}>{item.strength === 'strong' ? 'FORTE' : item.strength === 'moderate' ? 'MODERADA' : 'FRACA'}</Badge><button onClick={()=>handleRemoveEvidence(item.id)} title="Remover"><Trash2 size={15}/></button></div>
                  <h4>{item.description}</h4><p><b>Fonte:</b> {item.source}</p><p><b>Hipótese:</b> {item.hypothesis || 'Não relacionada'}</p><small>{item.rationale}</small>
                </article>)}
              </div>
            </section>

            <section className="opportunitySection">
              <div className="sectionHeading"><div><Badge tone="blue"><WandSparkles size={13}/> Opportunity Agent</Badge><h2>Compare soluções antes de se apaixonar por uma.</h2></div><Badge tone={state.opportunity_gate === 'ADVANCE' ? 'success' : 'neutral'}>{state.opportunity_gate || 'LOCKED'}</Badge></div>
              <p className="sectionLead">O agente compara cinco caminhos — inclusive opções não tecnológicas — por dor, benefício, recorrência, simplicidade e monetização. A prioridade é valor percebido × simplicidade de execução.</p>
              <div className="opportunityCallout">
                <div><b>Regra do Sprint 4</b><p>Não vence a solução mais sofisticada. Vence a menor solução capaz de entregar valor relevante de ponta a ponta.</p></div>
                <button className="btn primary" disabled={busy || !canGenerateOpportunity} onClick={generateOpportunities}><WandSparkles size={16}/>{state.solutions?.length ? 'Recalcular alternativas' : 'Gerar alternativas'}</button>
              </div>
              {!canGenerateOpportunity && <div className="opportunityLocked"><CircleAlert size={16}/> Registre pelo menos uma evidência e avance no Problem Gate antes de comprometer o projeto com uma solução.</div>}
              {opportunityAnalysis && <p className="opportunitySummary">{opportunityAnalysis.analysis}</p>}

              {!!state.solutions?.length && <div className="opportunityMatrix">
                <div className="matrixHeader"><span>Solução</span><span>Dor</span><span>Benefício</span><span>Recorr.</span><span>Simplic.</span><span>Monet.</span><span>Fit</span><span></span></div>
                {state.solutions.map((solution,index) => {
                  const selected = state.selected_solution?.id === solution.id;
                  return <article key={solution.id} className={`matrixRow ${selected ? 'selected' : ''}`}>
                    <div className="solutionName"><div><b>{solution.name}</b><small>{solution.type}</small></div>{index === 0 && <Badge tone="success">RECOMENDADA</Badge>}</div>
                    <span>{solution.scores.pain}</span><span>{solution.scores.benefit}</span><span>{solution.scores.recurrence}</span><span>{solution.scores.simplicity}</span><span>{solution.scores.monetization}</span><strong>{solution.execution_fit}</strong>
                    <button className={selected ? 'solutionSelected' : 'solutionChoose'} onClick={()=>chooseSolution(solution.id)} disabled={busy}>{selected ? <><Check size={14}/> Escolhida</> : 'Escolher'}</button>
                    <div className="solutionDetail">
                      <p>{solution.description}</p>
                      <div><b>MVP:</b> {solution.mvp}</div><div><b>Monetização:</b> {solution.monetization}</div><div><b>Diferencial:</b> {solution.differential}</div>
                    </div>
                  </article>;
                })}
              </div>}

              {state.selected_solution && <div className="selectedSolutionCard">
                <div><Badge tone="success">SOLUTION CARD</Badge><h3>{state.selected_solution.name}</h3><p>{state.value_proposition}</p></div>
                <div className="selectedSolutionGrid"><div><span>Tipo</span><b>{state.selected_solution.type}</b></div><div><span>Fit</span><b>{state.selected_solution.execution_fit}</b></div><div><span>Opportunity Gate</span><b>{state.opportunity_gate}</b></div></div>
              </div>}
            </section>
          </div>

          <aside className="copilotPanel">
            <div className="copilotTop"><Brain size={20}/><div><b>Venture Copilot</b><small>Orchestrator ativo</small></div></div>
            <div className="scoreBox"><div><span>Innovation Score</span><b>{state.opportunity_score || 0}<small>/100</small></b></div><div className="scoreTrack"><i style={{width:`${progress}%`}}/></div><small>Indicador diagnóstico; não é validação científica.</small></div>
            <div className="scoreBreakdown"><p><span>Problema</span><b>{breakdown.problem || 0}/20</b></p><p><span>Evidência</span><b>{breakdown.evidence || 0}/20</b></p><p><span>Valor</span><b>{breakdown.value || 0}/20</b></p><p><span>Viabilidade</span><b>{breakdown.feasibility || 0}/20</b></p><p><span>Validação</span><b>{breakdown.validation || 0}/20</b></p></div>
            <div className="copilotStat"><span>Fase atual</span><b>{state.selected_solution ? 'Solution selected' : 'Opportunity'}</b></div>
            <div className="copilotStat"><span>Problem Gate</span><b>{state.gate_status || 'INVESTIGATE'}</b></div>
            <div className="copilotStat"><span>Opportunity Gate</span><b>{state.opportunity_gate || 'LOCKED'}</b></div>
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
