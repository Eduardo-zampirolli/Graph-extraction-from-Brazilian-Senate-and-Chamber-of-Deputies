import os
import re
import pandas as pd

def main():
    ses_ano = {}
    for i in range(2020, 2025):  # 2020 to 2024 (5 years)
        sessoes(i, ses_ano)
    tipo_r = {}
    for i in range(2021, 2026):  # 2021 to 2025 (5 years)
        sen_r(i, tipo_r)
    tipo_cam = {}
    for i in range(2016, 2026):  # 2016 to 2025 (10 years)
        camara(i, tipo_cam)
    # Convert to DataFrames
    df_sessoes = pd.DataFrame.from_dict(ses_ano, orient='index',  columns=['Count']).reset_index()
    df_sessoes = df_sessoes.rename(columns={'index': 'Year'})
    df_sessoes['Source'] = 'Sessoes'

    df_senado = pd.DataFrame.from_dict(tipo_r, orient='index', 
                                     columns=['Count']).reset_index()
    df_senado[['Tipo', 'Year']] = pd.DataFrame(df_senado['index'].tolist(), 
                                             index=df_senado.index)
    df_senado = df_senado.drop(columns=['index'])
    df_senado['Source'] = 'Senado'

    df_camara = pd.DataFrame.from_dict(tipo_cam, orient='index', 
                                     columns=['Count']).reset_index()
    df_camara[['Tipo', 'Year']] = pd.DataFrame(df_camara['index'].tolist(), 
                                             index=df_camara.index)
    df_camara = df_camara.drop(columns=['index'])
    df_camara['Source'] = 'Camara'

    # Combine all DataFrames
    df_combined = pd.concat([df_sessoes, df_senado, df_camara], ignore_index=True)

    # Pivot for better visualization
    df_pivot = df_combined.pivot_table(index=['Source', 'Tipo'], 
                                     columns='Year', 
                                     values='Count', 
                                     fill_value=0)

    print("Combined DataFrame:")
    print(df_combined)
    print("\nPivoted View:")
    print(df_pivot)

    # Save to CSV
    df_combined.to_csv('parliament_data_by_year.csv', index=False)
    df_pivot.to_csv('parliament_data_pivoted.csv')


def sessoes(ano, dic):
    tam = len(os.listdir(f"Senado/senado/{ano}"))
    dic[ano] = tam

def sen_r(ano, dic):
    with os.scandir(f"Senado/senado(r)/{ano}") as files:
        for nota in files:
            with open(nota, 'r', encoding='utf-8') as file:
                titulo = file.readline()
                tipo = primeira_pal(titulo)
                dic[(tipo, ano)] = dic.get((tipo, ano), 0) + 1

def camara(ano, dic):
    with os.scandir(f"Camara/camara/{ano}") as files:
        for nota in files:
            with open(nota, 'r', encoding='utf-8') as file:
                titulo = file.readlines()[1].strip()
                tipo = (titulo)[:-1]
                dic[(tipo, ano)] = dic.get((tipo, ano), 0) + 1

 
# Extract the first word after the last hyphen (ignoring ordinal indicators like ª/º)
def primeira_pal(titulo):
    match = re.search(r'- \d+[ªº]\s+-\s+(\w+)', titulo)  # \w+ captures the first word
    if match:
        first_word = match.group(1)
        return first_word

if __name__ == "__main__":
    main()
