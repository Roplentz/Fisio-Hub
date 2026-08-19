# Sprint 2 — Inteligência clínica e conteúdo responsável

## Objetivo

Adicionar uma barreira clínica auditável entre a geração do roteiro e a
produção audiovisual. O sistema aponta riscos; não declara que uma afirmação
é verdadeira apenas porque nenhum padrão foi detectado.

## Entregas

- análise de alegações absolutas;
- bloqueio de orientação medicamentosa ou individual insegura;
- identificação de sintomas de alerta;
- exigência de referência para números clínicos;
- referências estruturadas com estado de verificação;
- CTA responsável;
- disclaimers por contexto;
- relatório `clinical-safety-report.json`;
- revisão humana sempre obrigatória;
- testes de bloqueio, revisão e rastreabilidade.

## Estados

- `pass`: nenhum padrão automático encontrado; revisão humana permanece;
- `review`: conteúdo exige revisão ou confirmação das referências;
- `block`: conteúdo não deve seguir para publicação.

## Limite importante

O verificador é uma barreira de segurança editorial, não um dispositivo
médico, parecer clínico ou sistema autônomo de validação científica.

## Próxima evolução

- conectores para PubMed/Crossref;
- deduplicação por DOI/PMID;
- avaliação de aderência entre citação e alegação;
- tela de aprovação por afirmação;
- bloqueio do render final quando o relatório estiver em `block`.
