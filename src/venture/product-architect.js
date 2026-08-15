const now = () => new Date().toISOString();

function feature(id, title, tier, problem, input, processing, output, acceptance) {
  return { id, title, tier, problem, input, processing, output, acceptance, states: { empty: 'Orientar o usuário sobre o primeiro passo.', loading: 'Mostrar progresso sem bloquear contexto.', error: 'Explicar a falha e permitir tentar novamente.', success: 'Confirmar resultado e indicar próxima ação.' } };
}

export function generateProductArchitecture(state) {
  const solution = state.selected_solution;
  if (!solution?.id) throw new Error('Selecione uma solução no Opportunity Lab antes de gerar a arquitetura do produto.');

  const valueProposition = state.value_proposition || `${solution.user} consegue ${solution.output.toLowerCase()} por meio de ${solution.name.toLowerCase()}.`;
  const journey = [
    { step: 1, name: 'Entrada', goal: 'Entender rapidamente a promessa do produto e iniciar a tarefa.', success: 'Usuário inicia o fluxo principal sem ajuda externa.' },
    { step: 2, name: 'Contexto', goal: `Coletar ${solution.input.toLowerCase()}.`, success: 'Dados mínimos válidos para executar a tarefa.' },
    { step: 3, name: 'Processamento', goal: solution.processing, success: 'Sistema processa sem exigir etapas desnecessárias.' },
    { step: 4, name: 'Resultado', goal: solution.output, success: 'Usuário recebe o valor prometido de forma compreensível.' },
    { step: 5, name: 'Próxima ação', goal: 'Permitir salvar, repetir, compartilhar ou agir sobre o resultado.', success: 'Usuário sabe claramente o que fazer depois.' }
  ];

  const screens = [
    { id: 'home', name: 'Início', purpose: 'Explicar a proposta de valor e iniciar o fluxo.' },
    { id: 'input', name: 'Entrada de dados', purpose: `Capturar ${solution.input.toLowerCase()}.` },
    { id: 'result', name: 'Resultado', purpose: `Entregar ${solution.output.toLowerCase()}.` },
    { id: 'history', name: 'Histórico', purpose: 'Recuperar resultados e reduzir retrabalho.' }
  ];

  const features = [
    feature('f1', 'Iniciar tarefa principal', 'MUST', 'O usuário precisa entrar no fluxo sem ambiguidade.', 'Ação inicial', 'Abrir o fluxo principal', 'Tarefa iniciada', 'Ao acionar o CTA principal, o usuário chega ao input correto em um passo.'),
    feature('f2', 'Coletar dados essenciais', 'MUST', 'Sem contexto mínimo o produto não consegue entregar valor.', solution.input, 'Validar apenas campos essenciais', 'Dados válidos', 'Campos obrigatórios impedem envio vazio e erros são explicados no próprio formulário.'),
    feature('f3', 'Executar mecanismo principal', 'MUST', 'O produto precisa resolver a tarefa central de ponta a ponta.', solution.input, solution.processing, solution.output, 'Com input válido, o sistema produz resultado verificável e não exibe botão ou função falsa.'),
    feature('f4', 'Apresentar resultado acionável', 'MUST', 'Resultado sem clareza não produz progresso.', 'Resultado processado', 'Estruturar e priorizar informação', solution.output, 'O usuário identifica conclusão e próxima ação em até uma tela.'),
    feature('f5', 'Histórico mínimo', 'SHOULD', 'Usuários recorrentes podem precisar recuperar resultados.', 'Resultados anteriores', 'Persistir e listar', 'Histórico consultável', 'Usuário encontra ao menos os resultados recentes sem refazer a tarefa.'),
    feature('f6', 'Compartilhamento/exportação', 'SHOULD', 'Alguns resultados precisam circular fora do produto.', 'Resultado final', 'Gerar representação compartilhável', 'Arquivo/link/resumo', 'Compartilhamento preserva conteúdo essencial do resultado.'),
    feature('f7', 'Personalizações avançadas', 'LATER', 'Customização pode aumentar valor, mas não prova o mecanismo principal.', 'Preferências', 'Aplicar configurações', 'Experiência personalizada', 'Somente implementar após evidência de uso recorrente.'),
    feature('f8', 'Automação e integrações adicionais', 'LATER', 'Integrações aumentam complexidade antes de provar valor.', 'Dados externos', 'Integração', 'Fluxos automatizados', 'Somente implementar quando remover trabalho real comprovado.' )
  ];

  const must = features.filter(item => item.tier === 'MUST');
  const should = features.filter(item => item.tier === 'SHOULD');
  const later = features.filter(item => item.tier === 'LATER');
  const mvp = {
    promise: valueProposition,
    core_flow: ['Início', 'Entrada de dados', 'Processamento', 'Resultado', 'Próxima ação'],
    must: must.map(item => item.title),
    should: should.map(item => item.title),
    later: later.map(item => item.title),
    killer_question: 'Se retirarmos esta funcionalidade, o usuário ainda recebe o valor principal?',
    complete: must.length >= 4
  };

  const requirements = must.map((item, index) => ({ id: `RF-${index + 1}`, requirement: item.title, acceptance: item.acceptance, dependency: index === 0 ? 'Nenhuma' : `RF-${index}` }));
  const prd = {
    title: `PRD — ${solution.name}`,
    vision: `Entregar ${solution.output.toLowerCase()} para ${solution.user} com o menor fluxo viável.`,
    problem: state.problem?.statement || '',
    audience: state.audience?.primary || solution.user,
    jtbd: state.jtbd || solution.jtbd,
    value_proposition: valueProposition,
    functional_requirements: requirements,
    non_functional_requirements: ['Responsividade', 'Acessibilidade básica', 'Persistência segura quando aplicável', 'Feedback claro de loading/erro/sucesso'],
    business_rules: ['Não criar função sem comportamento real.', 'Coletar apenas dados necessários ao resultado.', 'Permitir recuperação de erro sem perder todo o contexto.', 'Registrar mudanças importantes do Project State.'],
    dependencies: ['Project State persistente', 'Mecanismo principal da solução selecionada'],
    implementation_order: requirements.map(item => item.id),
    risks: [state.critical_hypothesis || 'Hipótese crítica ainda não definida', 'Escopo crescer antes da validação do fluxo principal']
  };

  const gateCriteria = {
    selected_solution: true,
    value_proposition: Boolean(valueProposition),
    end_to_end_journey: journey.length >= 5,
    must_features: must.length >= 4,
    acceptance_criteria: requirements.every(item => Boolean(item.acceptance)),
    mvp_core_flow: mvp.complete
  };
  const passed = Object.values(gateCriteria).every(Boolean);

  return {
    ...state,
    value_proposition: valueProposition,
    product_architecture: { journey, screens, features, generated_at: now() },
    mvp,
    prd,
    product_gate: passed ? 'ADVANCE' : 'INVESTIGATE',
    current_gate: 'MVP_GATE',
    current_phase: Math.max(state.current_phase || 0, 6),
    next_action: passed ? 'MVP definido. Revise o PRD e avance para o Critic Agent antes de construir.' : 'Revise as lacunas do fluxo principal antes de construir.',
    decisions: [...(state.decisions || []), { id: crypto.randomUUID(), type: 'PRODUCT_ARCHITECTURE_GENERATED', source: 'Product Architect', gate: passed ? 'ADVANCE' : 'INVESTIGATE', created_at: now() }],
    updated_at: now()
  };
}
