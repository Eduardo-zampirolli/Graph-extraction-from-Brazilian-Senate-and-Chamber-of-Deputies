import requests
from bs4 import BeautifulSoup
import os
import re

def main():
    ano = int(input())
    pasta= f'senado(r)/{ano}'
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    with open(f'codigos-senado(r)/{ano}.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i in range(int(len(lines))):
            cod = int(lines[i])
            escrever(cod,pasta)

def achar_data(texto):
    t = texto[20:200]
    padrao_data = r"Em (\d{1,2}(?:º|ª)? de [a-zA-Zç]+ de \d{4})"
    match = re.search(padrao_data, t)
    data = match.group(1)
    return data

def eh_sujeito(txt):
    return txt[:6] == 'A SRA.' or txt[:5] == 'O SR.'


def escrever(codigo, pasta):
    url = f'https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/r/{codigo}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        #Coletar o texto do site
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        arquivo = os.path.join(pasta, f'{codigo}.txt')
        with open(arquivo, 'w', encoding='utf-8') as file: 
            #Achar a data em que a sessao ocorreu
            texto = soup.find('div', class_="escriba-jq")
            titulo = texto.find('h1').text
            file.write(f"{titulo}\n")
            #Achar as 'table' que possuem as falas dos sujeitos
            elements = texto.find("table", id="tabelaQuartos", class_='principalStyle') 
            quartos = elements.find_all('div', class_ = 'principalStyle')
            for quarto in quartos:
                #Achar todos os politcos que falam
                sujeitos = quarto.find_all('b')
                for sujeito in sujeitos:
                    obj = sujeito.text.strip()
                    if eh_sujeito(obj):
                        file.write(f"\n")
                #Achar todas as falas
                falas = quarto.find_all('span')
                for fala in falas:
                    file.write(fala.get_text())
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}. Code: {codigo}")

if __name__ == "__main__":
    main()

