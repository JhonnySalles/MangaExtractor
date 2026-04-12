# Visão Geral da Arquitetura - Manga Text Extractor

## 🎯 Objetivo do Projeto
Um aplicativo Desktop em Python para extrair textos de balões de fala de mangás/comics utilizando técnicas de visão computacional e OCR, salvando os resultados estruturados (por Volume, Capítulo, Página e Coordenadas) em um banco de dados MySQL.

## 🛠️ Stack Tecnológico
* **Linguagem:** Python 3.9+
* **Interface Gráfica (GUI):** FreeSimpleGUI
* **Banco de Dados:** MySQL (com uso do `mysql-connector`)
* **Visão Computacional & IA:** TensorFlow (modelos baseados no SickZil-Machine para segmentação e remoção de texto).
* **OCR:** Tesseract OCR e WinOCR.
* **Manipulação de Imagem:** Pillow (PIL) e bibliotecas auxiliares.

## 🏗️ Padrão Arquitetural
A aplicação segue uma arquitetura **Event-Driven Desktop (Orientada a Eventos)**, separada em módulos lógicos. A interface gráfica roda em um laço infinito (Main Loop) e delega tarefas pesadas (I/O, Visão Computacional, OCR) para **Worker Threads**, mantendo a interface responsiva.

### Estrutura de Módulos (Packages)
* `src/manga_extractor/gui/`: Contém a interface do usuário (`window.py`). Concentra o Layout e o Loop de Eventos.
* `src/manga_extractor/core/`: O coração da aplicação.
  * `processor.py`: Pipeline principal de processamento (`ImageProcess`). Lê imagens, segmenta balões, aplica OCR.
  * `classes.py`: Modelos de Domínio (`Operation`, `Volume`, `Chapter`, `Page`, `Text`).
  * `globals.py`: Variáveis de estado global, como flags de cancelamento (`CANCEL_OPERATION`).
* `src/manga_extractor/database/`: Camada de persistência.
  * `db_util.py`: Utilitário de banco (`BdUtil`), responsável pela criação dinâmica de tabelas e inserção/atualização de dados estruturados.
  * `bd.py`: Gerenciamento da conexão com o MySQL.
* `src/manga_extractor/utils/`: Funções utilitárias (logs de tela, leitura/gravação de JSON de configuração).
* `src/manga_extractor/modules/`: Scripts secundários ou utilitários (ex: `correction.py` para recálculo de hashes MD5).

## ⚙️ Fluxo Principal de Execução (Core Pipeline)

1. **Setup e Configuração (GUI):**
   * O usuário seleciona um diretório de imagens.
   * A aplicação deduz o nome do Mangá, Volume e Capítulo (`helpers` e `processor.py`).
   * O usuário seleciona o idioma e o motor OCR.
2. **Disparo do Processamento (Thread):**
   * Ao clicar em "Processar", um objeto `Operation` é montado.
   * Uma nova `threading.Thread` é iniciada rodando `thread_process(operation)`.
3. **Preparação do Banco de Dados (`BdUtil`):**
   * A aplicação verifica a "Base" (ex: `kami_nomi`). Se não existir, ela cria as tabelas dinamicamente no MySQL (executando scripts com sufixos `_volumes`, `_capitulos`, `_paginas`, etc.) e as *Triggers* para UUID.
4. **Processamento da Imagem (`ImageProcess`):**
   * Itera sobre cada imagem na pasta.
   * Gera um hash MD5 (`hash_pagina`) da imagem original para evitar reprocessamento ou permitir correções.
   * Pré-processamento: Redução de ruídos, máscara e segmentação de áreas com falas usando modelos de Machine Learning (TensorFlow).
   * Recorte das imagens segmentadas.
   * Aplicação do OCR selecionado nas áreas de recorte.
   * Se for Japonês, aplica filtro opcional de Furigana (se habilitado).
5. **Persistência dos Dados:**
   * O resultado é convertido na hierarquia: `Volume -> Chapter -> Page -> Texts`.
   * O método `saveVolume` mapeia o objeto completo, chamando funções em cascata (`saveChapter`, `savePage`, `saveText`) para fazer `INSERT` ou `UPDATE` no MySQL baseando-se em lógicas de *Upsert* (buscando por ID/Hashes).
6. **Feedback para UI:**
   * Ao longo do processo, a Thread emite eventos `window.write_event_value('-THREAD_LOG-', msg)` que o laço principal da GUI intercepta e exibe no console nativo (`sg.Multiline`).

## 🗄️ Estrutura Dinâmica do Banco de Dados
Uma particularidade muito importante desta arquitetura é que as tabelas **não são fixas**. Para cada mangá (ou "Base"), é criado um conjunto isolado de tabelas usando um sufixo.

Se o mangá for "Teste", o sistema criará:
* `teste_volumes`: Metadados do encadernado (Idioma).
* `teste_capitulos`: Dados do scan, número do capítulo, flag de raw/extra.
* `teste_paginas`: Arquivos de imagem mapeados (MD5, número, nome).
* `teste_textos`: Lista de textos contendo `posicao_x1, y1, x2, y2` da bounding box e o conteúdo extraído.
* `teste_vocabularios`: Mapeamento de palavras/termos extraídos.
* `teste_capas`: Armazenamento binário (BLOB/Base64) das capas do volume.

*Nota: Chaves primárias (IDs) são tipicamente UUIDs auto-geradas por Triggers criadas durante a inicialização da tabela (`db_util.py`).*

## 🛡️ Gestão de Erros e Cancelamento
A arquitetura possui uma variável global `globals.CANCEL_OPERATION`. O loop de imagens dentro das threads verifica constantemente essa flag. Quando o usuário clica em "Parar processamento" na GUI, a flag vai para `True`, forçando a thread a encerrar graciosamente na próxima iteração.