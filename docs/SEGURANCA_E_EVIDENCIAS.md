# Segurança e evidências

## Controles e limites

| Risco | Controle preparado | Como comprovar |
|---|---|---|
| Exposição direta da API | Gunicorn somente em 127.0.0.1:3001 e NSG sem entrada 3001 | Listener local e teste externo da porta |
| Interceptação de credenciais | HTTPS, TLS 1.2/1.3 e redirecionamento HTTP | Certificado válido e resposta 301 |
| Acesso sem credenciais | Basic Auth no Nginx com senha bcrypt | 401 sem login e 200 após autenticação |
| SQL injection | Valores parametrizados e lista permitida de colunas | Código e teste com texto de SQL |
| XSS armazenado | DOM com textContent e CSP sem script inline | Revisão do JavaScript e teste visual no navegador |
| CSRF | Header customizado obrigatório em escritas e ausência de CORS | 403 sem o header; preflight rejeitado |
| Requisição abusiva | 64 KiB por corpo e rate limit no proxy | 413 e 429 em teste controlado |
| Privilégios excessivos | Serviço sem root, código somente leitura, diretório de dados restrito | Unit systemd e permissões dos arquivos |
| Dependências vulneráveis | pip-audit e Dependabot | Execução aprovada na aba Actions |
| Regressão funcional | unittest e verificação WSGI | Saída dos testes e CI |
| Perda de dados | Backup consistente e recuperação em ambiente isolado | Integridade e leitura da cópia restaurada |

O aplicativo local não possui autenticação própria. Na implantação, o proxy protege todo o site. Não exponha a API por outro listener. A conta `avaliador` possui acesso completo ao CRUD e não representa autorização granular. Para uso real, implemente identidades individuais, RBAC, trilha de auditoria, monitoramento, política de retenção e backup fora da VM. Uma única VM não fornece alta disponibilidade. O rate limit não impede DDoS volumétrico.

O controle de XSS teve inspeção estática e teste de armazenamento de payload como dado; ainda é necessário verificar a renderização no navegador. A CSP é defesa adicional. Testes aprovados não são garantia de ausência de vulnerabilidades.

## O que foi executado nesta preparação

- 18 testes automatizados da API, com banco temporário, sem alterar a base do usuário.
- Validação do contrato WSGI nas chamadas de teste.
- Requisições HTTP locais para health, vehicles, dashboard e página HTML: todas retornaram 200.
- Verificação de sintaxe JavaScript e dos scripts Bash.
- Backup e integridade SQLite em teste isolado.

Não foram executados: implantação Azure, Gunicorn/Nginx, obtenção ou renovação real de certificado, GitHub Actions, Bandit, pip-audit ou validação visual em navegador. A instalação de dependências não estava disponível neste ambiente. Esses itens têm procedimentos de validação no guia e devem receber evidências reais antes da entrega final.

## Prints obrigatórios para completar a entrega

Use Win+Shift+S no Windows. Para cada print, inclua legenda com o que foi feito, resultado, ambiente e data. Oculte senhas, chaves, tokens, e-mails pessoais e identificadores de assinatura quando desnecessários.

| ID | Print | O que precisa aparecer |
|---|---|---|
| E01 | VM no Azure | Nome, região, SO, SKU, vCPU e RAM |
| E02 | Disco | Tipo gerenciado, capacidade real e criptografia |
| E03 | NSG | 22 restrita ao seu IP, 80/443 permitidas, sem liberação 3001 |
| E04 | Dashboard publicado | URL HTTPS, certificado válido e veículos demonstrativos |
| E05 | Criação via API | POST, JSON, resposta 201 e ID criado |
| E06 | Consulta e edição | GET/PUT com ID real e valor alterado |
| E07 | Exclusão | DELETE confirmado, 204 e posterior GET 404 |
| E08 | Autenticação | Resposta 401 sem login e 200 autenticado, sem exibir credenciais |
| E09 | Testes e CI | Tests, Bandit e pip-audit com status e commit |
| E10 | Persistência | Registro antes e depois de reiniciar o serviço na VM |
| E11 | Backup e recuperação | integrity_check=ok e dados recuperados em pasta isolada |
| E12 | GitHub | URL do repositório, README, arquivos e commit implantado |

Modelo de legenda: “Figura E05 — POST /api/vehicles executado em [URL] em [DATA]. A API retornou HTTP 201 com o ID [ID], confirmando o cadastro no SQLite.” Substitua os campos usando sua evidência, não uma resposta esperada.

Antes de entregar, preencha URL do GitHub, URL HTTPS, hash do commit, dados reais da VM e as legendas. A senha do professor deve ser comunicada em canal privado. Remova marcadores de pendência apenas quando houver comprovação.
