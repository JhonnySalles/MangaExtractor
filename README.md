# Manga Text Extractor
> Programa para extrair de texto em balões de fala e salvar um banco de dados

<h4 align="center"> 
	🚧  PDV 🚀 Em construção...  🚧
</h4>

[![Build Status][travis-image]][travis-url]

<p align="center">
 <a href="#Sobre">Sobre</a> •
 <a href="#Estrutura do banco de dados">Estrutura do banco de dados</a> • 
 <a href="#Histórico-de-Release">Histórico de Release</a> • 
 <a href="#Features">Features</a> • 
 <a href="#Contribuindo">Contribuindo</a> • 
 <a href="#Exemplos">Exemplos</a>
</p>


## Sobre

Programa foi criado em Python utilizando de alguns recursos e apis a fim de estar reconhecendo os caracteres e convertendo para texto editável.

O programa percorre as imagens na pasta informada o sistema irá realizar um pré-processamento a fim de remover qualquer conteudo que não sejam as falas, utilizando dos recursos da api TensorFlow e o projeto do [SickZil-Machine](https://github.com/KUR-creative/SickZil-Machine) para este fim.

Após realizar o tratamento da imagem, será identificado as coordenadas na imagem que contém texto e processado individualmente utilizando os procedimentos do [text detection](https://github.com/qzane/text-detection)

Com as imagens recortadas em uma lista será então utilizado o WinOCR para o reconhcimento dos textos em cada seguimento da imagem.

Após obter as informações e gerar um objeto contendo as informações, estará salvando elas em um banco MySQL, no qual deve ser previamente criado.


### Estrutura da classe
    Class
    ├── nome                   # Nome informado
    ├── volume                 
    ├── capitulo               
    ├── arquivo                # Endereço completo do arquivo que está sendo processado (diretório + nome)
    ├── nomePagina             # Nome da imagem que está sendo processado
    ├── numeroPagina           # Um contador sequencial das imagens que estão no diretório
    ├── linguagem              # Linguagem informa
    ├── textos                 # Array de textos
    │   ├── texto              
    │   ├── sequencia          # Sequencia do texto na imagem
    │   ├── posX1              # Coordenadas da fala na imagem
    │   ├── posY1              
    │   ├── posX2              
    │   ├── posY2              
    └── hashPagina             # Hash md5 da imagem que está sendo processada, para futuras comparações
    
> Classe com informações da página que está sendo processada


### Estrutura do banco de dados

| id | manga | volume | capitulo | nome_pagina | numero_pagina | linguagem | hash_pagina |
| -- | ----- | ------ | -------- | ----------- | ------------- | --------- | ----------- |
|  1 | Test  |      1 |       56 | Test01.jpg  |             1 |        JP | 151515as15  |
|  2 | Dois  |      2 |    115   | D11501.jpg  |             1 |        JP | fdas155151  |

> Tabela referente as informações da página que está sendo processada


| id | id_volume | sequencia | texto                         | posicao_x1 | posicao_y1 | posicao_x2 | posicao_y2 |
| -- | --------- | --------- | ----------------------------- | ---------- | ---------- | ---------- | ---------- |
|  1 |         1 |         1 | うんそういうことならいんじゃない |         15 |         35 |         55 |         35 |
|  2 |         1 |         2 | ああそうなんだ                 |          0 |         35 |       154  |        995 |

> Tabela referente as informações dos textos identificados dos balões de fala


## Histórico de Release

* 0.0.1
    * Em progresso.


### Features

- [X] Tratamento das imagens
- [X] Segmentação da imagem em partes menores
- [X] Reconhecimento OCR dos textos
- [X] Obter a posição do texto na imagem
- [X] Salvar as informações no banco de dados,
- [X] Tesseract
- [ ] Melhoria no reconhecimento do texto
- [ ] API Cloud Vision 


## Contribuindo

1. Fork (<https://github.com/JhonnySalles/MangaExtractor/fork>)
2. Crie sua branch de recurso (`git checkout -b feature/fooBar`)
3. Faça o commit com suas alterações (`git commit -am 'Add some fooBar'`)
4. Realize o push de sua branch (`git push origin feature/fooBar`)
5. Crie um novo Pull Request

<!-- Markdown link & img dfn's -->

[travis-image]: https://img.shields.io/travis/dbader/node-datadog-metrics/master.svg?style=flat-square
[travis-url]: https://travis-ci.org/dbader/node-datadog-metrics
[wiki]: https://github.com/yourname/MangaExtractor/wiki


## Exemplos

> Tela inicial
![Tela inicial](https://raw.githubusercontent.com/JhonnySalles/MangaExtractor/main/example/Main.png)

> Execução do programa
![Execução](https://raw.githubusercontent.com/JhonnySalles/MangaExtractor/main/example/Execution.png)

> Imagem de exemplo utilizada
![Raw](https://raw.githubusercontent.com/JhonnySalles/MangaExtractor/main/example/05_117.jpg)

> Texto após o processamento salvo no banco de dados
![Banco](https://raw.githubusercontent.com/JhonnySalles/MangaExtractor/main/example/Database.png)

> Texto processado

    430
    380
    真琴のお金だしルうつか自由に使いな
    洋33自由にしルう
    は
    あーあとねきんかその金貨もうつつかかた使い方があって
    こんど今度お仕事するとこみてみたいな
    うんそういうことならいんじゃない
    ああそうなんだ
    ときしいなこの仕事の時椎名さんにお世話になってて椎名さんのおかげでうまくいったような感じだったので:お礼に:
    あそうだひとしいなこれつ椎名さんに譲ってもいいですか?
    しいな椎名さんってコンクルシオの?どうして?
    そうです:?
    、たただいしようぶまことはたら大丈夫真琴の働きへのせいしきたとう正式で妥当な報酬だからちゃんと頂いときな
