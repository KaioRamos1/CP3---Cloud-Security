# Contrato da API

Base local: `http://127.0.0.1:3001`. Base publicada: `https://SEU_FQDN`, após implantação. A autenticação do ambiente publicado usa HTTP Basic no Nginx, exclusivamente por HTTPS. Todos os recursos do site são protegidos pelo proxy.

Em POST e PUT, envie `Content-Type: application/json`. Em POST, PUT e DELETE, envie `X-Requested-With: MinhaFrota`. Esse cabeçalho protege contra requisições de escrita feitas por páginas de outra origem no navegador; não é senha nem autenticação. A aplicação não habilita CORS.

| Método | Caminho | Resultado |
|---|---|---|
| GET | `/api/health` | Saúde da API e acesso ao banco |
| GET / POST | `/api/vehicles` | Lista ou cadastra veículos |
| GET / PUT / DELETE | `/api/vehicles/{id}` | Consulta, atualiza campos ou exclui veículo |
| GET / POST | `/api/records` | Lista ou cadastra registros de custos e serviços |
| GET / PUT / DELETE | `/api/records/{id}` | Consulta, atualiza campos ou exclui registro |
| GET | `/api/dashboard` | Veículos ativos, custos do mês e até 10 pendências |
| GET | `/api/reports/costs` | Soma de valores por tipo e categoria, sem filtro de período |

Filtros: `GET /api/vehicles?type=moto` e `GET /api/records?vehicle_id=1`. Exclusão: acrescente `?confirm=true`; excluir um veículo também exclui seus registros por `ON DELETE CASCADE`. PUT faz atualização parcial neste projeto; em APIs maiores, PATCH seria uma escolha mais expressiva para essa semântica.

## Exemplos no PowerShell local

```powershell
$base = 'http://127.0.0.1:3001'
$headers = @{ 'X-Requested-With' = 'MinhaFrota' }
$body = @{
    type='carro'; brand='Fiat'; model='Argo'
    year=2024; plate='TST1A23'; odometer_km=12000
} | ConvertTo-Json
$novo = Invoke-RestMethod -Uri "$base/api/vehicles" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
$id = $novo.data.id
Invoke-RestMethod -Uri "$base/api/vehicles/$id"
Invoke-RestMethod -Uri "$base/api/vehicles/$id" -Method Put -Headers $headers -ContentType 'application/json' -Body '{"odometer_km":12500}'
Invoke-RestMethod -Uri "$base/api/vehicles/${id}?confirm=true" -Method Delete -Headers $headers
```

O POST retorna 201 e o ID criado. O PUT retorna 200. O DELETE bem-sucedido retorna 204 sem conteúdo. Para testar o ambiente HTTPS, use `curl.exe -u avaliador` e informe a senha interativamente, ou configure Basic Auth no Postman. Não cole a senha em scripts versionados.

## Cadastro de um custo

```json
{
  "vehicle_id": 1,
  "kind": "manutencao",
  "category": "Revisao",
  "description": "Troca de oleo",
  "due_date": "2026-11-10",
  "amount": 250,
  "status": "pendente"
}
```

Envie esse objeto para `POST /api/records` usando o ID real do veículo. `kind` aceita manutencao, pagamento, seguro, documento, abastecimento ou despesa. `status` aceita pendente, pago, atrasado, concluido ou ativo. Datas usam AAAA-MM-DD; valores devem ser finitos e não negativos.

## Validação e respostas

Veículos exigem type, brand, model, year e plate. Placas são normalizadas para maiúsculas sem hífen. O ano deve estar entre 1886 e o ano atual mais dois. O status do veículo aceita ativo, vendido ou inativo. Campos não reconhecidos, objetos em campos de texto, números negativos e datas impossíveis são rejeitados. O JSON é limitado a 64 KiB.

| Código | Significado |
|---|---|
| 200 / 201 / 204 | Consulta ou atualização / criação / exclusão |
| 400 | JSON, dados, campos ou filtros inválidos |
| 401 | Credencial ausente ou inválida no Nginx |
| 403 | Cabeçalho exigido para escrita ausente ou incorreto |
| 404 / 405 | Recurso inexistente / método incompatível |
| 409 | Placa duplicada, relação inválida ou confirmação de exclusão ausente |
| 413 / 415 | Corpo muito grande / tipo de conteúdo diferente de JSON |
| 429 | Limite de requisições do Nginx atingido |
| 500 | Falha interna sem exposição de detalhes técnicos |

Sucesso usa `{"data": ...}`, exceto health e 204. Erro da API usa `{"error":{"code":"...","message":"..."}}`. Erros gerados pelo Nginx, como 401 e 429, podem retornar HTML. Ausência de credencial não pode ser testada no servidor local: a camada de autenticação fica no proxy da implantação.

## Banco de dados

`vehicles` armazena identidade do veículo, placa única, quilometragem, status e timestamps. `records` referencia `vehicles.id`, registra categoria, descrição, datas, status e valor. A relação é **um veículo para muitos registros**. `app_meta` registra a inicialização para que as demonstrações não reapareçam depois de excluídas.

Chaves estrangeiras são habilitadas em cada conexão; valores SQL são parametrizados. As colunas usadas nas operações dinâmicas vêm de uma lista fixa. O banco usa WAL e timeout de espera por lock de cinco segundos. SQLite permite concorrência limitada de escrita; o projeto é dimensionado para um laboratório pequeno, sem múltiplas VMs compartilhando o mesmo arquivo.

Os valores monetários seguem o modelo didático original em REAL. Para um sistema financeiro, prefira centavos inteiros ou uma política decimal explícita. O esquema completo está em `schema.sql`.
