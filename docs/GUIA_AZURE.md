# Guia de execução no Windows e implantação no Azure

Siga a ordem. Os valores `SEU_USUARIO`, `SEU_IP`, `SEU_FQDN` e `SEU_EMAIL` são campos para substituir. Os recursos Azure podem gerar cobrança; confira a estimativa da sua assinatura antes de criar a VM.

## 1 Executar e entender localmente

Abra o PowerShell na pasta do projeto. Confirme Python e Git:

```powershell
python --version
git --version
python -m unittest -v test_api.py
python app.py --seed
```

Abra `http://127.0.0.1:3001`. Cadastre, edite e exclua um veículo de teste. Use `Ctrl+C` para encerrar o servidor. Este servidor de desenvolvimento fica em loopback e não é o servidor público da implantação.

## 2 Criar o repositório no GitHub

No GitHub: **New repository** → nome `minha-frota-cloud` → visibilidade conforme a orientação do professor. Para o roteiro abaixo, use um repositório público com dados demonstrativos. Crie-o vazio, sem README, gitignore ou licença automáticos: esses arquivos já estão no projeto.

Dentro da pasta do projeto no PowerShell:

```powershell
git init
git branch -M main
git config user.name "SEU NOME"
git config user.email "SEU_EMAIL_DO_GITHUB"
git add .
git status
git diff --cached --stat
git commit -m "Implementa API SQLite e configuracao Azure"
git remote add origin https://github.com/SEU_USUARIO/minha-frota-cloud.git
git push -u origin main
```

Antes do commit, confira que não foram incluídos banco, backups, chaves SSH, senhas, arquivos `.env` ou dados pessoais. Faça a autenticação pelo fluxo do Git Credential Manager; não coloque token no comando ou no README. Se o Git já estiver configurado, reutilize sua identidade.

Na aba **Actions**, abra `Testes e seguranca`. Só implante o commit depois dos checks aprovados. Se `pip-audit` sinalizar uma dependência, revise o aviso, atualize a versão e execute novamente; não transforme a falha em sucesso artificial. O workflow é CI com implantação manual posterior, não CD automático.

## 3 Criar uma VM dedicada ao laboratório

No [portal Azure](https://portal.azure.com), abra **Virtual machines → Create → Azure virtual machine**. Registre os valores reais usados:

| Campo | Configuração sugerida |
|---|---|
| Resource group | `rg-minhafrota-lab` |
| Nome | `vm-minhafrota` |
| Região | Uma permitida pela assinatura; exemplo `Brazil South` |
| Imagem | Ubuntu Server 24.04 LTS, x64, Gen2 |
| Segurança | Trusted launch se disponível e compatível com o tamanho |
| Size ou SKU | `Standard_B2ts_v2`: 2 vCPU, 1 GiB RAM, CPU por créditos |
| Alternativa de memória | `Standard_B2ls_v2`: 2 vCPU, 4 GiB RAM, se o orçamento permitir |
| Administrador | `azureuser` |
| Autenticação SSH | Chave pública; gere o par pelo portal e guarde a chave privada |
| Disco do SO | Gerenciado Standard SSD LRS; use o mínimo permitido pela imagem e anote a capacidade real |
| IP público | Standard, estático |

A disponibilidade do SKU varia por região, assinatura e quota. Se o tamanho não estiver disponível, escolha um equivalente permitido e atualize o relatório com o SKU real. Não selecione uma VM maior sem revisar a estimativa. B1s não é o padrão deste roteiro porque a documentação consultada classifica a família Bv1 em fim de vida.

Em **Disks**, não use disco efêmero para o SO. O SQLite ficará em `/var/lib/minhafrota/minha_frota.sqlite3`, no disco persistente da VM. Um disco de dados separado é uma evolução possível, mas não faz parte deste roteiro. Discos gerenciados têm criptografia em repouso da plataforma por padrão; isso não substitui permissões no Linux nem backup.

## 4 Configurar rede e DNS

Em **Networking**, configure o NSG associado à interface ou à sub-rede. Regras de entrada:

| Prioridade de exemplo | Porta TCP | Origem | Finalidade |
|---|---|---|---|
| 100 | 22 | Seu IP público com `/32` | Administração SSH |
| 110 | 80 | Internet | Validação ACME e redirecionamento para HTTPS |
| 120 | 443 | Internet | Aplicação com autenticação |

Não crie uma regra liberando a porta 3001. Revise se uma regra anterior abriu SSH para qualquer origem; edite essa regra para o seu IP. Se seu IP mudar, atualize o NSG antes de tentar conectar. Mantenha a negação padrão das outras conexões de entrada.

Abra o recurso **Public IP address → Configuration → DNS name label** e escolha um rótulo disponível. Copie o **DNS name completo retornado pelo Azure**, sem construir o nome por suposição. Ele será o `SEU_FQDN` deste roteiro. Alternativamente, use um domínio seu com registro A para o IP da VM. Confirme a resolução:

```powershell
Resolve-DnsName SEU_FQDN
```

É necessário permitir saída da VM para DNS, repositórios Ubuntu/Python, GitHub e autoridade certificadora. O roteiro não cria regras restritivas de saída.

## 5 Conectar e instalar

No PowerShell, use o caminho verdadeiro da chave baixada e o IP público da VM:

```powershell
ssh -i "$env:USERPROFILE\Downloads\vm-minhafrota_key.pem" azureuser@SEU_IP
```

Confirme a impressão digital do host usando as informações confiáveis da VM quando disponíveis. Não envie a chave privada ao GitHub.

A partir daqui, os comandos são **Bash dentro do Ubuntu**, não PowerShell:

```bash
sudo apt-get update
sudo apt-get install -y git curl
git clone https://github.com/SEU_USUARIO/minha-frota-cloud.git
cd minha-frota-cloud
git rev-parse HEAD
sudo bash deploy/install.sh SEU_FQDN SEU_EMAIL
```

O script instala Python/venv, Gunicorn, Nginx e Certbot; cria o usuário de serviço sem shell; inicializa o SQLite; configura o systemd; emite o certificado e solicita uma senha para `avaliador`. A execução aceita os termos da autoridade certificadora usados pelo Certbot. Não imprima a senha nem a inclua no relatório.

Durante o bootstrap, a porta 80 responde 503 para a aplicação e permite apenas o desafio ACME. A aplicação só é publicada depois de configurados TLS e autenticação. Se o certificado falhar, confira DNS, NSG, porta 80 e os logs do Certbot. Não troque HTTPS por HTTP para enviar a senha.

Se a VM só permitir repositório privado, use um método de autenticação Git autorizado sem gravar token no URL. O clone público acima não funciona para um repositório privado sem autenticação.

## 6 Validar a implantação

Na VM:

```bash
sudo systemctl status minhafrota --no-pager
sudo nginx -t
curl --fail http://127.0.0.1:3001/api/health
sudo ss -lntp
sudo journalctl -u minhafrota -n 30 --no-pager
sudo certbot renew --dry-run
git rev-parse HEAD
```

A API deve aparecer em `127.0.0.1:3001`, não em `0.0.0.0:3001`. Nginx atende as portas 80 e 443. O health local retorna `{"status":"ok","database":"ok"}`. Registre o hash do commit, a data e o resultado dos comandos.

No PowerShell do seu Windows, fora da sessão SSH:

```powershell
curl.exe -i https://SEU_FQDN/api/health
curl.exe -i -u avaliador https://SEU_FQDN/api/health
Test-NetConnection SEU_IP -Port 3001
```

O primeiro comando deve retornar **401**. O segundo pede a senha e deve retornar **200**. O teste da porta 3001 deve indicar `TcpTestSucceeded: False`; uma falha isolada não comprova toda a política do NSG, então registre também as regras e o listener local.

Abra `https://SEU_FQDN`, faça login e teste o CRUD. Não use `curl -k`: a validação do certificado é parte da evidência. Não tire prints da senha nem do cabeçalho Authorization.

## 7 Backup e recuperação

Execute na VM, a partir do clone do projeto:

```bash
sudo install -d -o minhafrota -g minhafrota -m 0750 /var/lib/minhafrota/backups
sudo -u minhafrota python3 deploy/backup.py \
  /var/lib/minhafrota/minha_frota.sqlite3 \
  /var/lib/minhafrota/backups/minhafrota-AAAAMMDD-HHMM.sqlite3
```

Troque o sufixo por data e hora reais. O script usa a API `sqlite3.backup`, verifica a integridade e não sobrescreve backups. Com WAL ativo, não copie apenas o arquivo `.sqlite3` de um banco em uso.

Para guardar uma cópia fora da VM, crie temporariamente uma cópia legível apenas pelo administrador:

```bash
sudo install -o azureuser -g azureuser -m 0600 \
  /var/lib/minhafrota/backups/minhafrota-AAAAMMDD-HHMM.sqlite3 \
  /home/azureuser/minhafrota-backup.sqlite3
```

No Windows, fora da sessão SSH:

```powershell
scp -i "$env:USERPROFILE\Downloads\vm-minhafrota_key.pem" azureuser@SEU_IP:/home/azureuser/minhafrota-backup.sqlite3 .\minhafrota-backup.sqlite3
```

Após conferir a cópia, remova somente o arquivo temporário em `/home/azureuser`. Não o adicione ao Git. Faça um teste de recuperação em uma pasta isolada local: copie o backup para `C:\Temp\MinhaFrotaRestore\minha_frota.sqlite3`, encerre outro servidor local na porta 3001 e execute:

```powershell
$env:MINHA_FROTA_DATA_DIR = 'C:\Temp\MinhaFrotaRestore'
python app.py
```

Confira os registros restaurados. Ao terminar, encerre com `Ctrl+C` e remova a variável da sessão com `Remove-Item Env:MINHA_FROTA_DATA_DIR`. Isso valida recuperação local sem sobrescrever o banco da VM. A cópia no mesmo disco não protege contra perda desse disco. Não há agendamento automático de backup neste projeto.

## 8 Atualizar e encerrar o laboratório

Antes de atualizar, faça backup e registre o hash atual. Publique alterações no GitHub, espere a CI e, na VM, execute `git pull --ff-only`, confira o novo hash e rode o instalador novamente com o mesmo FQDN. Revalide o health e o CRUD. O script preserva o banco e a senha existentes; não possui migrações automáticas de esquema.

Para reverter código, use um commit aprovado anterior e reinstale a aplicação, verificando a compatibilidade com o esquema. Não restaure um banco antigo sem avaliar a perda de dados mais recentes.

Após a avaliação, exporte as evidências e backups. Parar pelo sistema operacional não equivale necessariamente a desalocar pelo Azure. Mesmo desalocada, a VM pode continuar gerando cobrança por discos e IPs. Exclua o grupo de recursos somente se ele for exclusivo do laboratório, se a avaliação terminou e se você já preservou o que precisa.
