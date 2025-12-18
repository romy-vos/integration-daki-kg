import requests
from time import sleep
import urllib.request, urllib.error, urllib.parse
import pandas as pd
import numpy as np

def get_last_item_url(url):

    if url is not None:

        res = url.split("/")[-1]
        return float(res)

    return np.nan

meddra_base_uri = "http://purl.bioontology.org/ontology/MEDDRA/"
snomed_base_uri = "https://data.bioontology.org/ontologies/SNOMEDCT"

encoded_uri = urllib.parse.quote(meddra_base_uri + "collections", safe='')
url = "https://data.bioontology.org/search?q=%28SMQ%29&ontologies=MEDDRA&include=prefLabel,notation&pagesize=400&page=1"
headers = {"Authorization": f"apikey token={API_KEY}"}
response = requests.get(url, headers=headers).json()
collection = response.get("collection")

smqs = {}
for item in collection:
    label = item.get("prefLabel")
    if not label.endswith("(SMQ)"):
        continue
    smq = item.get("notation")
    smqs[smq] = label

smqs = {}
smqs["20000213"] = "Chronic Kidney Disease"

# get all members of the SMQ through the "has_member" property
# SMQ = "20000213"  CKD SMQ
# SMQ = "20000003" AKI SMQ
all_smqs_df = pd.DataFrame()

for key, value in smqs.items():

    print(key)
    print(value)
    
    encoded_uri = urllib.parse.quote(meddra_base_uri + key, safe='')
    url = f"https://data.bioontology.org/ontologies/MEDDRA/classes/{encoded_uri}?display=all"

    print(url)
    headers = {"Authorization": f"apikey token={API_KEY}"}
    response = requests.get(url, headers=headers).json()
    member_property = "has_member"
    smq_members_uri = response.get("properties")[meddra_base_uri + member_property]
    smq_members = [i.split("/")[-1] for i in smq_members_uri] # keep only the meddra ID rather than the full uri

    # Then map those members (which are MedDRA terms) to SNOMED 
    # Get the matching (LOOM) SNOMED IDs using BioPortal API

    smq_mappings = {}

    for meddra_id in smq_members:

        encoded_uri = urllib.parse.quote(meddra_base_uri + meddra_id, safe='')
        url = f"https://data.bioontology.org/ontologies/MEDDRA/classes/{encoded_uri}/mappings/"

        headers = {"Authorization": f"apikey token={API_KEY}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            mappings = response.json()
            snomed_mappings = []

            for mapping in mappings:
                for cls in mapping.get("classes"):
                    ont = cls.get("links")["ontology"]
                    if ont == snomed_base_uri:
                        if cls["@id"] not in snomed_mappings:
                            snomed_mappings.append(cls["@id"])
            
            smq_mappings[meddra_id] = snomed_mappings

        else:
            print("Error:", response.status_code, response.text)

    df = pd.DataFrame.from_dict(smq_mappings, orient = "index").reset_index()
    df["MEDDRA_SMQ_label"] = value
    df["MEDDRA_SMQ_id"] = float(key)
    df = df.rename(columns = {"index": "MEDDRA"})
    df["MEDDRA"] = df[["MEDDRA"]].applymap(lambda x: float(x))
    print(df)

    #df.to_csv("bioportal_ckd_meddra_snomed.tsv", sep = "\t", index = False)
    
    # then also add the official meddra_to_snomed mappings
    # open bioportal mappings and change header names for readability
    #bioportal_mappings = pd.read_csv("bioportal_ckd_meddra_snomed.tsv", sep = "\t").drop(columns = "Unnamed: 0")
    bioportal_mappings = df
    bioportal_cols = [col for col in bioportal_mappings.columns if isinstance(col, int)]
    bioportal_mappings[bioportal_cols] = bioportal_mappings[bioportal_cols].applymap(lambda x: get_last_item_url(x))
    bioportal_mappings = bioportal_mappings.rename(columns = {col: f"BioPortal_{col}" for col in bioportal_cols})

    # then add the offical meddra_to_snomed mappings, some name changing
    meddra_mappings = pd.read_excel("aki_meddra_terms.xlsx", sheet_name = "der2_sRefset_MedDRAtoSNOMED", dtype={"mapSource": "float64", "referencedComponentId": "float64"}) # mapsource = meddra, referencedComponentId = SNOMED
    meddra_mappings = meddra_mappings.rename(columns = {"mapSource": "MEDDRA", "referencedComponentId": "MedDRA_to_SNOMEDCT"})
    mappings = bioportal_mappings.merge(meddra_mappings[["MedDRA_to_SNOMEDCT", "MEDDRA"]], how = "left", on = "MEDDRA")

    # explode df to easily turn into triples
    mappings = mappings.melt(id_vars=["MEDDRA", "MEDDRA_SMQ_id", "MEDDRA_SMQ_label"],
            var_name="Source",
            value_name="Mapping")
    mappings = mappings.dropna()

    all_smqs_df = pd.concat([df, mappings])

#all_smqs_df.to_csv("ckd_smq_mappings.tsv", sep = "\t", index = False)
#all_smqs_df.to_csv("og_aki_smq_mappings.tsv", sep = "\t", index = False)





