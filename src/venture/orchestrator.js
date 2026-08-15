const clean = (text = '') => text.replace(/\s+/g, ' ').trim();
const sentence = (text = '') => clean(text).split(/[.!?]/).filter(Boolean)[0] || '';

const inferAudience = (text) => {
  const t = text.toLowerCase();
  const candidates = [
    ['pacient', 'Pacientes'],
    ['alun', 'Estudantes'],
    ['fisioterapeut', 'Fisioterapeutas'],
    ['professor', 'Professores'],
    ['idos', 'Pessoas idosas'],
    ['surdo', 'Pessoas surdas sinalizantes'],
    ['dentist', 'Dentistas'],
    ['gestor', 'Gestores'],
  ];
  return candidates.find(([key]) => t.includes(key))?.[1] || 'Público ainda não definido';
};

const buildProblem = (text) => {
  const first = sentence(text);
  if (!first) return 'Problema ainda não descrito';
  return first.length > 180 ? `${first.slice(0, 177)}...` : first;
};

const scoreDiscovery = ({ problem, audience, evidence, assumptions }) => {
  let score = 0;
  if (problem?.statement && problem.statement !== 'Problema ainda não descrito') score += 8;
  if (audience?.primary && audience.primary !== 'Público ainda não definido') score += 5;
  if ((evidence || []).length) score += 4;
  if ((assumptions || []).length <= 3) score += 3;
  return Math.min(20, score);
};

export function runDiscoveryAgent(input, currentState) {
  const text = clean(input);
  const audience = inferAudience(text);
  const problem = buildProblem(text);
  const facts = text ? [{ label: 'Relato inicial', value: text, source: 'user' }] : [];
  const assumptions = [];

  if (audience === 'Público ainda não definido') {
    assumptions.push('O público que mais sofre com o problema ainda precisa ser identificado.');
  }
  assumptions.push('A frequência e a intensidade do problema ainda precisam ser verificadas com usuários reais.');
  assumptions.push('As soluções atuais podem ser insuficientes, mas isso ainda não foi demonstrado por evidências.');

  const risks = [
    'Construir uma solução antes de confirmar frequência, consequência e contexto do problema.',
  ];
  if (audience === 'Público ainda não definido') risks.push('Público excessivamente amplo ou indefinido.');

  const evidence = currentState.evidence || [];
  const problemData = {
    statement: problem,
    context: text,
    consequences: currentState.problem?.consequences || 'Ainda não verificadas',
    frequency: currentState.problem?.frequency || 'Ainda não verificada',
    severity: currentState.problem?.severity || 'Ainda não verificada',
  };
  const audienceData = { ...currentState.audience, primary: audience };
  const score = scoreDiscovery({ problem: problemData, audience: audienceData, evidence, assumptions });
  const recommendation = evidence.length >= 2 && audience !== 'Público ainda não definido' ? 'AVANÇAR' : 'INVESTIGAR';

  return {
    analysis: 'O relato foi convertido em um estado inicial de discovery. Os itens sem evidência permanecem explicitamente classificados como hipóteses.',
    facts,
    evidence,
    assumptions,
    risks,
    recommendation,
    next_action: recommendation === 'AVANÇAR'
      ? 'Revisar a formulação do problema e preparar o Opportunity Gate.'
      : 'Validar o problema com usuários reais: confirme quem sofre, quando ocorre, frequência e consequência.',
    project_updates: {
      source_text: text,
      problem: problemData,
      audience: audienceData,
      jtbd: `Quando enfrento ${problem.toLowerCase()}, quero uma forma melhor de lidar com isso, para alcançar o resultado necessário com menos fricção.`,
      facts,
      assumptions,
      risks,
      opportunity_score: score,
      gate_recommendation: recommendation,
      current_gate: 'PROBLEM_GATE',
    },
  };
}

export function orchestrate({ action = 'DISCOVERY', input, state }) {
  if (action === 'DISCOVERY') return runDiscoveryAgent(input, state);
  throw new Error(`Ação do Orchestrator ainda não implementada: ${action}`);
}
