import requests
from bs4 import BeautifulSoup
import re
def sujeito(txt):
    return txt[:6] == 'A SRA.' or txt[:5] == 'O SR.'

codigo = 75070
url = f'https://escriba.camara.leg.br/escriba-servicosweb/html/{codigo}'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all elements that contain the speaker and speech
    elements = soup.find("table")  # Include 'div' if speech is nested in divs
    print(elements) 
    current_speaker = None
    current_speech = []
    
    for element in elements:
        if element.name == 'a' and sujeito(element.text.strip()):
            # If we encounter a new speaker, print the previous speaker and their speech
            if current_speaker:
                print(f"Speaker: {current_speaker}")
                print("Speech:", ' '.join(current_speech))
                print("\n" )
            
            # Start capturing the new speaker and their speech
            current_speaker = element.text.strip()
            current_speech = []
        elif current_speaker and element.name in ['p', 'div']:  # Capture speech from <p> or <div> tags
            # Capture the speech text
            speech_text = element.text.strip()
            if speech_text and not sujeito(speech_text):  # Avoid capturing new speakers as speech
                current_speech.append(speech_text)
    
    # Print the last speaker and their speech
    if current_speaker:
        print(f"Speaker: {current_speaker}")
        print("Speech:", ' '.join(current_speech))
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")