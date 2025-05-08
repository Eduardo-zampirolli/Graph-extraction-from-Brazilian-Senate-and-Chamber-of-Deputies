import requests
from bs4 import BeautifulSoup
import os
import re

#Funcao que determina se o texto esta se referindo ao falante
def eh_sujeito(txt):
    return txt[:6] == 'A SRA.' or txt[:5] == 'O SR.'

def main():
    ano = int(input())
    pasta= f'camara/{ano}'
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    with open(f'codigos-camara/{ano}.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i in range(int(1+len(lines)/2)):
            tipo = lines[2*i]
            cod = int(lines[(2*i)+1])
            escrever(tipo,cod,pasta)

#Encontrar a data no texto selecionado
def achar_data(texto):
    padrao_data = r"Em (\d{1,2}(?:º|ª)? de [a-zA-Zç]+ de \d{4})"
    match = re.search(padrao_data, texto)
    data = match.group(1)
    return data


def escrever(tipo, codigo, pasta):
    url = f'https://escriba.camara.leg.br/escriba-servicosweb/html/{codigo}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        arquivo = os.path.join(pasta, f'{codigo}.txt')
        with open(arquivo, 'w', encoding='utf-8') as file: 
            #Achar a data contida no titulo
            titulo = soup.find('div', class_="contentTitle").text
            data = achar_data(titulo)
            file.write(f"{data}\n")
            file.write(f"{tipo}\n")
            #Achar as 'table' que contem as falas dos sujeitos
            elements = soup.find("table") 
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
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}. Code: {tipo} {codigo}")

if __name__ == "__main__":
    main()
