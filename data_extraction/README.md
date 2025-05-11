# Files description for data extraction

## `achar_cod_{...}.py`

Those are functions that make web-scrapping in governments sites in order to colect the necessary data from political session of the legislative.
### Imports
```python
import requests
from bs4 import BeautifulSoup
import re
import os
```
- **`requests`**: library to access the sites
- **`BeautifulSoup`**: web-scrappin, analizing the html code as a tree, with tools to search through it
- **`re`**: Find patterns in the text

### Camara (*`achar_cod_cam.py`*) 

This code uses the link to a pdf table that contained all the information from the session in a pre-defined period of time, in this code we got from the beggining to the end of a year: "https://www.camara.leg.br/transmissoes/download?termo=&dataInicial__proxy=01%2F01%2F{ano}&dataInicial=01%2F01%2F{ano}&dataFinal__proxy=31%2F12%2F{ano}&dataFinal=31%2F12%2F{ano}"

It gives access to: _CENTRO_, _COMISSAO_, _CPI_, _CONSELHO_, _GRUPO_, _PLENARIO_ and _OUTROS_

After that, it was created files for every year collected, that have all sessions codes from that year.

### Senado
_OBS: For the *Senado* it was used a different aproach, since there was no table of code session available, so those codes made web scrapping from Senado's site and loop over codes intervals (found after trying multiples numbers on site and seeing which intervals corresponded to sessions codes)._
- `achar_cod_sen_s.py`: uses the site https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/s/{codigo}
    It gives access to _SESSAO_


- `achar_cod_sen_r.py`: uses the site https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/r/{codigo}.
    It gives access to _CPI_, _COMISSOES_, _CONSELHO_, _FRENTE_, _GRUPO_, _REPRESENTACAO_


## `{...}_txt.py`

### Camara
With Beautifulwith, the code got the html script of the site: 'https://escriba.camara.leg.br/escriba-servicosweb/html/{codigo}' that gives access to the session content, the speakers and theirs speeches.
With the html tree created by `BeutifulSoup` the code collected the speakers and theirs speeches and saved in `.txt` files grouped by year.

### Senado
Same aproach of CAMARA, but uses the site: https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/s/{codigo}. 


### Senado_r
Same aproach of CAMARA, but uses the site: https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/r/{codigo}. 

## `achar_err.py`
Access all the codes that were added to the table on the oficial Camara site, but the notes weren't available to do the text colection.

## `table.py`
All the data collected was added to a sheet on `table.py`