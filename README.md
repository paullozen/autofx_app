# AutoFX App - YouTube Content Pipeline

## 🚀 Como Executar

### Pré-requisitos
- Node.js 18+
- Python 3.x

### Instalação

1. Instale as dependências Node.js:
```bash
npm install
```

2. Crie o ambiente virtual Python e instale as dependências:
```bash
python3 -m venv venv
./venv/bin/pip install -r backend/requirements.txt
./venv/bin/playwright install chromium
```

### Executar a Aplicação

Você precisa executar **dois servidores** simultaneamente:

#### Terminal 1 - Frontend (React + Vite)
```bash
npm run dev
```
Acesse: http://localhost:5173

#### Terminal 2 - Backend (Node.js + Python)
```bash
npm run server
```
Servidor rodando em: http://localhost:3001

## 📋 Funcionalidades

### Mapeamento Menu → Scripts Python

| Menu Lateral | Script Python |
|--------------|---------------|
| Create Profile | `profile_generator.py` |
| Channel Info | `channel_info.py` |
| Clean Base | `clean_bases.py` |
| Get Scripts | `get_scripts.py` |
| SRT Generator | `srt_generator.py` |
| Image Suggestions | `suggestion_generator.py` |
| Image Generator | `image_generator.py` |
| Image Render | `make_and_render.py` |

### Create Profile
1. Clique em **"Create Profile"** na barra lateral
2. Digite o nome do novo perfil
3. Clique em **"Create Profile"**
4. O script Python será executado e o output aparecerá no **Execution Log**
5. O perfil criado aparecerá na lista **"Existing Profiles"**
6. Para deletar um perfil, clique no ícone de lixeira ao lado do nome

### Terminal Interativo
- **Campo de Input Verde**: Digite inputs quando o script Python solicitar
- Pressione **Enter** ou clique no ícone de envio
- O campo aceita entrada vazia (apenas Enter) para scripts que permitem

### Execution Log
- Mostra todos os outputs dos scripts Python em tempo real
- Auto-scroll para o final quando novos logs aparecem
- Ocupa 50% da altura da tela
- Botão **Clear** para limpar o log

## 🔧 Como Funciona

1. **Frontend (React)**: Interface do usuário
2. **Backend (Node.js)**: Servidor que executa scripts Python
3. **Scripts Python**: Processam as tarefas do pipeline

### Fluxo de Execução

1. Usuário clica em um stage (ex: "Create Profile")
2. Frontend envia requisição para `http://localhost:3001/execute`
3. Servidor Node.js executa o script Python correspondente usando o Python do venv
4. Input é enviado para o script Python via stdin
5. Output do Python é capturado linha por linha
6. Logs são exibidos no **Execution Log** em tempo real

### Input Interativo

Quando um script Python pede input:
1. Digite no campo verde acima do terminal
2. Pressione Enter
3. O input é enviado via `/send-input` endpoint
4. O script continua a execução

## 🎨 Temas

- **Dark Mode** (padrão)
- **Light Mode**

Use o botão de tema na barra lateral para alternar.

## 📁 Estrutura de Pastas

```
autofx_app/
├── backend/
│   ├── profile_generator.py
│   ├── channel_info.py
│   ├── clean_bases.py
│   ├── get_scripts.py
│   ├── srt_generator.py
│   ├── suggestion_generator.py
│   ├── image_generator.py
│   ├── make_and_render.py
│   ├── profiles.py
│   ├── requirements.txt
│   ├── chrome_profiles/        # Perfis criados
│   └── support_scripts/        # Scripts auxiliares
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx
│   │   ├── MainPanel.jsx
│   │   ├── ExecutionLog.jsx
│   │   └── Layout.jsx
│   └── App.jsx
├── server.js                   # Servidor backend
└── venv/                       # Ambiente virtual Python
```

## 🔐 Configuração

Alguns scripts precisam de variáveis de ambiente. Crie um arquivo `.env` na raiz do projeto (ou copie o exemplo):

```bash
cp .env.example .env   # copie e preencha os valores
```

```env
# YouTube API
YT_API_KEY=sua_chave_aqui

# Notion API
NOTION_TOKEN=seu_token_aqui
NOTION_DATABASE_ID=id_do_database
NOTION_DATA_SOURCE_ID=id_da_fonte
```


## 🐛 Troubleshooting

### Erro ao executar scripts Python
- Verifique se o venv está ativado
- Confirme que todas as dependências foram instaladas: `./venv/bin/pip list`

### Servidor backend não inicia
- Verifique se a porta 3001 está livre
- Reinicie o servidor: `npm run server`

### Scripts não aparecem no log
- Verifique o console do navegador (F12)
- Confirme que o backend está rodando
- Teste a conexão: `curl http://localhost:3001`
