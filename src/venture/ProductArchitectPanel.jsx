import React from 'react';
import { Boxes, CheckCircle2, FileText, Layers3 } from 'lucide-react';
import { generateProductArchitecture } from './product-architect.js';

function Tier({ label, items }) {
  return <div className="productTier"><b>{label}</b>{items?.map(item => <span key={item}>{item}</span>)}</div>;
}

export default function ProductArchitectPanel({ state, busy, commit, setError, setSaved }) {
  async function generate() {
    setError(''); setSaved(false);
    try { await commit(generateProductArchitecture(state)); }
    catch (err) { setError(err.message || 'Não foi possível gerar a arquitetura do produto.'); }
  }

  const architecture = state.product_architecture;
  const prd = state.prd;
  return <section className="productArchitectSection">
    <div className="sectionHeading">
      <div><span className="ventureBadge blue"><Boxes size={13}/> Product Architect</span><h2>Transforme a solução em um produto mínimo completo.</h2></div>
      <span className={`ventureBadge ${state.product_gate === 'ADVANCE' ? 'success' : 'neutral'}`}>{state.product_gate || 'LOCKED'}</span>
    </div>
    <p className="sectionLead">O agente cria proposta de valor, jornada, telas, funcionalidades MUST/SHOULD/LATER, critérios de aceitação e um PRD vivo. A regra é simples: se a função não for necessária para entregar o valor principal, ela sai do MVP.</p>

    <div className="productArchitectCallout">
      <div><b>MVP Killer Question</b><p>Se retirarmos esta funcionalidade, o usuário ainda recebe o valor principal? Se sim, ela não é MUST.</p></div>
      <button className="btn primary" disabled={busy || !state.selected_solution} onClick={generate}><Layers3 size={16}/>{architecture ? 'Regerar arquitetura' : 'Gerar arquitetura do produto'}</button>
    </div>
    {!state.selected_solution && <div className="opportunityLocked">Escolha uma solução no Opportunity Lab antes de arquitetar o produto.</div>}

    {architecture && <>
      <div className="valuePropositionCard"><small>PROPOSTA DE VALOR</small><strong>{state.value_proposition}</strong></div>

      <div className="productJourney">
        {architecture.journey.map(step => <article key={step.step}><span>{step.step}</span><div><b>{step.name}</b><p>{step.goal}</p><small>{step.success}</small></div></article>)}
      </div>

      <div className="productColumns">
        <div className="screenMap"><h3>Mapa de telas</h3>{architecture.screens.map(screen => <div key={screen.id}><b>{screen.name}</b><span>{screen.purpose}</span></div>)}</div>
        <div className="mvpScope"><h3>Escopo MVP</h3><Tier label="MUST" items={state.mvp?.must}/><Tier label="SHOULD" items={state.mvp?.should}/><Tier label="LATER" items={state.mvp?.later}/></div>
      </div>

      <div className="featureArchitecture"><h3>Arquitetura funcional</h3>{architecture.features.map(item => <article key={item.id}><div><span className={`featureTier ${item.tier.toLowerCase()}`}>{item.tier}</span><b>{item.title}</b></div><p>{item.problem}</p><small><strong>Critério:</strong> {item.acceptance}</small></article>)}</div>

      {prd && <div className="prdCard">
        <div className="prdHeader"><FileText size={20}/><div><small>PRD VIVO</small><h3>{prd.title}</h3></div></div>
        <p>{prd.vision}</p>
        <div className="prdMeta"><div><span>Público</span><b>{prd.audience}</b></div><div><span>Requisitos MUST</span><b>{prd.functional_requirements.length}</b></div><div><span>MVP Gate</span><b>{state.product_gate}</b></div></div>
        <div className="prdRequirements">{prd.functional_requirements.map(req => <div key={req.id}><CheckCircle2 size={15}/><span><b>{req.id} · {req.requirement}</b><small>{req.acceptance}</small></span></div>)}</div>
      </div>}
    </>}
  </section>;
}
