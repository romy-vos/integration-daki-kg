import pandas as pd
from datetime import datetime
import numpy as np

pd.options.display.max_columns = 10
pd.options.display.max_rows = 20

dir = "g-standaard/"
bst801 = pd.read_csv(dir + "BST801T.csv")

bst801.ATCODE = bst801.ATCODE.str.strip()
bst801.ATOMSE = bst801.ATOMSE.str.strip()
bst801.ATOMS = bst801.ATOMS.str.strip()

# get ALL atcs included in the KG
import os 
path = "output_with_segments_all"
path_2 = "additionally_non_simple"
path_3 = "additionally_simple"

scraped = []

for p in [path, path_2, path_3]:
    s = [name.strip() for name in os.listdir(p)
                if os.path.isdir(os.path.join(p, name))]
    scraped += s

all_atc = list(set(scraped))

atc_mapping = {}

for atc in all_atc:
    atc_mapping[atc] = atc[0:3]

atc_mapping_df =  pd.DataFrame.from_dict(atc_mapping, orient = "index", columns = ["Group"])
atc_mapping_df.reset_index(inplace = True, drop = False)

atc_mapping_df = atc_mapping_df.merge(bst801[["ATCODE", "ATOMS", "ATOMSE"]], left_on = "Group", right_on = "ATCODE", how = "left")

# to triples
atc_mapping_df["relation"] = "part_of_group"
atc_group_triples = atc_mapping_df[["index", "ATCODE", "relation", "Group", "ATOMS", "ATOMSE"]]

#atc_group_triples.to_csv("atc_group_triples_lang_upd.tsv", sep = "\t")