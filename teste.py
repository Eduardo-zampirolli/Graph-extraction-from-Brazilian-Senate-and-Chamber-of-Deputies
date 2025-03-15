import re
import requests
from bs4 import BeautifulSoup
url = 'https://escriba.camara.leg.br/escriba-servicosweb/html/75070'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

# Extract the debate text (adjust the selector based on the HTML structure)

debate_text = soup.get_text(separator="\n")  # Combine all text with line breaks
print(soup.find_all(string='name="4037375"'))
print(soup.find_all(href=re.compile("4037375")))

soup.find_all(href=re.compile("4037375"))
#print(nome)
#print(debate_text)
