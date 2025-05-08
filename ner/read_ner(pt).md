## Detalhes do Script `ner.py`

O script `ner.py` é uma ferramenta abrangente para realizar Reconhecimento de Entidades Nomeadas (NER) em textos em português, com foco específico em entidades de pessoa ("PESSOA"). Ele combina métodos baseados em regras com um modelo transformer pré-treinado para extrair, mesclar, remover duplicatas e agrupar nomes de pessoas semelhantes.

### Visão Geral
O script processa arquivos de texto para:

1. Extrair entidades de pessoa usando um modelo transformer pré-treinado e métodos baseados em regras.
2. Mesclar entidades adjacentes ou sobrepostas em uma única entidade.
3. Remover duplicatas com base em seus spans.
4. Agrupar nomes semelhantes sob um nome canônico.
5. Gerar texto anotado e arquivos JSON de entidades agrupadas para análise posterior.

### Componentes Principais
#### 1. Classe `IntegratedNERProcessor`
Esta classe encapsula a lógica para NER, mesclagem, remoção de duplicatas e agrupamento.

- **`__init__`**
  - Propósito: Inicializa o processador NER carregando o modelo pré-treinado, tokenizer e pipeline NER.
  - Complexidade:
    - Lida com seleção de GPU/CPU (`torch.cuda.is_available()`).
    - Garante que o `model_max_length` do tokenizer seja válido e define um padrão, se necessário.
    - Compila expressões regulares para extração baseada em regras de títulos parlamentares e nomes.

- **`_rule_based_ner`**
  - Propósito: Extrai entidades usando regras predefinidas para títulos parlamentares e nomes.
  - Lógica:
    - Usa expressões regulares para identificar padrões como "O SR. PRESIDENTE (Nome Partido-Estado)".
    - Evita spans sobrepostos usando um conjunto `processed_spans`.

- **`_extract_entities_with_overlap`**
  - Propósito: Extrai entidades usando uma abordagem de janela deslizante para lidar com textos longos.
  - Lógica:
    - Divide o texto em chunks sobrepostos para evitar truncar entidades nas bordas.
    - Ajusta posições de entidades de chunk-relativo para texto original.

- **`_merge_adjacent_entities`**
  - Propósito: Mescla entidades adjacentes ou sobrepostas em uma única entidade.
  - Lógica:
    - Ordena entidades pela posição inicial.
    - Verifica se as entidades são adjacentes ou sobrepostas e as mescla.

- **`_remove_duplicate_spans`**
  - Propósito: Remove entidades duplicadas com spans idênticos, mantendo a de maior pontuação.

- **`_normalize_for_comparison`**
  - Propósito: Normaliza nomes para comparação removendo pontuação, títulos e espaços extras.

- **`_is_similar`**
  - Propósito: Verifica se dois nomes são semelhantes usando correspondência de strings fuzzy.

- **`_group_similar_persons`**
  - Propósito: Agrupa entidades de pessoa semelhantes sob um nome canônico.

- **`process_text`**
  - Propósito: Orquestra todo o processo NER, incluindo extração, mesclagem, remoção de duplicatas e agrupamento.

#### 2. Funções Independentes
- **`create_annotated_text`**
  - Propósito: Gera texto anotado com tags `<PESSOA:Nome>` para entidades identificadas.

- **`save_grouped_entities`**
  - Propósito: Salva o dicionário de entidades agrupadas em um arquivo JSON.

- **`save_annotated_text`**
  - Propósito: Salva o texto anotado em um arquivo.

- **`main`**
  - Propósito: Lida com argumentos de linha de comando e processa arquivos de entrada.

### Partes Complexas
1. **Extração com Janela Deslizante**
   - Ajusta posições de entidades de chunk-relativo para texto original.
   - Garante que nenhuma entidade seja perdida nas bordas dos chunks.

2. **Mesclagem de Entidades**
   - Ajusta spans e textos dinamicamente com base em sobreposições ou adjacências.

3. **Agrupamento de Nomes Semelhantes**
   - Atualiza mapeamentos dinamicamente quando nomes canônicos mudam.

### Resumo
O script `ner.py` é uma ferramenta robusta para extrair e processar entidades de pessoa de textos em português. Sua combinação de métodos baseados em regras e modelos garante alta precisão, enquanto sua lógica de mesclagem, remoção de duplicatas e agrupamento lida com casos complexos como entidades sobrepostas e variações de nomes. O script é modular e extensível, tornando-o adequado para tarefas de processamento de texto em larga escala.
