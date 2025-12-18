import os
from bs4 import BeautifulSoup
import requests
from collections import defaultdict

# need URLs
with open("urls/need/need_urls.txt", "r") as file:
    need = file.readlines()

# comorbidities
with open("urls/comorbidities/ckd.txt") as file:
    chronic_kidney_disease = file.readlines()

with open("urls/comorbidities/diabetes_1.txt") as file:
    diabetes_1 = file.readlines()

with open("urls/comorbidities/diabetes_2.txt") as file:
    diabetes_2 = file.readlines()

with open("urls/comorbidities/heart_failure_acute.txt") as file:
    heart_failure_acute = file.readlines()

with open("urls/comorbidities/heart_failure.txt") as file:
    heart_failure = file.readlines()

with open("urls/comorbidities/hypertension.txt") as file:
    hypertension = file.readlines()

list_contents = {"NEED": need, "Chronic Kidney Disease": chronic_kidney_disease, "Diabetes type 1": diabetes_1, "Diabetes type 2": diabetes_2, "Heart Failure": heart_failure, "Acute Heart Failure": heart_failure_acute, "Hypertension": hypertension}
all_atc = defaultdict(list)
all_atc_removed = []

for name, contents in list_contents.items():

    for url in contents:

        print(url)
        # go to URL
        page = requests.get(url.strip())
        soup = BeautifulSoup(page.content, "html5lib")
        # extract ATC 
        bylines = soup.findAll(class_ = "byline-item")

        try: 
            atc = bylines[1].text
            all_atc[atc].append(name)
        except IndexError:
            print("THIS URL DOES NOT EXIST ANYMORE. ", url)
            all_atc_removed.append(url)
            continue

with open("all_atc_no_DDI_removed_from_fk.txt", "w") as output:
    for line in all_atc_removed:
        output.write(line + "\n")


with open("all_atc_no_DDI.txt", "w") as output:
    for key, value in all_atc.items():
        output.write(str(key) + "\t" + str(value) + "\n")
