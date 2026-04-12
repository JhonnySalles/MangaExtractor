# Tela Principal - Manga Text Extractor (window.py)

## 🎯 Objetivo / Contexto

Tela única e principal da aplicação desktop responsável por configurar, gerenciar e executar a extração de textos de mangás utilizando OCR. A tela permite processar um único mangá, gerenciar uma fila de processamento (lista) ou estruturar arquivos físicos em pastas.

## 🧩 Componentes de UI e Arquivos

- **Classe Principal / Controller:** `src/manga_extractor/gui/window.py` (Função `main()` e Loop de Eventos do FreeSimpleGUI).
- **Layout:** Definido de forma declarativa na variável `layout` (não utiliza XML).
- **Abas (Tabs):**
  - `Tab('Operação')`: Configurações de diretório, nome, idioma e OCR, além do painel de log (`-OUTPUT-`).
  - `Tab('Lista operações')`: Tabela com a fila de mangás para processamento em lote.
  - `Tab('Montar estrutura de arquivos')`: Utilitário para ler pastas bagunçadas e organizar por Volume/Capítulo.
- **Principais Views (Keys / IDs):**
  - `-DIRECTORY-`: Input + FolderBrowse para selecionar a pasta de origem das imagens.
  - `-MANGA-`, `-VOLUME-`, `-CHAPTER-`, `-SCAN-`: Inputs para os metadados do mangá.
  - `-BASE-`: Input para o nome da tabela base no MySQL.
  - `-LANGUAGE-`: ComboBox de seleção do idioma (`Português`, `Japonês`, `Inglês`, `Japonês (vertical/horizontal)`).
  - `-OCRTYPE-`: ComboBox de seleção do motor OCR (`WinOCR` ou `Tesseract`).
  - `-FURIGANA-`: Checkbox para ativar a limpeza de Furigana.
  - `-BTN_PROCESS-`, `-BTN_PROCESS_LIST-`, `-BTN_COPY_FILES-`: Botões primários de ação (Iniciam threads de processamento).
  - `-TABLE-`: Tabela (`sg.Table`) da lista de operações.
  - `-PROGRESSBAR-`: Barra de progresso global.

## ⚙️ Regras de Negócio e Lógica (Core Logic)

- **Autopreenchimento Inteligente:** Ao selecionar um diretório (`eventDirectory`), a tela tenta ler o arquivo de configuração existente ou deduzir o Nome, Volume e Capítulo a partir dos nomes das pastas (`getDirectoryName`, `getDirectoryInformation`).
- **Busca no Banco de Dados:** Baseado no nome deduzido, a tela busca se a tabela (`-BASE-`) já existe no MySQL (`findTable`) e colore o texto do `-LABELBASE-` de verde (chartreuse) se existir, ou laranja (orangered) se for uma tabela nova. Também recupera o último volume processado (`-LASTVOLUME-`).
- **Controle do Furigana:** Se o idioma selecionado não for "Japonês", as opções de Furigana (`-FURIGANA-` e `-ADDITIONAL_FILTER_FURIGANA-`) são automaticamente desabilitadas.
- **Processamento Assíncrono (Threads):** Para não travar a interface gráfica (GUI), todas as rotinas pesadas são enviadas para Threads secundárias (`thread_process`, `thread_list_process`, `thread_copy_file`).
- **Comunicação Thread -> GUI:** As threads disparam eventos customizados de volta para a UI atualizar seu estado (`window.write_event_value`), como progressão da barra, logs do console e alertas de término/erro.

## 🔄 Fluxo de Navegação

- **Aplicação Single-Window:** Não há transição entre janelas. Toda a interação ocorre nas abas internas da janela principal instanciada por `sg.Window('Manga Text Extractor', layout)`.

## 🌍 Dicionário de Eventos Customizados (Referência para IA)

- **Eventos de Input UI:**
  - `-DIRECTORY-`, `-MANGA-`, `-BASE-`, `-TABLE-`, `-LANGUAGE-`
- **Eventos Disparados pelas Threads (Background -> Foreground):**
  - `-THREAD_AVISO-`: Dispara um Popup de aviso simples.
  - `-THREAD_LOG-`: Atualiza o log visual no memo (multiline `-OUTPUT-`).
  - `-THREAD_PROGRESSBAR_UPDATE-` / `-THREAD_PROGRESSBAR_MAX-`: Controlam o andamento da UI.
  - `-THREAD_LIST_UPDATE-`: Atualiza os dados do grid `-TABLE-`.
  - `-THREAD_ERROR-` / `-THREAD_END-`: Tratam o fim do processamento habilitando os botões novamente.
