# Projeto de melhorias — RP ViralLab Studio

## Objetivo

Tornar o RP ViralLab Studio mais profissional, previsível e seguro para uso contínuo, preservando a velocidade de experimentação e mantendo o processamento local quando isso proteger dados e reduzir custos.

## Princípios de priorização

As melhorias são priorizadas por risco operacional, proteção de dados, confiabilidade do fluxo e qualidade da experiência. A primeira etapa deve estabilizar o núcleo antes de expandir recursos de IA ou publicação automática.

| Horizonte | Foco | Resultado esperado |
|---|---|---|
| Implementado nesta rodada | Bootstrap explícito, escrita atômica, limites de arquivos, testes e CI somente-leitura | O app deixa de executar código-fonte dinamicamente, reduz corrupção de arquivos, rejeita entradas excessivas e valida o fluxo sem auto-commit. |
| Próximos 7 dias | Jobs assíncronos, validação de mídia e concluir proteção de branches | Renderização mais resiliente e operação sem bloqueio da interface. |
| Próximos 30 dias | Jobs assíncronos, schemas versionados e política de dados | Renderização e análise não bloqueiam a interface; contratos são migráveis e auditáveis. |
| Próximos 90 dias | Autenticação, armazenamento de objetos, auditoria e release controlado | Base adequada para multiusuário, uso profissional e publicação confiável. |

## Entregas implementadas

### Bootstrap explícito

O `app.py` agora importa `app_v3` como módulo normal. O fluxo deixou de ler, substituir e executar o código-fonte em tempo de execução. O autoteste foi incorporado ao próprio Studio como etapa nativa, e a interface de voz deixou de depender do patch textual para iniciar.

O módulo de compatibilidade do patch foi mantido apenas para fixtures e integrações legadas, mas não é mais necessário no caminho principal da aplicação.

### Persistência mais segura

O índice de projetos, `project.json` e `video-package.json` passam a ser escritos em arquivo temporário e publicados por rename atômico. Isso reduz o risco de arquivos parcialmente gravados quando há interrupção do processo.

### Limites defensivos para backups

A importação de ZIP agora rejeita backups maiores que 250 MB, com mais de 5.000 arquivos ou com membro individual maior que 50 MB. A validação de caminho existente contra traversal foi preservada.

### Proteção de mídia

Uploads de vídeo são limitados a 250 MB e narrações a 100 MB. As gravações usam arquivo temporário antes da publicação definitiva, e o usuário recebe mensagens claras quando o limite é excedido.

### Regressão coberta por testes

Foram adicionados testes para o limite de membros e tamanho de ZIP, o limite de narração e o novo contrato do entrypoint. A suíte final executada apresentou 54 testes aprovados.

### CI/CD com menor privilégio

Foi preparada localmente uma revisão dos workflows para operar com `contents: read`, sem commit automático na branch principal, e para separar validação de promoção em ambiente `production`. Essas alterações não foram incluídas na branch pública desta PR porque o token atual não possui a permissão `workflows`; permanecem disponíveis na branch local `feature/professional-hardening` para publicação posterior com credencial autorizada.

## Próxima frente arquitetural

A principal frente arquitetural remanescente é separar tarefas longas do processo Streamlit. O aplicativo já inicia por imports normais e o autoteste já é uma etapa nativa, mas FFmpeg, Whisper, OpenCV e geração de ativos ainda devem executar em workers com estado persistido, limites de CPU/memória, cancelamento e limpeza.

O usuário deve ver progresso e resultado mesmo depois de atualizar a página.

A segunda frente é migrar metadados de projeto para banco transacional e mídia para armazenamento de objetos com URLs temporárias. Fotos de avatar, voz, vídeos, transcrições e conteúdos potencialmente clínicos devem possuir retenção, criptografia, autorização por projeto, consentimento e exclusão auditável.

## Critérios de aceite do produto profissional

| Área | Critério |
|---|---|
| Inicialização | O app inicia por imports normais e o smoke test executa o mesmo caminho da produção. |
| Projetos | Criar, salvar, importar, exportar e excluir projetos é transacional e auditável. |
| Mídia | Tamanho, duração, MIME e resolução são validados antes do processamento. |
| IA | Cada saída é validada por schema, com modelo, versão, latência e fallback registrados. |
| Privacidade | Foto, voz, vídeo e transcrição têm consentimento, retenção e exclusão verificáveis. |
| Operação | Análise e renderização são jobs observáveis, canceláveis e isolados da interface. |
| Publicação | Nenhum conteúdo é publicado sem revisão humana e aprovação explícita. |
| CI/CD | Branches protegidas, actions fixadas, checks obrigatórios e promoção sem force-push. |

## Validação executada

```text
python -m pytest -q
54 passed

python -m compileall -q app.py app_v3.py pages src tests
OK

git diff --check
OK
```

## Limitações desta rodada

Não foram implementadas autenticação multiusuário, banco de dados, fila de jobs, criptografia de mídia, revisão clínica automática ou publicação em redes sociais. Essas mudanças exigem decisões de produto, infraestrutura e governança de dados que não devem ser introduzidas de forma silenciosa em um patch local.
