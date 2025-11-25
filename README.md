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

| Menu Lateral | Script Python | Descrição |
|--------------|---------------|-----------|
| **Create Profile** | `profile_generator.py` | Cria perfis do Chrome para automação |
| **API Key** | N/A | Gerenciamento seguro de chaves de API |
| **Script** | `get_scripts.py` | Baixa roteiros do Notion ou permite entrada manual |
| **SRT Generator** | `srt_generator.py` | Gera legendas sincronizadas |
| **Audio Generator** | `audio_generator.py` | Gera áudio usando GenAI Pro |
| **Audio Download** | `audio_downloader.py` | Baixa os áudios gerados |
| **Image Suggestions** | `suggestion_generator.py` | Gera prompts de imagem baseados no roteiro |
| **Image Generator** | `image_generator.py` | Gera imagens usando IA |
| **Image Render** | `make_and_render.py` | Renderiza o vídeo final |
| **Channel Info** | `channel_info.py` | Coleta informações do canal |
| **Clean Base** | `clean_bases.py` | Limpa arquivos temporários |

### ✨ Novas Funcionalidades

#### 🔑 Gerenciamento de API Keys
- Acesse a aba **API Key** no menu lateral.
- Interface segura para gerenciar chaves do OpenAI, GenAI Pro, YouTube e Notion.
- As chaves são salvas criptografadas/mascaradas na interface.
- Persistência automática no arquivo `backend/.env`.

#### 🖼️ Configuração de Sugestões de Imagem
- Na aba **Image Suggestions**, clique no botão **Config**.
- Edite diretamente os prompts usados para gerar sugestões de cenas e padrões de imagem.
- Salva automaticamente nos arquivos `prompts/Scene_Suggestion.txt` e `prompts/IMG_PATTERNS.txt`.

#### 📂 Acesso Rápido a Pastas
- Ícones de pasta no menu lateral permitem abrir diretamente o diretório de output correspondente a cada ferramenta.
- Facilita a verificação de arquivos gerados (áudios, imagens, vídeos).

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
2. **Backend (Node.js)**: Servidor que executa scripts Python e gerencia arquivos
3. **Scripts Python**: Processam as tarefas do pipeline

### Fluxo de Execução

1. Usuário clica em um stage (ex: "Create Profile")
2. Frontend envia requisição para `http://localhost:3001/execute`
3. Servidor Node.js executa o script Python correspondente usando o Python do venv
4. Input é enviado para o script Python via stdin
5. Output do Python é capturado linha por linha
6. Logs são exibidos no **Execution Log** em tempo real

## 🎨 Temas

- **Dark Mode** (padrão)
- **Light Mode**

Use o botão de tema na barra lateral para alternar.

## 📁 Estrutura de Pastas

```
autofx_app/
├── backend/
│   ├── .env                    # Arquivo de variáveis de ambiente (Gerado automaticamente)
│   ├── audio_generator.py
│   ├── audio_downloader.py
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
├── prompts/                    # Arquivos de configuração de prompts
│   ├── Scene_Suggestion.txt
│   └── IMG_PATTERNS.txt
├── output/                     # Diretório de saída dos arquivos gerados
│   ├── audio/
│   ├── imgs_output/
│   ├── render_output/
│   └── ...
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx
│   │   ├── MainPanel.jsx
│   │   ├── ExecutionLog.jsx
│   │   ├── ApiKeyModal.jsx
│   │   ├── ImageSuggestionsConfigModal.jsx
│   │   └── Layout.jsx
│   └── App.jsx
├── server.js                   # Servidor backend
└── venv/                       # Ambiente virtual Python
```

## 🔐 Configuração

A configuração de chaves de API agora é feita diretamente pela interface gráfica na aba **API Key**. Não é necessário editar o arquivo `.env` manualmente.

As chaves suportadas incluem:
- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_MODEL`
- **GenAI Pro**: `GENAIPRO_API_KEY`
- **YouTube**: `YT_API_KEY`, `YOUTUBE_CHANNEL_ID`
- **Notion**: `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `NOTION_DATA_SOURCE_ID`

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
