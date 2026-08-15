export const createProjectState = (input = {}) => ({
  project_id: input.project_id || crypto.randomUUID(),
  project_name: input.project_name || 'Novo projeto de inovação',
  user_id: input.user_id || null,
  current_phase: 0,
  status: 'active',
  problem: {
    statement: '', context: '', consequences: '', frequency: '', severity: '',
    current_solution: '', non_solution_cost: ''
  },
  audience: { primary: '', segments: [] },
  jtbd: '',
  facts: [], evidence: [], assumptions: [], unknowns: [], risks: [],
  critical_hypothesis: '',
  opportunity_score: 0,
  score_breakdown: { problem: 0, evidence: 0, value: 0, feasibility: 0, validation: 0 },
  value_proposition: '',
  solutions: [],
  selected_solution: '',
  opportunity_gate: 'LOCKED',
  mvp: {}, business_model: {}, experiments: [], metrics: [], decisions: [],
  current_gate: 'PROBLEM_GATE',
  gate_status: 'INVESTIGATE',
  next_action: 'Descreva o problema, ideia ou oportunidade que deseja investigar.',
  updated_at: new Date().toISOString()
});

const normalize = (text = '') => text.trim().replace(/\s+/g, ' ');
const sentence = (text = '') => normalize(text).split(/[.!?]/)[0] || '';
const hasAny = (text, patterns) => patterns.some((pattern) => pattern.test(text));
const uniq = (items) => [...new Set(items.filter(Boolean))];
const clamp10 = (value) => Math.max(0, Math.min(10, Math.round(value)));

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
  if (hasAny(input, [/risco/i,/erro/i,/atras/i,/perda/i,/dor/i,/custo/i,/retrabalho/i,/abandono/i,/seguran/i])) return 'Há consequência relevante mencionada no relato, ainda não quantificada.';
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
  const feasibility = state.selected_solution ? Math.min(20, 8 + Math.round((state.selected_solution.scores?.simplicity || 5) * 1.2)) : 4;
  const validation = Math.min(20, (state.experiments || []).length * 8 + ((state.evidence || []).length ? 4 : 0));
  return { total: problem + evidence + value + feasibility + validation, breakdown: { problem, evidence, value, feasibility, validation } };
}

export function runDiscoveryAgent(rawInput, currentState) {
  const input = normalize(rawInput);
  if (input.length < 20) {
    return {
      analysis: 'Ainda há pouco contexto para formular o problema com segurança.',
      facts: [], evidence: [], assumptions: ['O relato inicial ainda é insuficiente para separar problema de solução.'],
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
  const nonSolutionCost = hasAny(input, [/se não/i,/se nao/i,/sem resolver/i,/caso não/i,/caso nao/i]) ? 'Há custo/consequência de não resolver mencionado no relato.' : currentState.problem?.non_solution_cost || '';
  const assumptions = ['O problema é relevante o suficiente para motivar mudança de comportamento.','O público reconhece o problema e tentaria resolvê-lo.'];
  if (frequency === 'Não medida') assumptions.push('O problema ocorre com frequência suficiente para justificar uma intervenção.');
  if (probableSolution) assumptions.push('A solução tecnológica citada é superior a alternativas mais simples.');
  const unknowns = [];
  if (audience === 'Público ainda não especificado') unknowns.push('Qual é o usuário primário?');
  if (frequency === 'Não medida') unknowns.push('Com que frequência o problema acontece?');
  if (consequences === 'Não explicitada') unknowns.push('Qual é a consequência concreta de não resolver?');
  if (currentSolution === 'Não informada') unknowns.push('Como o público resolve isso hoje?');
  if (!currentState.evidence?.length) unknowns.push('Que evidência comportamental sustenta que o problema existe?');
  const criticalHypothesis = !currentState.evidence?.length ? 'O público realmente vivencia esse problema com frequência e consequência relevantes.' : 'A evidência coletada representa o público-alvo e não apenas casos isolados.';
  const gate = computeDiscoveryGate({ statement: first, audience, frequency, consequences, evidenceCount: currentState.evidence?.length || 0 });
  const draftState = {
    ...currentState,
    problem: { ...currentState.problem, statement: first, context: input, consequences, frequency, severity: currentState.problem?.severity || 'Não medida', current_solution: currentSolution, non_solution_cost: nonSolutionCost },
    audience: { ...currentState.audience, primary: audience }, critical_hypothesis: criticalHypothesis
  };
  const score = calculateInnovationScore(draftState);
  const nextAction = gate.status === 'ADVANCE' ? 'O Problem Gate foi atravessado. Gere e compare alternativas no Opportunity Lab.' : gate.status === 'PIVOT' ? 'Reformule o problema antes de investir em solução.' : 'Colete uma evidência real e preencha as lacunas prioritárias do Discovery.';
  return {
    analysis: probableSolution ? 'Detectei uma solução embutida no relato. Ela foi tratada como hipótese, não como resposta.' : 'O problema foi estruturado em usuário, contexto, frequência, consequência e solução atual.',
    facts: [`Relato do usuário em ${new Date().toLocaleDateString('pt-BR')}: ${input}`], evidence: [], assumptions, unknowns,
    risks: uniq([!currentState.evidence?.length && 'Ainda não há evidência registrada de comportamento real do público.', frequency === 'Não medida' && 'A frequência do problema permanece desconhecida.', probableSolution && 'Há risco de viés de solução.']),
    critical_hypothesis: criticalHypothesis, gate_criteria: gate.criteria, recommendation: gate.status, next_action: nextAction,
    project_updates: {
      problem: draftState.problem, audience: draftState.audience,
      jtbd: `Quando ${first.toLowerCase()}, eu quero resolver a situação com menos fricção, para evitar ${consequences.toLowerCase()}.`,
      unknowns, critical_hypothesis: criticalHypothesis, opportunity_score: score.total, score_breakdown: score.breakdown,
      current_gate: 'PROBLEM_GATE', gate_status: gate.status, next_action: nextAction
    }
  };
}

export function classifyEvidence({ type = 'observation', description = '', source = '' }) {
  const text = `${type} ${description} ${source}`.toLowerCase();
  if (/pagamento|compra|uso real|comportamento|prontuário|prontuario|dados? administrativos?|log de uso|pré-venda|pre-venda/.test(text)) return { strength: 'strong', rationale: 'Há sinal comportamental ou dado independente diretamente relacionado ao problema.' };
  if (/entrevista|observação|observacao|questionário|questionario|grupo focal|pesquisa com usuários|pesquisa com usuarios/.test(text)) return { strength: 'moderate', rationale: 'Há coleta estruturada com usuários, mas a evidência ainda pode depender de relato e amostra.' };
  return { strength: 'weak', rationale: 'A evidência é principalmente opinião, percepção ou fonte indireta e precisa de triangulação.' };
}

export function addEvidence(state, draft) {
  const description = normalize(draft.description || '');
  if (description.length < 10) throw new Error('Descreva a evidência com pelo menos 10 caracteres.');
  const classification = classifyEvidence(draft);
  const item = {
    id: crypto.randomUUID(), type: draft.type || 'observation', source: normalize(draft.source || 'Fonte não informada'),
    date: draft.date || new Date().toISOString().slice(0, 10), description,
    hypothesis: normalize(draft.hypothesis || state.critical_hypothesis || ''), strength: draft.strength || classification.strength,
    rationale: draft.rationale || classification.rationale, created_at: new Date().toISOString()
  };
  const evidence = [...(state.evidence || []), item];
  const nextBase = { ...state, evidence };
  const gate = computeDiscoveryGate({ statement: nextBase.problem?.statement, audience: nextBase.audience?.primary, frequency: nextBase.problem?.frequency, consequences: nextBase.problem?.consequences, evidenceCount: evidence.length });
  const scored = calculateInnovationScore(nextBase);
  return {
    ...nextBase, opportunity_score: scored.total, score_breakdown: scored.breakdown, gate_status: gate.status,
    next_action: gate.status === 'ADVANCE' ? 'Problem Gate atravessado: gere alternativas no Opportunity Lab.' : 'Continue coletando evidências e reduzindo as incertezas críticas.',
    decisions: [...(state.decisions || []), { id: crypto.randomUUID(), type: 'EVIDENCE_ADDED', source: 'Evidence Engine', evidence_id: item.id, created_at: new Date().toISOString() }], updated_at: new Date().toISOString()
  };
}

export function removeEvidence(state, evidenceId) {
  const evidence = (state.evidence || []).filter(item => item.id !== evidenceId);
  const next = { ...state, evidence };
  const scored = calculateInnovationScore(next);
  return { ...next, opportunity_score: scored.total, score_breakdown: scored.breakdown, updated_at: new Date().toISOString() };
}

function baseOpportunityScores(state, overrides = {}) {
  const evidenceQuality = Math.min(10, (state.evidence || []).reduce((sum, item) => sum + ({ weak: 1, moderate: 2, strong: 3 }[item.strength] || 1), 0));
  const pain = clamp10(5 + (state.problem?.consequences && state.problem.consequences !== 'Não explicitada' ? 2 : 0) + (state.problem?.non_solution_cost ? 1 : 0) + Math.min(2, evidenceQuality / 3));
  const recurrence = clamp10(state.problem?.frequency === 'Diária' ? 9 : state.problem?.frequency === 'Semanal' ? 8 : state.problem?.frequency === 'Mensal' ? 6 : state.problem?.frequency?.startsWith('Recorrente') ? 7 : 5);
  return { pain, recurrence, ...overrides };
}

function makeSolution(state, { name, type, description, input, processing, output, differential, monetization, mvp, scores }) {
  const normalizedScores = {
    pain: clamp10(scores.pain), benefit: clamp10(scores.benefit), recurrence: clamp10(scores.recurrence),
    simplicity: clamp10(scores.simplicity), monetization: clamp10(scores.monetization)
  };
  const valuePerceived = Math.round((normalizedScores.pain + normalizedScores.benefit + normalizedScores.recurrence + normalizedScores.monetization) / 4 * 10) / 10;
  const executionFit = Math.round((valuePerceived * normalizedScores.simplicity) * 10) / 10;
  return { id: crypto.randomUUID(), name, type, description, user: state.audience?.primary || 'Público-alvo', jtbd: state.jtbd, input, processing, output, differential, monetization, mvp, scores: normalizedScores, value_perceived: valuePerceived, execution_fit: executionFit };
}

export function runOpportunityAgent(state) {
  if (!state?.problem?.statement) throw new Error('Conclua o Discovery antes de gerar alternativas.');
  const base = baseOpportunityScores(state);
  const problem = state.problem.statement;
  const current = state.problem.current_solution || 'processo atual';
  const solutions = [
    makeSolution(state, {
      name: 'Serviço concierge guiado', type: 'Serviço',
      description: `Resolver ${problem.toLowerCase()} por meio de uma jornada humana padronizada antes de automatizar.`,
      input: 'Solicitação e contexto do usuário', processing: 'Protocolo humano padronizado + checklist', output: 'Orientação/resultado entregue de ponta a ponta',
      differential: 'Valida valor com pouca tecnologia e gera aprendizado rápido.', monetization: 'Pagamento por atendimento ou pacote', mvp: 'Formulário + protocolo + atendimento manual',
      scores: { ...base, benefit: 8, simplicity: 9, monetization: 7 }
    }),
    makeSolution(state, {
      name: 'Fluxo WhatsApp assistido', type: 'Automação leve',
      description: `Organizar a resolução de ${problem.toLowerCase()} em um canal já usado pelo público.`,
      input: 'Mensagem ou formulário curto', processing: 'Roteiro decisório + respostas padronizadas + intervenção humana quando necessário', output: 'Próxima ação clara e acompanhamento',
      differential: 'Baixa barreira de adoção e rápida implantação.', monetization: 'Assinatura B2B ou pacote de uso', mvp: 'WhatsApp + planilha/banco simples + templates',
      scores: { ...base, benefit: 8, simplicity: 8, monetization: 8 }
    }),
    makeSolution(state, {
      name: 'Portal web focado na tarefa', type: 'Produto digital',
      description: `Centralizar a tarefa principal relacionada a ${problem.toLowerCase()} sem criar um sistema amplo.`,
      input: 'Dados essenciais do caso', processing: 'Regras de negócio e organização do fluxo', output: 'Resultado estruturado, histórico e próxima ação',
      differential: `Substitui parte da fricção do ${current} com uma experiência específica.`, monetization: 'Freemium ou assinatura', mvp: '1 fluxo principal + resultado + histórico',
      scores: { ...base, benefit: 9, simplicity: 7, monetization: 8 }
    }),
    makeSolution(state, {
      name: 'Copiloto com IA', type: 'IA aplicada',
      description: `Usar IA apenas onde ela reduz trabalho cognitivo em ${problem.toLowerCase()}.`,
      input: 'Contexto estruturado + texto/dados do usuário', processing: 'Modelo de IA com regras e revisão humana', output: 'Análise, recomendação ou conteúdo personalizado',
      differential: 'Personalização e velocidade quando a tarefa exige interpretação.', monetization: 'Assinatura por usuário ou consumo', mvp: 'Uma função de IA com revisão humana e log',
      scores: { ...base, benefit: 9, simplicity: 5, monetization: 8 }
    }),
    makeSolution(state, {
      name: 'Kit/protocolo de autoatendimento', type: 'Solução não tecnológica',
      description: `Redesenhar instruções, checklist e materiais para reduzir ${problem.toLowerCase()} sem software.`,
      input: 'Situação e necessidade do usuário', processing: 'Protocolo visual e sequência orientada', output: 'Ação correta com menos dúvida e retrabalho',
      differential: 'Menor custo e ótima solução-controle para testar se tecnologia é realmente necessária.', monetization: 'Licença do método, treinamento ou venda do kit', mvp: 'Checklist + guia + piloto supervisionado',
      scores: { ...base, benefit: 7, simplicity: 10, monetization: 6 }
    })
  ].sort((a,b) => b.execution_fit - a.execution_fit);

  const recommended = solutions[0];
  const hasEvidence = (state.evidence || []).length > 0;
  const gate = state.gate_status !== 'ADVANCE' ? 'INVESTIGATE' : hasEvidence && recommended.execution_fit >= 55 ? 'ADVANCE' : 'INVESTIGATE';
  return {
    analysis: `Foram comparadas cinco abordagens, incluindo soluções não tecnológicas. A recomendação privilegia valor percebido × simplicidade de execução, não sofisticação.`,
    recommendation: gate,
    next_action: gate === 'ADVANCE' ? `Selecionar “${recommended.name}” ou justificar outra escolha e avançar para arquitetura do produto.` : 'Aprimore as evidências do problema antes de comprometer recursos com a solução.',
    project_updates: { solutions, opportunity_gate: gate, current_gate: 'OPPORTUNITY_GATE', next_action: gate === 'ADVANCE' ? `Selecionar uma alternativa e registrar a decisão.` : 'Reforçar evidências antes de selecionar a solução.' }
  };
}

export function selectSolution(state, solutionId) {
  const solution = (state.solutions || []).find(item => item.id === solutionId);
  if (!solution) throw new Error('Alternativa não encontrada.');
  const nextBase = { ...state, selected_solution: solution, value_proposition: `${solution.user} consegue ${solution.output.toLowerCase()} por meio de ${solution.name.toLowerCase()}, com menos fricção do que ${state.problem?.current_solution || 'a alternativa atual'}.`, current_phase: Math.max(state.current_phase || 0, 4), current_gate: 'SOLUTION_GATE', gate_status: 'ADVANCE', opportunity_gate: 'ADVANCE', next_action: 'Solução selecionada. Avance para Product Architecture e definição do MVP.' };
  const scored = calculateInnovationScore(nextBase);
  return { ...nextBase, opportunity_score: scored.total, score_breakdown: scored.breakdown, decisions: [...(state.decisions || []), { id: crypto.randomUUID(), type: 'SOLUTION_SELECTED', source: 'Opportunity Agent', solution_id: solution.id, solution_name: solution.name, created_at: new Date().toISOString() }], updated_at: new Date().toISOString() };
}

export function orchestrate({ action = 'DISCOVERY', input = '', state }) {
  if (!state) throw new Error('Project State é obrigatório.');
  if (action === 'DISCOVERY') return runDiscoveryAgent(input, state);
  if (action === 'OPPORTUNITY') return runOpportunityAgent(state);
  return { analysis: `A ação ${action} ainda não está habilitada nesta fase.`, facts: [], evidence: [], assumptions: [], unknowns: [], risks: [], recommendation: 'INVESTIGATE', next_action: 'Concluir a etapa atual primeiro.', project_updates: {} };
}

export function applyValidatedAgentOutput(state, output, note = 'Agent') {
  const allowed = ['problem','audience','jtbd','unknowns','critical_hypothesis','opportunity_score','score_breakdown','current_gate','gate_status','next_action','solutions','opportunity_gate'];
  const safeUpdates = Object.fromEntries(Object.entries(output.project_updates || {}).filter(([key]) => allowed.includes(key)));
  return {
    ...state, ...safeUpdates,
    facts: [...(state.facts || []), ...(output.facts || [])],
    evidence: [...(state.evidence || []), ...(output.evidence || [])],
    assumptions: uniq([...(state.assumptions || []), ...(output.assumptions || [])]),
    unknowns: uniq([...(safeUpdates.unknowns || state.unknowns || []), ...(output.unknowns || [])]),
    risks: uniq([...(state.risks || []), ...(output.risks || [])]),
    decisions: [...(state.decisions || []), { id: crypto.randomUUID(), type: 'AGENT_ANALYSIS', source: note, recommendation: output.recommendation, created_at: new Date().toISOString() }],
    updated_at: new Date().toISOString()
  };
}
