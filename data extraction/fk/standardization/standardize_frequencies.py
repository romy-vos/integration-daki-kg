import pandas as pd
import numpy as np
pd.set_option("display.max_rows", 150)

path = "complete_clean_output_with_fragments_full_non_simple.tsv"
df = pd.read_csv(path, sep = "\t")

def standardize(term):

    mappings = []
    mapping = {
        "zeer vaak": [],
        "vaak": [],
        "soms": [],
        "zelden": [],
        "zeer zelden": [],
        "verder zijn gemeld": []
        }

    if term is not np.nan:
        term = term.lower()
        for key, _ in mapping.items():
            if (key in term):   
                mappings.append(key)
        
    # return longest ( = most precise) match
    if mappings:
        return max(mappings, key = lambda x: len(x.split()))
        
    return "onbekend"

mapping_numeric = {
    "zeer vaak": int(5),
    "vaak": int(4),
    "soms": int(3),
    "zelden": int(2),
    "zeer zelden": int(1),
    "verder zijn gemeld": int(-1),
    "onbekend": int(-1)
    }

df.loc[df.mapping_type == "bijwerkingen", "frequency_mapped"] = df.loc[df.mapping_type == "bijwerkingen", "frequency"].apply(lambda x: standardize(x))
df["frequency_numeric"] = df["frequency_mapped"].map(mapping_numeric)

df_check = df[(df.mapping_type == "bijwerkingen") & (df.frequency_numeric.isnull())]

#df.to_csv("complete_clean_output_freq_standardized_with_freqs_numeric_full_non_simple.tsv", sep = "\t")
