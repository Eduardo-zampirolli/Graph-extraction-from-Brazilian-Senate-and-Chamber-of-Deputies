#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import glob

def create_annotated_text(original_text, grouped_entities):
    """
    Cria texto anotado inserindo tags <PESSOA:nome> nas posições indicadas.
    
    Args:
        original_text: Texto original sem anotações
        grouped_entities: Dicionário com entidades agrupadas e suas posições
        
    Returns:
        Texto com anotações <PESSOA:nome>
    """
    # Cria uma lista de todas as posições de início e fim de entidades
    # Cada item é uma tupla (posição, é_início, nome_entidade)
    positions = []
    for entity_name, occurrences in grouped_entities.items():
        for start, end, *_ in occurrences:
            positions.append((start, True, entity_name))  # Início da entidade
            positions.append((end, False, entity_name))   # Fim da entidade
    
    # Ordena as posições em ordem decrescente para inserir as tags de trás para frente
    # Isso evita que as posições sejam alteradas ao inserir as tags
    positions.sort(reverse=True)
    
    # Insere as tags no texto
    annotated_text = original_text
    for pos, is_start, entity_name in positions:
        if is_start:
            # Início da entidade: insere <PESSOA:nome>
            annotated_text = annotated_text[:pos] + f"<PESSOA:{entity_name}>" + annotated_text[pos:]
        else:
            # Fim da entidade: insere </PESSOA>
            annotated_text = annotated_text[:pos] + "</PESSOA>" + annotated_text[pos:]
    
    return annotated_text

def process_file(original_text_path, grouped_entities_path, output_annotated_path=None):
    """
    Processa um arquivo, criando o texto anotado.
    
    Args:
        original_text_path: Caminho para o arquivo de texto original
        grouped_entities_path: Caminho para o arquivo JSON com entidades agrupadas
        output_annotated_path: Caminho para salvar o texto anotado (opcional)
        
    Returns:
        Texto anotado
    """
    # Carrega o texto original
    try:
        with open(original_text_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
    except Exception as e:
        print(f"Erro ao ler o arquivo de texto original {original_text_path}: {e}")
        return None
    
    # Carrega o arquivo JSON com entidades agrupadas
    try:
        with open(grouped_entities_path, 'r', encoding='utf-8') as f:
            grouped_entities = json.load(f)
    except Exception as e:
        print(f"Erro ao ler o arquivo JSON {grouped_entities_path}: {e}")
        return None
    
    # Cria o texto anotado
    annotated_text = create_annotated_text(original_text, grouped_entities)
    
    # Salva o texto anotado, se especificado
    if output_annotated_path:
        try:
            with open(output_annotated_path, 'w', encoding='utf-8') as f:
                f.write(annotated_text)
            print(f"Texto anotado salvo em {output_annotated_path}")
        except Exception as e:
            print(f"Erro ao salvar o texto anotado em {output_annotated_path}: {e}")
    
    return annotated_text

def process_directory(input_dir, output_dir=None):
    """
    Processa todos os arquivos em um diretório.
    
    Args:
        input_dir: Diretório contendo os arquivos a serem processados
        output_dir: Diretório para salvar os arquivos processados (opcional)
    """
    if output_dir is None:
        output_dir = input_dir
    
    # Garante que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Encontra todos os arquivos .txt que não são .annotated.txt
    txt_files = []
    for file in glob.glob(os.path.join(input_dir, "*.txt")):
        if not file.endswith(".annotated.txt"):
            txt_files.append(file)
    
    total_files = len(txt_files)
    print(f"Encontrados {total_files} arquivos de texto para processar")
    
    for i, txt_file in enumerate(txt_files, 1):
        base_name = os.path.basename(txt_file)
        name_without_ext = os.path.splitext(base_name)[0]
        
        # Caminho para o arquivo JSON correspondente
        json_file = os.path.join(input_dir, f"{name_without_ext}.grouped_entities.json")
        
        # Caminho para o arquivo de saída
        output_file = os.path.join(output_dir, f"{name_without_ext}.annotated.txt")
        
        if not os.path.exists(json_file):
            print(f"Arquivo JSON {json_file} não encontrado, pulando...")
            continue
        
        print(f"[{i}/{total_files}] Processando {base_name}...")
        process_file(txt_file, json_file, output_file)
    
    print(f"Processamento concluído para {total_files} arquivos")

def main():
    """
    Função principal para executar o script a partir da linha de comando.
    """
    if len(sys.argv) < 3:
        print("Uso:")
        print("  Para processar um único arquivo:")
        print("    python create_annotated.py <arquivo_texto_original> <arquivo_json> [arquivo_saida]")
        print("  Para processar um diretório:")
        print("    python create_annotated.py --dir <diretorio_entrada> [diretorio_saida]")
        sys.exit(1)
    
    # Verifica se é para processar um diretório
    if sys.argv[1] == "--dir":
        input_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        process_directory(input_dir, output_dir)
    else:
        # Processa um único arquivo
        original_text_path = sys.argv[1]
        grouped_entities_path = sys.argv[2]
        output_annotated_path = sys.argv[3] if len(sys.argv) > 3 else None
        
        if output_annotated_path is None:
            # Se não foi especificado um arquivo de saída, usa o mesmo nome do arquivo original
            # mas com a extensão .annotated.txt
            base_name = os.path.splitext(original_text_path)[0]
            output_annotated_path = f"{base_name}.annotated.txt"
        
        process_file(original_text_path, grouped_entities_path, output_annotated_path)

if __name__ == "__main__":
    main()
