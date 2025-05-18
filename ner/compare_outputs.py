import json
import sys
from collections import defaultdict

def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}", file=sys.stderr)
        return None

def check_overlap(s1, e1, s2, e2):
    """Checks if two spans (s1, e1) and (s2, e2) overlap."""
    return max(s1, s2) < min(e1, e2)

def check_name_equality(name1, name2):
    """
    Verifica se dois nomes são iguais, ignorando apenas diferenças de capitalização.
    
    Args:
        name1: Primeiro nome
        name2: Segundo nome
        
    Returns:
        True se os nomes forem iguais (ignorando case), False caso contrário
    """
    return name1.lower() == name2.lower()

def get_all_raw_texts_for_canonical(canonical_name, data, original_text_content):
    """Helper to get all raw texts associated with a canonical name in a dataset."""
    raw_texts = set()
    if canonical_name in data:
        for start, end, *_ in data[canonical_name]:
            if 0 <= start < end <= len(original_text_content):
                raw_texts.add(original_text_content[start:end])
    return raw_texts

def compare_ner_results_v3(
    manual_gabarito_path,
    algo_output_path,
    original_text_path
):
    manual_data = load_json(manual_gabarito_path)
    algo_data_grouped = load_json(algo_output_path)

    if not manual_data or not algo_data_grouped:
        return "Error loading input JSON files for v3 comparison."

    try:
        with open(original_text_path, "r", encoding="utf-8") as f:
            original_text = f.read()
    except FileNotFoundError:
        return f"Error: Original text file not found at {original_text_path} for v3 comparison."

    # --- Preprocessing --- 
    # 1. Create a flat list of all algorithm entities with their original group name and raw text.
    all_algo_entities_flat = []
    for algo_canon_name, positions in algo_data_grouped.items():
        for start, end, *_ in positions:
            if 0 <= start < end <= len(original_text):
                raw_text = original_text[start:end]
                all_algo_entities_flat.append({
                    "algo_canon": algo_canon_name,
                    "start": start,
                    "end": end,
                    "raw_text": raw_text,
                    "used_in_tp_or_dm": False # Mark if used
                })
            else:
                print(f"Warning (Algo): Position {start}-{end} for canon \t{algo_canon_name}\t out of bounds.", file=sys.stderr)

    # 2. Get all raw texts for each canonical group in both manual and algo data
    manual_raw_texts_by_canon = {cn: get_all_raw_texts_for_canonical(cn, manual_data, original_text) for cn in manual_data}
    algo_raw_texts_by_canon = {cn: get_all_raw_texts_for_canonical(cn, algo_data_grouped, original_text) for cn in algo_data_grouped}
    
    true_positives = []
    detected_misgrouped = []
    false_negatives = []

    # --- Main Comparison Logic --- 
    for manual_canon, manual_occurrences in manual_data.items():
        manual_canon_associated_raw_texts = manual_raw_texts_by_canon.get(manual_canon, set())

        for m_start, m_end, *_ in manual_occurrences:
            manual_entity_raw_text = original_text[m_start:m_end] if 0 <= m_start < m_end <= len(original_text) else "[MANUAL_BOUNDS_ERR]"
            matched_this_manual_entity_as_tp = False
            matched_this_manual_entity_as_dm = False

            # Check against all flat algorithm entities for overlap
            for algo_entity_dict in all_algo_entities_flat:
                if algo_entity_dict["used_in_tp_or_dm"]: # If already used for another manual entity, consider skipping or refine logic
                    # For now, an algo entity can match multiple manual entities if they overlap with it.
                    # This might lead to an algo entity being part of multiple TPs/DMs if it spans across them.
                    # This is generally acceptable in span-based evaluations.
                    pass 

                if check_overlap(m_start, m_end, algo_entity_dict["start"], algo_entity_dict["end"]):
                    # Overlap detected. Now check name equality.
                    algo_entity_original_canon = algo_entity_dict["algo_canon"]
                    
                    # NOVA VERIFICAÇÃO: Verifica se os nomes são exatamente iguais (ignorando apenas case)
                    # Compara o nome canônico manual com o nome canônico do algoritmo
                    names_are_equal = check_name_equality(
                        manual_canon, 
                        algo_entity_original_canon
                    )
                    
                    # Também verifica se o texto bruto da entidade manual é igual ao nome canônico do algoritmo
                    raw_text_equal_to_algo_canon = check_name_equality(
                        manual_entity_raw_text,
                        algo_entity_original_canon
                    )
                    
                    # Verifica se o nome canônico manual é igual ao texto bruto da entidade do algoritmo
                    manual_canon_equal_to_algo_raw = check_name_equality(
                        manual_canon,
                        algo_entity_dict["raw_text"]
                    )
                    
                    # Verifica se os textos brutos são iguais
                    raw_texts_are_equal = check_name_equality(
                        manual_entity_raw_text,
                        algo_entity_dict["raw_text"]
                    )
                    
                    # Considera verdadeiro positivo se qualquer uma das comparações de nome for igual
                    is_name_match = names_are_equal or raw_text_equal_to_algo_canon or manual_canon_equal_to_algo_raw or raw_texts_are_equal
                    
                    # Verificação conceitual original (mantida para compatibilidade)
                    algo_canon_associated_raw_texts = algo_raw_texts_by_canon.get(algo_entity_original_canon, set())
                    is_conceptually_equivalent = bool(manual_canon_associated_raw_texts.intersection(algo_canon_associated_raw_texts))
                    
                    # Só considera verdadeiro positivo se AMBOS os critérios forem atendidos:
                    # 1. Há sobreposição de spans
                    # 2. Os nomes são exatamente iguais (ignorando apenas case)
                    if is_name_match and is_conceptually_equivalent:
                        true_positives.append({
                            "manual_canon": manual_canon,
                            "manual_pos": (m_start, m_end),
                            "manual_raw_text": manual_entity_raw_text,
                            "algo_canon": algo_entity_original_canon,
                            "algo_pos": (algo_entity_dict["start"], algo_entity_dict["end"]),
                            "algo_raw_text": algo_entity_dict["raw_text"],
                            "span_relation": "overlap",
                            "name_equality": "match"
                        })
                        algo_entity_dict["used_in_tp_or_dm"] = True 
                        matched_this_manual_entity_as_tp = True
                        break # This manual entity is TP, move to next manual entity
                    else:
                        # Overlap exists, but names don't match = Detected Misgrouped
                        detected_misgrouped.append({
                            "manual_canon": manual_canon,
                            "manual_pos": (m_start, m_end),
                            "manual_raw_text": manual_entity_raw_text,
                            "algo_canon_detected_under": algo_entity_original_canon,
                            "algo_pos_detected": (algo_entity_dict["start"], algo_entity_dict["end"]),
                            "algo_raw_text_detected": algo_entity_dict["raw_text"],
                            "span_relation": "overlap",
                            "reason": "name_mismatch" if not is_name_match else "concept_mismatch"
                        })
                        algo_entity_dict["used_in_tp_or_dm"] = True
                        matched_this_manual_entity_as_dm = True
                        break # This manual entity is DM, move to next manual entity
            
            if not matched_this_manual_entity_as_tp and not matched_this_manual_entity_as_dm:
                false_negatives.append({
                    "manual_canon": manual_canon,
                    "manual_pos": (m_start, m_end),
                    "manual_raw_text": manual_entity_raw_text
                })

    # --- Identify False Positives --- 
    false_positives = []
    for algo_entity_dict in all_algo_entities_flat:
        if not algo_entity_dict["used_in_tp_or_dm"]:
            false_positives.append({
                "algo_canon": algo_entity_dict["algo_canon"],
                "algo_pos": (algo_entity_dict["start"], algo_entity_dict["end"]),
                "algo_raw_text": algo_entity_dict["raw_text"]
            })

    # --- Report Generation --- 
    report = ["## Relatório de Comparação NER (v4 - Overlap, Igualdade Exata de Nomes)\n"]
    report.append(f"Total de Ocorrências Manuais (Gabarito): {sum(len(v) for v in manual_data.values())}")
    report.append(f"Total de Ocorrências do Algoritmo: {len(all_algo_entities_flat)}\n")
    report.append(f"Critério de Igualdade: Nomes exatamente iguais (ignorando apenas maiúsculas/minúsculas)\n")
    
    tp_count = len(true_positives)
    dm_count = len(detected_misgrouped)
    fn_count = len(false_negatives)
    fp_count = len(false_positives)

    report.append(f"### Métricas Gerais")
    report.append(f"- True Positives (TP - Detecção e Agrupamento Corretos com Overlap e Nomes Iguais): {tp_count}")
    report.append(f"- Detected but Misgrouped (DM - Detecção Correta com Overlap, mas Nomes Diferentes ou Agrupamento Incorreto): {dm_count}")
    report.append(f"- False Negatives (FN - Entidades do Gabarito Não Detectadas): {fn_count}")
    report.append(f"- False Positives (FP - Entidades Detectadas pelo Algoritmo, Ausentes no Gabarito ou Não Usadas em TP/DM): {fp_count}\n")

    # Strict Precision/Recall/F1 (TP only)
    precision_strict = tp_count / (tp_count + fp_count + dm_count) if (tp_count + fp_count + dm_count) > 0 else 0
    recall_strict = tp_count / (tp_count + fn_count + dm_count) if (tp_count + fn_count + dm_count) > 0 else 0
    f1_strict = 2 * (precision_strict * recall_strict) / (precision_strict + recall_strict) if (precision_strict + recall_strict) > 0 else 0
    report.append(f"Métricas Estritas (TPs contam para acerto; DMs contam como erro tanto para precisão quanto para recall):")
    report.append(f"  - Precisão Estrita: {precision_strict:.4f}")
    report.append(f"  - Recall Estrito: {recall_strict:.4f}")
    report.append(f"  - F1-Score Estrito: {f1_strict:.4f}\n")

    # Lenient Precision/Recall/F1 (TP + DM as correct detection for recall)
    precision_lenient_detection = (tp_count + dm_count) / (tp_count + dm_count + fp_count) if (tp_count + dm_count + fp_count) > 0 else 0
    recall_lenient_detection = (tp_count + dm_count) / (tp_count + dm_count + fn_count) if (tp_count + dm_count + fn_count) > 0 else 0
    f1_lenient_detection = 2 * (precision_lenient_detection * recall_lenient_detection) / (precision_lenient_detection + recall_lenient_detection) if (precision_lenient_detection + recall_lenient_detection) > 0 else 0
    report.append(f"Métricas Flexíveis de Detecção (TPs e DMs contam como detecção correta para recall; DMs ainda penalizam precisão se o objetivo é agrupamento perfeito):")
    report.append(f"  - Precisão (Detecção): {precision_lenient_detection:.4f} (TP+DM / TP+DM+FP)")
    report.append(f"  - Recall (Detecção): {recall_lenient_detection:.4f} (TP+DM / TP+DM+FN)")
    report.append(f"  - F1-Score (Detecção): {f1_lenient_detection:.4f}\n")

    def format_entity_details(prefix, canon, raw, pos):
        return f"  - {prefix}: \t{canon}\t \t{raw}\t @ {pos}"

    report.append("\n### Detalhes dos True Positives (TPs)\n")
    if true_positives: 
        for item in sorted(true_positives, key=lambda x: (x["manual_canon"], x["manual_pos"][0])):
            report.append(format_entity_details("Manual", item["manual_canon"], item["manual_raw_text"], item["manual_pos"]) + 
                          f" | Algo: \t{item['algo_canon']}\t \t{item['algo_raw_text']}\t @ {item['algo_pos']}")
    else: report.append("  Nenhum True Positive.")

    report.append("\n### Detalhes dos Detected but Misgrouped (DMs)\n")
    if detected_misgrouped: 
        for item in sorted(detected_misgrouped, key=lambda x: (x["manual_canon"], x["manual_pos"][0])):
            report.append(format_entity_details("Manual", item["manual_canon"], item["manual_raw_text"], item["manual_pos"]) +
                          f" | Detectado em Algo Grupo: \t{item['algo_canon_detected_under']}\t \t{item['algo_raw_text_detected']}\t @ {item['algo_pos_detected']} | Razão: {item['reason']}")
    else: report.append("  Nenhum Detected but Misgrouped.")

    report.append("\n### Detalhes dos False Negatives (FNs)\n")
    if false_negatives: 
        for item in sorted(false_negatives, key=lambda x: (x["manual_canon"], x["manual_pos"][0])):
            report.append(format_entity_details("Manual", item["manual_canon"], item["manual_raw_text"], item["manual_pos"]))
    else: report.append("  Nenhum False Negative.")

    report.append("\n### Detalhes dos False Positives (FPs)\n")
    if false_positives: 
        for item in sorted(false_positives, key=lambda x: (x["algo_canon"], x["algo_pos"][0])):
            report.append(format_entity_details("Algoritmo", item["algo_canon"], item["algo_raw_text"], item["algo_pos"]))
    else: report.append("  Nenhum False Positive.")
        
    return "\n".join(report)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python improved_compare_outputs.py <diretorio> <arquivo_base>")
        print("Exemplo: python improved_compare_outputs.py /caminho/para/diretorio 67323")
        sys.exit(1)
    
    directory = sys.argv[1]
    base_filename = sys.argv[2]
    
    manual_gabarito_file = f"{directory}/manual_grouped.json"
    algo_output_file = f"{directory}/{base_filename}.grouped_entities.json"
    text_file = f"{directory}/reconstructed_original_from_gabarito.txt"
    report_output_path = f"{directory}/comparison_report.md"
    
    report_content = compare_ner_results_v3(
        manual_gabarito_file, 
        algo_output_file, 
        text_file
    )
    
    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"Relatório de comparação v4 salvo em: {report_output_path}")
