export const createProjectState = (input = {}) => ({
  project_id: input.project_id || crypto.randomUUID(),
  project_name: input.project_name || 'Novo projeto de inovação',
  user_id: input.user_id || null,
  current_phase: 0,
  status: 'active',
  problem: {
    statement: '',
    context: '',
    consequences: '',
    frequency: '',
    severity: '',
    current_solution: '',
    non_solution_cost: ''
  },
  audience: { primary: '', segments: [] },
  jtbd: '',
  facts: [],
  evidence: [],
  assumptions: [],
  unknowns: [],
  risks: [],
  critical_hypothesis: '',
  opportunity_score: 0,
  score_breakdown: { problem: 0, evidence: 0, value: 0, feasibility: 0, validation: 0 },
  value_proposition: '',
  solutions: [],
  selected_solution: '',
  mvp: {},
  business_model: {},
  experiments: [],
  metrics: [],
  decisions: [],
  current_gate: 'PROBLEM_GATE',
  gate_status: 'INVESTIGATE',
  next_action: 'Descreva o problema, ideia ou oportunidade que deseja investigar.',
  updated_at: new Date().toISOString()
});

const normalize = (text = '') => text.trim().replace(/\s+/g, ' ');
const sentence = (text = '') => normalize(text).split(/[.!?]/)[0] || '';
const hasAny = (text, patterns) => patterns.some((pattern) => pattern.test(text));
const uniq = (items) => [...new Set(items.filter(Boolean))];

function inferAudience(input, currentState) {
  const match = input.match(/(?:para|com|entre|em)\s+(pacientes?|alunos?|profissionais?|fisioterapeutas?|professores?|gestores?|equipes?|usuários?|familiares?|cuidadores?|dentistas?|médicos?)[^,.]*/i);
  return match?.[1] || currentState.audience?.primary || 'Público ainda não especificado';
}

function inferFrequency(input, currentState) {
  if (/diari|todo dia|todos os dias/i.test(input)) return 'Diária';
  if (/seman|toda semana/i.test(input)) return 'Semanal';
  if (/mensal|todo mês|todo mes/i.test(input)) return 'Mensal';
  if (/frequent|muitas vezes|recorrent/i.test(input)) return 'Recorrente, não quantificada';
  if (/raramente|eventual|às vezes|as vezes/i.test(input)) return 'Eventual';
  return currentState.problem?.frequency || 'Não medida';
}

function inferConsequence(input, currentState) {
  const consequenceMatch = input.match(/(?:causa|causando|gera|gerando|resulta|resultando|leva a|provoca|consequ[eê]ncia)[^.!?]*/i);
  if (consequenceMatch) return consequenceMatch[0].trim();
  if (hasAny(input, [/risco/i,/erro/i,/atras/i,/perda/i,/dor/i,/custo/i,/retrabalho/i,/abandono/i,/seguran/i])) {
    return 'Há consequência relevante mencionada no relato, ainda não quantificada.';
  }
  return currentState.problem?.consequences || 'Não explicitada';
}

function inferCurrentSolution(input, currentState) {
  const match = input.match(/(?:hoje|atualmente|agora|resolve[m]?|fazem?|usam?|utilizam?)[^.!?]*/i);
  return match?.[0]?.trim() || currentState.problem?.current_solution || 'Não informada';
}

function computeDiscoveryGate({ statement, audience, frequency, consequences, evidenceCount }) {
  const criteria = {
    problem: Boolean(statement && statement.length > 15),
    audience: audience && audience !== 'Público ainda não especificado',
    frequency: frequency && frequency !== 'Não medida',
    consequence: consequences && !['Não explicitada', 'A confirmar com o usuário'].includes(consequences),
    evidence: evidenceCount > 0
  };
  const structural = [criteria.problem, criteria.audience, criteria.frequency, criteria.consequence].filter(Boolean).length;
  if (structural <= 1) return { status: 'PIVOT', criteria };
  if (structural === 4 && criteria.evidence) return { status: 'ADVANCE', criteria };
  return { status: 'INVESTIGATE', criteria };
}

export function calculateInnovationScore(state) {
  const problemCriteria = [
    Boolean(state.problem?.statement),
    state.audience?.primary && state.audience.primary !== 'Público ainda não especificado',
    state.problem?.frequency && state.problem.frequency !== 'Não medida',
    state.problem?.consequences && state.problem.consequences !== 'Não explicitada',
    Boolean(state.problem?.current_solution)
  ];
  const problem = Math.round((problemCriteria.filter(Boolean).length / problemCriteria.length) * 20);

  const evidenceWeights = { weak: 1, moderate: 2.5, strong: 4 };
  const evidenceRaw = (state.evidence || []).reduce((sum, item) => sum + (evidenceWeights[item.strength] || 1), 0);
  const evidence = Math.min(20, Math.round(evidenceRaw * 2));

  const value = Math.min(20, (state.problem?.non_solution_cost ? 8 : 0) + (state.problem?.consequences && state.problem.consequences !== 'Não explicitada' ? 6 : 0) + (state.critical_hypothesis ? 6 : 0));
  const feasibility = state.selected_solution ? 10 : 4;
  const validation = Math.min(20, (state.experiments || []).length * 8 + ((state.evidence || []).length ? 4 : 0));

  return {
    total: problem + evidence + value + feasibility + validation,
    breakdown: { problem, evidence, value, feasibility, validation }
  };
}

export function runDiscoveryAgent(rawInput, currentState) {
  const input = normalize(rawInput);
  if (input.length < 20) {
    return {
      analysis: 'Ainda há pouco contexto para formular o problema com segurança.',
      facts: [],
      evidence: [],
      assumptions: ['O relato inicial ainda é insuficiente para separar problema de solução.'],
      unknowns: ['Quem vive o problema?', 'Quando ele acontece?', 'Qual consequência ocorre se nada for feito?'],
      risks: ['Avançar agora pode cristalizar uma solução antes de compreender o problema.'],
      critical_hypothesis: 'Existe um problema relevante e recorrente para um público identificável.',
      recommendation: 'INVESTIGATE',
      next_action: 'Explique quem vive o problema, quando ele acontece, como resolve hoje e o que ocorre se nada for feito.',
      project_updates: {}
    };
  }

  const first = sentence(input);
  const probableSolution = hasAny(input, [/\bapp\b/i,/aplicativo/i,/plataforma/i,/sistema/i,/inteligência artificial/i,/\bia\b/i,/software/i,/site/i,/chatbot/i]);
  const audience = inferAudience(input, currentState);
  const frequency = inferFrequency(input, currentState);
  const consequences = inferConsequence(input, currentState);
  const currentSolution = inferCurrentSolution(input, currentState);
  const nonSolutionCost = hasAny(input, [/se não/i,/se nao/i,/sem resolver/i,/caso não/i,/caso nao/i])
    ? 'Há custo/consequência de não resolver mencionado no relato.'
    : currentState.problem?.non_solution_cost || '';

  const assumptions = [
    'O problema é relevante o suficiente para motivar mudança de comportamento.',
    'O público reconhece o problema e tentaria resolvê-lo.'
  ];
  if (frequency === 'Não medida') assumptions.push('O problema ocorre com frequência suficiente para justificar uma intervenção.');
  if (probableSolution) assumptions.push('A solução tecnológica citada é superior a alternativas mais simples.');

  const unknowns = [];
  if (audience === 'Público ainda não especificado') unknowns.push('Qual é o usuário primário?');
  if (frequency === 'Não medida') unknowns.push('Com que frequência o problema acontece?');
  if (consequences === 'Não explicitada') unknowns.push('Qual é a consequência concreta de não resolver?');
  if (currentSolution === 'Não informada') unknowns.push('Como o público resolve isso hoje?');
  if (!currentState.evidence?.length) unknowns.push('Que evidência comportamental sustenta que o problema existe?');

  const criticalHypothesis = !currentState.evidence?.length
    ? 'O público realmente vivencia esse problema com frequência e consequência relevantes.'
    : 'A evidência coletada representa o público-alvo e não apenas casos isolados.';

  const gate = computeDiscoveryGate({
    statement: first,
    audience,
    frequency,
    consequences,
    evidenceCount: currentState.evidence?.length || 0
  });

  const draftState = {
    ...currentState,
    problem: {
      ...currentState.problem,
      statement: first,
      context: input,
      consequences,
      frequency,
      severity: currentState.problem?.severity || 'Não medida',
      current_solution: currentSolution,
      non_solution_cost: nonSolutionCost
    },
    audience: { ...currentState.audience, primary: audience },
    critical_hypothesis: criticalHypothesis
  };
  const score = calculateInnovationScore(draftState);

  const nextAction = gate.status === 'ADVANCE'
    ? 'O Problem Gate foi atravessado. Priorize a hipótese crítica e avance para análise da oportunidade.'
    : gate.status === 'PIVOT'
      ? 'Reformule o problema antes de investir em solução: público, contexto e consequência ainda estão frágeis.'
      : 'Colete uma evidência real e preencha as lacunas prioritárias do Discovery.';

  return {
    analysis: probableSolution
      ? 'Detectei uma solução embutida no relato. Ela foi tratada como hipótese, não como resposta. O foco permanece no problema, no comportamento atual e na consequência.'
      : 'O problema foi estruturado em usuário, contexto, frequência, consequência e solução atual. Os pontos sem evidência permanecem marcados como hipótese ou desconhecido.',
    facts: [`Relato do usuário em ${new Date().toLocaleDateString('pt-BR')}: ${input}`],
    evidence: [],
    assumptions,
    unknowns,
    risks: uniq([
      !currentState.evidence?.length && 'Ainda não há evidência registrada de comportamento real do público.',
      frequency === 'Não medida' && 'A frequência do problema permanece desconhecida.',
      probableSolution && 'Há risco de viés de solução: a tecnologia apareceu antes de a necessidade estar comprovada.'
    ]),
    critical_hypothesis: criticalHypothesis,
    gate_criteria: gate.criteria,
    recommendation: gate.status,
    next_action: nextAction,
    project_updates: {
      problem: draftState.problem,
      audience: draftState.audience,
      jtbd: `Quando ${first.toLowerCase()}, eu quero resolver a situação com menos fricção, para evitar ${consequences.toLowerCase()}.`,
      unknowns,
      critical_hypothesis: criticalHypothesis,
      opportunity_score: score.total,
      score_breakdown: score.breakdown,
      current_gate: 'PROBLEM_GATE',
      gate_status: gate.status,
      next_action: nextAction
    }
  };
}

export function classifyEvidence({ type = 'observation', description = '', source = '' }) {
  const text = `${type} ${description} ${source}`.toLowerCase();
  if (/pagamento|compra|uso real|comportamento|prontuário|prontuario|dados? administrativos?|log de uso|pré-venda|pre-venda/.test(text)) {
    return { strength: 'strong', rationale: 'Há sinal comportamental ou dado independente diretamente relacionado ao problema.' };
  }
  if (/entrevista|observação|observacao|questionário|questionario|grupo focal|pesquisa com usuários|pesquisa com usuarios/.test(text)) {
    return { strength: 'moderate', rationale: 'Há coleta estruturada com usuários, mas a evidência ainda pode depender de relato e amostra.' };
  }
  return { strength: 'weak', rationale: 'A evidência é principalmente opinião, percepção ou fonte indireta e precisa de triangulação.' };
}

export function addEvidence(state, draft) {
  const description = normalize(draft.description || '');
  if (description.length < 10) throw new Error('Descreva a evidência com pelo menos 10 caracteres.');
  const classification = classifyEvidence(draft);
  const item = {
    id: crypto.randomUUID(),
    type: draft.type || 'observation',
    source: normalize(draft.source || 'Fonte não informada'),
    date: draft.date || new Date().toISOString().slice(0, 10),
    description,
    hypothesis: normalize(draft.hypothesis || state.critical_hypothesis || ''),
    strength: draft.strength || classification.strength,
    rationale: draft.rationale || classification.rationale,
    created_at: new Date().toISOString()
  };
  const evidence = [...(state.evidence || []), item];
  const nextBase = { ...state, evidence };
  const gate = computeDiscoveryGate({
    statement: nextBase.problem?.statement,
    audience: nextBase.audience?.primary,
    frequency: nextBase.problem?.frequency,
    consequences: nextBase.problem?.consequences,
    evidenceCount: evidence.length
  });
  const scored = calculateInnovationScore(nextBase);
  return {
    ...nextBase,
    opportunity_score: scored.total,
    score_breakdown: scored.breakdown,
    gate_status: gate.status,
    next_action: gate.status === 'ADVANCE'
      ? 'Problem Gate atravessado: teste a hipótese crítica ou avance para Opportunity.'
      : 'Continue coletando evidências e reduzindo as incertezas críticas.',
    decisions: [...(state.decisions || []), {
      id: crypto.randomUUID(), type: 'EVIDENCE_ADDED', source: 'Evidence Engine', evidence_id: item.id, created_at: new Date().toISOString()
    }],
    updated_at: new Date().toISOString()
  };
}

export function removeEvidence(state, evidenceId) {
  const evidence = (state.evidence || []).filter(item => item.id !== evidenceId);
  const next = { ...state, evidence };
  const scored = calculateInnovationScore(next);
  return { ...next, opportunity_score: scored.total, score_breakdown: scored.breakdown, updated_at: new Date().toISOString() };
}

export function orchestrate({ action = 'DISCOVERY', input = '', state }) {
  if (!state) throw new Error('Project State é obrigatório.');
  if (action === 'DISCOVERY') return runDiscoveryAgent(input, state);
  return {
    analysis: `A ação ${action} ainda não está habilitada nesta fase.`,
    facts: [], evidence: [], assumptions: [], unknowns: [], risks: [], recommendation: 'INVESTIGATE',
    next_action: 'Concluir Discovery e Evidence Engine primeiro.', project_updates: {}
  };
}

export function applyValidatedAgentOutput(state, output, note = 'Discovery Agent') {
  const allowed = ['problem','audience','jtbd','unknowns','critical_hypothesis','opportunity_score','score_breakdown','current_gate','gate_status','next_action'];
  const safeUpdates = Object.fromEntries(Object.entries(output.project_updates || {}).filter(([key]) => allowed.includes(key)));
  return {
    ...state,
    ...safeUpdates,
    facts: [...(state.facts || []), ...(output.facts || [])],
    evidence: [...(state.evidence || []), ...(output.evidence || [])],
    assumptions: uniq([...(state.assumptions || []), ...(output.assumptions || [])]),
    unknowns: uniq([...(safeUpdates.unknowns || state.unknowns || []), ...(output.unknowns || [])]),
    risks: uniq([...(state.risks || []), ...(output.risks || [])]),
    critical_hypothesis: output.critical_hypothesis || safeUpdates.critical_hypothesis || state.critical_hypothesis || '',
    decisions: [...(state.decisions || []), {
      id: crypto.randomUUID(),
      type: 'AGENT_ANALYSIS',
      source: note,
      recommendation: output.recommendation,
      rationale: output.analysis,
      created_at: new Date().toISOString()
    }],
    updated_at: new Date().toISOString()
  };
}
