import requests
from bs4 import BeautifulSoup
import re
import os

#Funcao que analisa se ha notas taquigraficas no site com o codigo inserido
def possui_notas(soup):
    aviso = soup.find('div', class_="portlet-body") 
    txt_aviso = aviso.get_text()
    if len(txt_aviso) >  300:
        return(aviso != "As sessões sem Notas Taquigráficas podem ser encontradas no Diário do Senado Federal" and aviso != "Reunião indisponível")
    return False

#Funcao que reconhece o ano de realizacao
def achar_ano(texto):
    t = texto[20:200]
    match = re.search(r'\b(20(1[6-9]|2[0-4]))\b', t)
    ano = match.group()
    return ano

#Funcao que acha codigos que possuem notas taquigraficas
def achar(codigo, pasta):
    url = f"https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/s/{codigo}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:

        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        if possui_notas(soup):
            total = soup.find('div', class_="container sf-spacer-xs")
            texto = total.get_text()
            ano = achar_ano(texto)
            with open(f'{pasta}/{ano}.txt', 'a', encoding='utf-8') as file:
                file.write(f"{codigo}\n")


def main():
    pasta = 'codigos-senado'
    if not os.path.exists(pasta):
        os.makedirs(pasta)
    for i in range(432781-422907):
        achar(i+422907,pasta)

    #for i in range(26291-23964):
    #    achar(i+23964,pasta)
    '''
    2020: 23964 até 24399
    2021: 24429 ate 24904
    2022: 24926 ate 25331 e 317954 (Sessão Deliberativa Ordinária)
    2023: 25341 ate 25877
    2024 25979 ate 26291 e 418862 ate 430902 (começou a ficar com numeros muito grandes)
    comissoes r: de 9912 ate 12560
    '''


if __name__ == "__main__":
    main()

