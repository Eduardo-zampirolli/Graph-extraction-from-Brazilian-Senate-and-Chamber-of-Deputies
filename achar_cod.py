import requests
from bs4 import BeautifulSoup
import os

def achar(pasta, ano):
    url = f"https://www.camara.leg.br/transmissoes/download?termo=&dataInicial__proxy=01%2F01%2F{ano}&dataInicial=01%2F01%2F{ano}&dataFinal__proxy=31%2F12%2F{ano}&dataFinal=31%2F12%2F{ano}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        #print(soup)            
        linhas = soup.find_all('td')

        arquivo = os.path.join(pasta, f'{ano}.txt')

        with open(arquivo, 'w', encoding='utf-8') as file:
            for linha in linhas:
                cat = linha.find('span', class_="g-agenda__categoria")
                if cat != None:
                    texto = cat.text.strip()
                    if len(texto) > 0:
                        tipo = texto.split()[0]
                        a = linha.find('a')
                        link = a.get('href')
                        codigo = link.split('/')[-1]
                        if tipo!='Outros' and tipo!="SECRETARIA":
                            file.write(f"{tipo}:\n{codigo}\n")
                        #file.write(f"{tipo}:\n{codigo}\n")

def main():
    global pasta
    pasta = 'codigos'
    ano = int(input())
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    achar(pasta,ano)

if __name__ == "__main__":
    main()
