export const createProjectState = (input = {}) => ({
  project_id: input.project_id || crypto.randomUUID(),
  project_name: input.project_name || 'Novo projeto de inovação',
  user_id: input.user_id || null,
  current_phase: 0,
  status: 'active',
  problem: { statement: '', context: '', consequences: '', frequency: '', severity: '' },
  audience: { primary: '', segments: [] },
  jtbd: '',
  facts: [],
  evidence: [],
  assumptions: [],
  unknowns: [],
  risks: [],
  opportunity_score: 0,
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

export function runDiscoveryAgent(rawInput, currentState) {
  const input = normalize(rawInput);
  if (input.length < 20) {
    return {
      analysis: 'Ainda há pouco contexto para formular o problema com segurança.',
      facts: [], evidence: [], assumptions: ['O relato inicial ainda é insuficiente para separar problema de solução.'],
      risks: ['Avançar agora pode cristalizar uma solução antes de compreender o problema.'],
      recommendation: 'INVESTIGATE',
      next_action: 'Explique quem vive o problema, quando ele acontece e o que ocorre se nada for feito.',
      project_updates: {}
    };
  }

  const first = sentence(input);
  const probableSolution = /\b(app|aplicativo|plataforma|sistema|ia|inteligência artificial|software|site)\b/i.test(input);
  const audienceMatch = input.match(/(?:para|com)\s+(pacientes?|alunos?|profissionais?|fisioterapeutas?|professores?|gestores?|equipes?|usuários?)[^,.]*/i);
  const audience = audienceMatch?.[1] || currentState.audience.primary || 'Público ainda não especificado';

  const assumptions = [
    'O problema relatado é frequente o suficiente para justificar uma intervenção.',
    'O público percebe esse problema como relevante.'
  ];
  if (probableSolution) assumptions.push('A solução tecnológica mencionada é melhor do que alternativas mais simples.');

  const risks = [
    'Ainda não há evidência registrada de comportamento real do público.',
    'A frequência e a severidade do problema ainda precisam ser medidas.'
  ];

  const knownSignals = [Boolean(first), audience !== 'Público ainda não especificado', input.length > 80];
  const signalCount = knownSignals.filter(Boolean).length;
  const recommendation = signalCount >= 3 ? 'ADVANCE' : 'INVESTIGATE';
  const score = Math.min(40, 12 + signalCount * 7);

  return {
    analysis: probableSolution
      ? 'Há uma solução embutida no relato. O Venture Copilot separou a hipótese de solução do problema para evitar viés de construção.'
      : 'O relato contém material suficiente para uma primeira formulação do problema, mas ainda exige validação com evidências.',
    facts: [`Relato fornecido pelo usuário: ${input}`],
    evidence: [],
    assumptions,
    risks,
    recommendation,
    next_action: recommendation === 'ADVANCE'
      ? 'Registre pelo menos uma evidência real e teste a hipótese mais arriscada antes de definir a solução.'
      : 'Detalhe o público, a frequência, a consequência e como esse problema é resolvido hoje.',
    project_updates: {
      problem: {
        ...currentState.problem,
        statement: first,
        context: input,
        consequences: currentState.problem.consequences || 'A confirmar com o usuário',
        frequency: currentState.problem.frequency || 'Não medida',
        severity: currentState.problem.severity || 'Não medida'
      },
      audience: { ...currentState.audience, primary: audience },
      jtbd: `Quando enfrentar ${first.toLowerCase()}, quero conseguir progredir com menos fricção, para alcançar um resultado melhor.`,
      opportunity_score: score,
      current_gate: 'PROBLEM_GATE',
      gate_status: recommendation,
      next_action: recommendation === 'ADVANCE'
        ? 'Adicionar evidência real e testar a hipótese mais arriscada.'
        : 'Aprofundar problema, público, frequência e consequência.'
    }
  };
}

export function orchestrate({ action = 'DISCOVERY', input = '', state }) {
  if (!state) throw new Error('Project State é obrigatório.');
  if (action !== 'DISCOVERY') {
    return {
      analysis: `A ação ${action} ainda não faz parte da Sprint 1.`,
      facts: [], evidence: [], assumptions: [], risks: [], recommendation: 'INVESTIGATE',
      next_action: 'Concluir Discovery primeiro.', project_updates: {}
    };
  }
  return runDiscoveryAgent(input, state);
}

export function applyValidatedAgentOutput(state, output, note = 'Discovery Agent') {
  const allowed = ['problem','audience','jtbd','opportunity_score','current_gate','gate_status','next_action'];
  const safeUpdates = Object.fromEntries(
    Object.entries(output.project_updates || {}).filter(([key]) => allowed.includes(key))
  );
  return {
    ...state,
    ...safeUpdates,
    facts: [...state.facts, ...(output.facts || [])],
    evidence: [...state.evidence, ...(output.evidence || [])],
    assumptions: [...new Set([...state.assumptions, ...(output.assumptions || [])])],
    risks: [...new Set([...state.risks, ...(output.risks || [])])],
    decisions: [...state.decisions, {
      id: crypto.randomUUID(),
      type: 'AGENT_ANALYSIS',
      source: note,
      recommendation: output.recommendation,
      created_at: new Date().toISOString()
    }],
    updated_at: new Date().toISOString()
  };
}
