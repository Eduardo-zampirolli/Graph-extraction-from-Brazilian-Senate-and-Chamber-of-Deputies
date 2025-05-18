# NER para Textos Parlamentares

Este repositório contém scripts para reconhecimento de entidades nomeadas (NER) em textos parlamentares brasileiros, com foco na identificação de pessoas (PESSOA).

## Arquivos do Projeto

### Scripts Principais

- **ner.py**: Script principal que realiza o reconhecimento de entidades nomeadas em textos, utilizando um modelo pré-treinado. Gera arquivos `.grouped_entities.json` com as entidades agrupadas.

- **create_annotations.py**: Cria arquivos `.annotated.txt` a partir de textos originais e arquivos `.grouped_entities.json`, inserindo tags `<PESSOA:nome>` nas posições corretas.

- **extract_annotation.py**: Extrai entidades manualmente anotadas de arquivos de gabarito, gerando arquivos JSON com as entidades extraídas.

- **create_manual.py**: Cria arquivos JSON agrupados a partir de anotações manuais extraídas.

- **compare_outputs.py**: Compara os resultados do NER automático com anotações manuais (gabarito), gerando relatórios de métricas como precisão, recall e F1-score.

## Métodos Importantes

### Mesclagem de Entidades

O processo de mesclagem (`_merge_adjacent_entities`) combina entidades adjacentes ou sobrepostas que provavelmente pertencem ao mesmo nome. Por exemplo:

- Entidades fragmentadas como "Senador" e "João Silva" são mescladas em "Senador João Silva"
- Nomes separados por espaços ou conectores como "de", "da", "do" são unidos
- Entidades sobrepostas são combinadas para formar uma única menção

### Agrupamento de Entidades

O agrupamento (`_group_similar_persons`) identifica diferentes variações do mesmo nome e as agrupa sob um nome canônico:

- Usa similaridade de texto para identificar variações do mesmo nome (ex: "João Silva", "J. Silva", "Silva")
- Prioriza nomes mais completos como representantes do grupo
- Mantém todas as posições de ocorrência para cada entidade agrupada
- Utiliza a biblioteca fuzzywuzzy para calcular similaridade entre strings

### Método de Teste

O processo de avaliação (`compare_outputs.py`) compara os resultados do NER com anotações manuais:

- **True Positives (TP)**: Entidades corretamente identificadas e agrupadas
- **Detected but Misgrouped (DM)**: Entidades detectadas mas agrupadas incorretamente
- **False Negatives (FN)**: Entidades do gabarito não detectadas
- **False Positives (FP)**: Entidades detectadas incorretamente

Calcula métricas de precisão, recall e F1-score em dois modos:
- **Estrito**: Apenas TPs são considerados acertos
- **Flexível**: TPs e DMs são considerados detecções corretas

## Como Usar

### Processamento de Textos

1. **Reconhecimento de Entidades**:
   ```
   python ner.py <diretorio_entrada> <diretorio_saida>
   ```
   Processa todos os arquivos `.txt` no diretório de entrada e gera arquivos `.grouped_entities.json` no diretório de saída.

2. **Criação de Arquivos Anotados**:
   ```
   python create_annotations.py --original-dir <dir_textos> --json-dir <dir_json> --output-dir <dir_saida>
   ```
   Cria arquivos `.annotated.txt` a partir dos textos originais e dos arquivos JSON gerados pelo NER.

3. **Extração de Anotações Manuais**:
   ```
   python extract_annotation.py <arquivo_gabarito> <arquivo_json_saida> <arquivo_texto_reconstruido>
   ```
   Extrai entidades de um arquivo de gabarito manual.

4. **Comparação de Resultados**:
   ```
   python compare_outputs.py <diretorio> <arquivo_base>
   ```
   Compara os resultados do NER com anotações manuais e gera um relatório de métricas.

## Fluxo de Trabalho

1. Execute o `ner.py` para processar os textos e gerar os arquivos `.grouped_entities.json`
2. Use o `create_annotations.py` para gerar os arquivos `.annotated.txt` com as tags
3. Para avaliação, extraia anotações manuais com `extract_annotation.py`
4. Compare os resultados usando `compare_outputs.py`