#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import argparse
from pathlib import Path

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

def process_file(original_text_path, json_path, output_path=None):
    """
    Processa um arquivo, criando o texto anotado.
    
    Args:
        original_text_path: Caminho para o arquivo de texto original
        json_path: Caminho para o arquivo JSON com entidades agrupadas
        output_path: Caminho para salvar o texto anotado (opcional)
        
    Returns:
        Texto anotado ou None em caso de erro
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
        with open(json_path, 'r', encoding='utf-8') as f:
            grouped_entities = json.load(f)
    except Exception as e:
        print(f"Erro ao ler o arquivo JSON {json_path}: {e}")
        return None
    
    # Cria o texto anotado
    annotated_text = create_annotated_text(original_text, grouped_entities)
    
    # Salva o texto anotado, se especificado
    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(annotated_text)
            print(f"Texto anotado salvo em {output_path}")
        except Exception as e:
            print(f"Erro ao salvar o texto anotado em {output_path}: {e}")
    
    return annotated_text

def process_directories(original_texts_dir, json_dir, output_dir=None):
    """
    Processa todos os arquivos correspondentes entre os diretórios.
    
    Args:
        original_texts_dir: Diretório contendo os textos originais
        json_dir: Diretório contendo os arquivos JSON
        output_dir: Diretório para salvar os arquivos anotados (opcional)
    """
    if output_dir is None:
        output_dir = original_texts_dir
    
    # Garante que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Encontra todos os arquivos JSON
    json_files = glob.glob(os.path.join(json_dir, "*.grouped_entities.json"))
    
    if not json_files:
        print(f"Nenhum arquivo .grouped_entities.json encontrado em {json_dir}")
        return
    
    total_files = len(json_files)
    print(f"Encontrados {total_files} arquivos JSON para processar")
    
    processed_count = 0
    skipped_count = 0
    
    for i, json_file in enumerate(json_files, 1):
        # Extrai o nome base do arquivo JSON (sem caminho e sem extensão)
        json_basename = os.path.basename(json_file)
        name_without_ext = json_basename.replace(".grouped_entities.json", "")
        
        # Procura o arquivo de texto original correspondente
        original_text_file = None
        possible_text_files = [
            os.path.join(original_texts_dir, f"{name_without_ext}.txt"),
            os.path.join(original_texts_dir, f"{name_without_ext}")
        ]
        
        for text_file in possible_text_files:
            if os.path.exists(text_file):
                original_text_file = text_file
                break
        
        if not original_text_file:
            print(f"[{i}/{total_files}] Arquivo de texto original para {name_without_ext} não encontrado, pulando...")
            skipped_count += 1
            continue
        
        # Define o caminho de saída
        output_file = os.path.join(output_dir, f"{name_without_ext}.annotated.txt")
        
        print(f"[{i}/{total_files}] Processando {name_without_ext}...")
        
        # Processa o arquivo
        if process_file(original_text_file, json_file, output_file):
            processed_count += 1
        else:
            skipped_count += 1
    
    print(f"\nProcessamento concluído: {processed_count} arquivos processados, {skipped_count} arquivos pulados")

def main():
    """
    Função principal para executar o script a partir da linha de comando.
    """
    parser = argparse.ArgumentParser(description='Recria arquivos .annotated a partir de textos originais e arquivos .grouped_entities.json')
    
    # Argumentos para processamento de diretórios
    parser.add_argument('--original-dir', help='Diretório contendo os textos originais')
    parser.add_argument('--json-dir', help='Diretório contendo os arquivos .grouped_entities.json')
    parser.add_argument('--output-dir', help='Diretório para salvar os arquivos .annotated.txt (opcional)')
    
    # Argumentos para processamento de arquivos individuais
    parser.add_argument('--original-file', help='Arquivo de texto original')
    parser.add_argument('--json-file', help='Arquivo .grouped_entities.json')
    parser.add_argument('--output-file', help='Arquivo de saída .annotated.txt (opcional)')
    
    args = parser.parse_args()
    
    # Verifica se os argumentos para processamento de diretórios foram fornecidos
    if args.original_dir and args.json_dir:
        process_directories(args.original_dir, args.json_dir, args.output_dir)
    
    # Verifica se os argumentos para processamento de arquivos individuais foram fornecidos
    elif args.original_file and args.json_file:
        process_file(args.original_file, args.json_file, args.output_file)
    
    # Se nenhum argumento válido foi fornecido, exibe a ajuda
    else:
        parser.print_help()
        print("\nExemplos de uso:")
        print("  Para processar diretórios:")
        print("    python recreate_annotated.py --original-dir /caminho/para/textos --json-dir /caminho/para/jsons --output-dir /caminho/para/saida")
        print("  Para processar um único arquivo:")
        print("    python recreate_annotated.py --original-file arquivo.txt --json-file arquivo.grouped_entities.json --output-file arquivo.annotated.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
