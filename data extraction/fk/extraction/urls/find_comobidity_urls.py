import os
from bs4 import BeautifulSoup
import requests

comorbidity = "heart_failure_acute"

if comorbidity == "ckd":
    url = "https://www.farmacotherapeutischkompas.nl/bladeren/indicatieteksten/chronische_nierschade#chronische_nierschade_overzicht_indicatietekst"
    subsection_id = "chronische_nierschade_overzicht_indicatietekst"

if comorbidity == "heart_failure":
    url = "https://www.farmacotherapeutischkompas.nl/bladeren/indicatieteksten/hartfalen__chronisch"
    subsection_id = "hartfalen__chronisch_overzicht_indicatietekst"

if comorbidity == "heart_failure_acute":
    url = "https://www.farmacotherapeutischkompas.nl/bladeren/indicatieteksten/hartfalen__acuut"
    subsection_id = "hartfalen__acuut_overzicht_indicatietekst"

if comorbidity == "diabetes_1":
    url = "https://www.farmacotherapeutischkompas.nl/bladeren/indicatieteksten/diabetes_mellitus_type_1#diabetes_mellitus_type_1_overzicht_indicatietekst"
    subsection_id = "diabetes_mellitus_type_1_overzicht_indicatietekst"

if comorbidity == "diabetes_2":
    url = "https://www.farmacotherapeutischkompas.nl/bladeren/indicatieteksten/diabetes_mellitus_type_2"
    subsection_id = "diabetes_mellitus_type_2_overzicht_indicatietekst"

if comorbidity == "hypertension":
    url = "https://www.farmacotherapeutischkompas.nl/bladeren/indicatieteksten/primaire_hypertensie#primaire_hypertensie_overzicht_indicatietekst"
    subsection_id = "primaire_hypertensie_overzicht_indicatietekst"

base_url = "https://www.farmacotherapeutischkompas.nl"

page = requests.get(url)
soup = BeautifulSoup(page.content, "html5lib")
subsection = soup.find(id = subsection_id)  
medication = subsection.findAll("a", class_ = "pat-inject icon-medicine", href = True)

output_dir = "urls/comorbidities"
output_path = os.path.join(output_dir, comorbidity)

with open(output_path + ".txt", "w") as file:
    for m in medication:
        file.write(base_url + m["href"] + "\n")
    
    print(f"File created: {output_path}")



