import requests
from bs4 import BeautifulSoup
import os

def achar():
    url = "https://www.camara.leg.br/transmissoes/download?termo=&dataInicial__proxy=01%2F01%2F2024&dataInicial=01%2F01%2F2024&dataFinal__proxy=31%2F12%2F2024&dataFinal=31%2F12%2F2024"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        #print(soup)            
        linhas = soup.find_all('td')
        for linha in linhas:
            cat = linha.find('span', class_="g-agenda__categoria")
            if cat != None:
                texto = cat.text.strip()
                tipo = texto.split()[0]
                a = linha.find('a')
                link = a.get('href')
                codigo = link.split('/')[-1]

                print(f"{tipo}:\n{codigo}")
        sessoes = soup.find_all('span', class_="g-agenda__categoria")
       # for sessao in sessoes:
            #print(sessao)
            #print(sessoes.content)


def main():
    achar()

if __name__ == "__main__":
    main()
