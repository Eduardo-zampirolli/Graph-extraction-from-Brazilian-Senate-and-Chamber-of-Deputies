# Files description for data extraction

## "achar_cod_{...}.py"

Those are functions that make web-scrapping in governments sites in order to colect the necessary data from political session of the legislative.
### Imports
```python
import requests
from bs4 import BeautifulSoup
import re
import os
```
- **`requests`**: l;ibrary to access the sites
- **`BeautifulSoup`**: web-scrappin, analizing the html code as a tree, with tools to search through it
- **`re`**: Find patterns in the text

### Camara

In this we got the link to a pdf table that contained all the information from the session in a pre-defined period of time, in this code we got from the beggining to the end of a year:
```python
f"https://www.camara.leg.br/transmissoes/download?
termo=&dataInicial__proxy=01%2F01%2F{ano}&dataInicial=01%2F01%2F{ano}&
dataFinal__proxy=31%2F12%2F{ano}&dataFinal=31%2F12%2F{ano}"
```

