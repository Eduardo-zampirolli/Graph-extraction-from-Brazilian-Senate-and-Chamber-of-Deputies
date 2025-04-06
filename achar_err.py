import requests
from bs4 import BeautifulSoup
import os

def eh_sujeito(txt):
    return txt[:6] == 'A SRA.' or txt[:5] == 'O SR.'


def main():
    ano = int(input())
    pasta= f'camara-err'
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    with open(f'codigos-camara/{ano}.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i in range(int(1+len(lines)/2)):
            tipo = lines[2*i]
            cod = int(lines[(2*i)+1])
            escrever(tipo,ano, cod,pasta)
        #for line in lines:
         #   escrever(int(line),pasta)





def escrever(tipo, ano, codigo, pasta):
    url = f'https://escriba.camara.leg.br/escriba-servicosweb/html/{codigo}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 500:
        arquivo = os.path.join(pasta, f'{ano}.txt')
        with open(arquivo, 'a', encoding='utf-8') as file: 
            file.write(f"{tipo}{codigo}\n")
            # Find all elements that contain the speaker and speech

if __name__ == "__main__":
    main()
