# Guia de Uso — Painel Administrativo

Este guia explica como usar o painel administrativo do site da Igreja de Cristo em Jucurutu. Ele foi pensado pra quem está usando o sistema pela primeira vez, então segue a ordem natural de uso: primeiro acesso como administrador root, criação de outros administradores, e depois o dia a dia de publicar conteúdo no site.

O acesso ao painel é feito em `/auth/login`, a partir do endereço `https://igrejadecristojucurutu.com.br`.

---

## 1. Primeiro acesso (administrador root)

O administrador **root** é o que tem acesso total ao sistema — é ele quem cria e gerencia os outros administradores.

1. Acesse `/auth/login` e entre com o e-mail e a senha do administrador root.
2. Como é o primeiro login, o sistema vai pedir a configuração da **autenticação em duas etapas (2FA)** — veja a seção abaixo.
3. Depois de confirmar o 2FA, você cai direto no painel principal (`/admin/`), que mostra um resumo: quantos administradores estão ativos, quantos existem no total, e quantos acessaram o sistema hoje.

> Por segurança, a tela de login aceita no máximo 5 tentativas por minuto. Se errar demais, espere um pouco antes de tentar de novo.

---

## 2. Configurando a autenticação em duas etapas (2FA)

Isso só acontece uma vez, no primeiro login de cada administrador (root ou editor):

1. Depois de digitar e-mail e senha corretamente, aparece um **QR code** na tela.
2. Abra um aplicativo autenticador no celular — recomendo o **Google Authenticator**, mas qualquer app compatível com TOTP funciona (Authy, Microsoft Authenticator, etc).
3. Escaneie o QR code com o app. Ele vai passar a gerar um código numérico de 6 dígitos, que muda a cada 30 segundos.
4. Volte pro navegador e digite o código que está aparecendo no app naquele momento.
5. Pronto — dali em diante, todo login vai pedir e-mail, senha, e o código atual do app.

**Importante:** guarde bem o celular/app onde o 2FA foi configurado. Se o administrador perder acesso ao aplicativo autenticador, só o root consegue resolver isso (trocando a senha dele — o que reseta o 2FA e obriga a escanear um novo QR code no próximo login).

---

## 3. Criando um administrador editor

Depois de logado como root, vá até a área de administradores no painel (menu correspondente a **Administradores**):

1. Clique em **cadastrar novo administrador**.
2. Preencha nome, e-mail e senha.
3. Marque se ele já entra **ativo** ou não (um administrador inativo não consegue fazer login).
4. Salve.

O novo administrador (editor) já pode fazer login normalmente com essas credenciais — e, no primeiro acesso dele, vai passar pelo mesmo processo de configuração do 2FA descrito acima.

### Gerenciando administradores já existentes

Ainda na área de administradores, o root pode:

- **Editar** nome, e-mail e status (ativo/inativo) de qualquer administrador.
- **Trocar a senha** de qualquer administrador — útil se alguém esquecer a senha ou perder o acesso ao 2FA. Ao trocar a senha, o 2FA daquele administrador é reiniciado: no próximo login, ele vai ter que escanear um novo QR code.
- **Excluir** um administrador — essa ação pede a senha do próprio root como confirmação, exatamente pra evitar exclusões acidentais.

> O root não consegue excluir a própria conta por essa tela — isso é proposital, pra evitar que o sistema fique sem nenhum administrador root.

---

## 4. Publicando conteúdo no site

Depois que os administradores estão criados, o uso do dia a dia é gerenciar o conteúdo. Cada tipo de conteúdo tem sua própria tela de listagem, cadastro, edição e exclusão no painel:

### Estudos bíblicos (pregações)
Cadastre título, categoria, referência bíblica e o texto completo — o campo de texto usa um editor rico (Quill), então dá pra formatar negrito, listas, links etc. igual num editor de texto normal.

### Agenda semanal
Cadastre os encontros fixos da igreja (culto de oração, culto de doutrina, PG jovem, culto de domingo etc.), com dia da semana e horário. Dá pra ativar ou desativar um item da agenda sem precisar excluir — útil se um encontro for pausado temporariamente.

### Devocionais
Cadastre o devocional do dia, com data, título, texto e referência bíblica. Dá pra editar ou excluir devocionais já publicados.

### Pregações em vídeo
Basta colar o link do vídeo no YouTube — o sistema busca automaticamente o título, a duração e a miniatura do vídeo, sem precisar preencher isso manualmente.

### História da igreja
Área para textos institucionais e fotos sobre a trajetória da igreja.

### Ministérios / Departamentos
Cadastre os ministérios (jovens, homens, mulheres, infantil etc.), cada um com nome, descrição e status ativo/inativo. A ordem de exibição no site pode ser reorganizada diretamente arrastando os itens na lista.

### Eventos
Cadastre eventos com data, horário, local e imagem — eles aparecem automaticamente na seção de eventos do site.

### Redes sociais
Gerencie os links para Instagram, YouTube e demais redes exibidos no rodapé do site.

### Pedidos de oração
Os pedidos enviados pelos visitantes do site (de forma identificada ou anônima) chegam nessa área para a equipe pastoral acompanhar. Esse é o único formulário público do site — por isso todo o texto digitado ali passa por uma limpeza automática antes de ser salvo, prevenindo que alguém tente inserir código malicioso através dele.

---

## 5. Histórico de ações (somente root)

Existe uma tela exclusiva para o administrador root, com o histórico completo de tudo que já foi feito no painel: quem criou, editou ou excluiu algo, quando, e o que exatamente mudou (valores antes e depois). Dá pra filtrar por período, por tipo de ação (criação, edição, exclusão, login, logout) e por administrador.

Isso serve tanto para acompanhar o trabalho da equipe quanto para investigar qualquer coisa fora do comum. Por segurança, senhas e chaves de autenticação nunca aparecem nesse histórico, nem de forma criptografada.

---

## 6. Variáveis de ambiente (arquivo `.env`)

O sistema depende de um arquivo `.env` na raiz do projeto, que **não vai para o repositório** (deve estar no `.gitignore`) — é ele quem guarda as chaves e credenciais sensíveis fora do código-fonte. Ao configurar o projeto num servidor novo, crie esse arquivo com pelo menos os itens abaixo:

| Variável | Para que serve | Como gerar/obter |
|---|---|---|
| `chave_teste_base64` | Chave de criptografia (Fernet) usada para cifrar a chave secreta do 2FA de cada administrador antes de salvar no banco | Gere com Python: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `YOUTUBE_API_KEY` | Chave da API do YouTube, usada para buscar automaticamente título, duração e miniatura ao cadastrar uma pregação em vídeo | Criada no [Google Cloud Console](https://console.cloud.google.com/), ativando a "YouTube Data API v3" e gerando uma chave de API |
| `senha_do_app` | Chave secreta do Flask (`SECRET_KEY`) — assina a sessão e o cookie de login. Se não for definida, o sistema gera uma aleatória a cada reinício, o que derruba a sessão de todo mundo logado | Gere com Python: `python -c "import secrets; print(secrets.token_hex(64))"` |
| `FLASK_ENV` | Define se o sistema está em modo produção ou desenvolvimento — muda regras de cookie, HTTPS obrigatório e política de segurança (Talisman/CSP) | Use `production` no servidor real; deixe em branco ou `development` na sua máquina local |
| `MAIL_USERNAME` | E-mail do Gmail usado para o sistema enviar mensagens | O endereço de Gmail que vai funcionar como remetente |
| `MAIL_PASSWORD` | Senha usada para o envio pelo Gmail — **não é a senha normal da conta**, precisa ser uma "senha de app" | Gere em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), com a verificação em duas etapas do Gmail ativada |
| `email_root` | E-mail do administrador root criado automaticamente na primeira vez que o sistema sobe (só se ainda não existir nenhum root no banco) | Escolha o e-mail que você vai usar pra logar como root |
| `senha_root` | Senha do administrador root criado automaticamente nessa mesma primeira inicialização | Escolha uma senha forte — dá pra trocar depois pelo próprio painel, uma vez logado |

> Renomear `chave_teste_base64` para algo como `FERNET_SECRET_KEY`, e `senha_do_app` para `SECRET_KEY`, é recomendável antes de ir para produção — os nomes atuais não deixam claro o que cada chave protege de fato (a primeira nada tem de "teste": é ela que cifra os segredos do 2FA).

O banco de dados, nesse projeto, é **SQLite** (`church.db`), com o caminho definido direto no código — então não existe uma variável tipo `DATABASE_URL` a configurar; o arquivo do banco é criado sozinho na primeira execução, dentro da pasta do projeto.

**Atenção com `email_root`/`senha_root`:** essas duas só têm efeito na primeira vez que o sistema roda (quando ainda não existe nenhum administrador root no banco). Depois que o root já foi criado, elas ficam sem efeito — pode até removê-las do `.env` depois disso, já que a senha real passa a ser a que está salva (como hash) no banco.

Nunca compartilhe o `.env` real (com os valores preenchidos) por e-mail, WhatsApp ou repositório público — apenas o modelo (`.env.example`) sem os valores, como referência de quais variáveis existem.

---

## 7. Boas práticas

- Nunca compartilhe sua senha ou o código do 2FA com outra pessoa — cada administrador deve ter seu próprio login.
- Se um administrador sair da equipe, desative (ou exclua) o acesso dele o quanto antes.
- Prefira desativar um administrador a excluí-lo, caso ache que ele pode voltar a colaborar — assim o histórico de ações dele continua preservado.
- Sempre acesse o painel pelo endereço com `https://` — a comunicação já é criptografada por padrão, então evite salvar a senha em computadores compartilhados.
