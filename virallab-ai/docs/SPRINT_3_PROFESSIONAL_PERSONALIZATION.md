# Sprint 3 — Personalização profissional

## Objetivo

Permitir que cada profissional produza conteúdo coerente com sua identidade,
usando apenas materiais autorizados e sem aplicar rosto, logo ou mídia em
cenas indevidas.

## Entregas

- kit de marca persistente e versionado;
- cores, fontes, tom e diretrizes visuais;
- logotipo validado e removível;
- biblioteca privada de fotos, vídeos e áudios próprios;
- consentimento obrigatório e SHA-256 por arquivo;
- exclusão individual da mídia e atualização do manifesto;
- dicionário de pronúncia para termos clínicos em português;
- separação entre roteiro exibido e texto enviado ao TTS;
- testes de persistência, consentimento, validação e exclusão.

## Integração com recursos existentes

O Sprint 3 complementa, sem duplicar:

- `AvatarMasterStore`: três fotos e Imagem Mestre;
- `AuthorProfileStore`: referência visual legada;
- `AssetLibrary`: candidatos e aprovação por cena;
- `VoicePlan`: narração e alinhamento;
- `MediaProvider`: mídia local e Pexels.

## Regras de aplicação

- rosto e referências pessoais apenas em cenas `avatar`;
- logo somente em composição final ou capa aprovada;
- mídia própria exige declaração de autorização;
- pronúncia altera apenas a cópia de síntese de voz;
- exclusão deve remover arquivo e registro correspondente;
- nenhuma personalização elimina a revisão humana.
