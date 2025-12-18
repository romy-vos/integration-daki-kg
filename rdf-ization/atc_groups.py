import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF
from itertools import islice
from datetime import datetime
from typing import List, Tuple, Iterable, Optional
from RDFStarConverter import *

file = "atc_group_triples_lang_upd_all.tsv"
df = pd.read_csv(file, sep = "\t")

df["property"] = "subClassOf"

df = df[["ATCODE", "property", "Group", "ATOMSE_drug", "ATOMSE_group"]]
df.to_csv("group_triples.tsv", sep = "\t", index = False)

file = "group_triples.tsv"

output_path = "rdf_files/final/main_drug_groups.ttl"

with open(output_path, "w", encoding="utf-8") as f:

    conv = RdfStarConverter(
        labels = "both",
        prefixes = Prefixes(sub_ns = "atc:", ob_ns = "atc:", prop_ns = "rdfs:"),
        types = ["dakikg:Drug", "dakikg:DrugClass"],
        ann_obj_types = [], 
        ann_prop_prefixes = [],
        ann_obj_prefixes = [], 
        tag = "@en",
        skip_header = True,
    )

    turtle_star = conv.convert_file(file)
    f.write(turtle_star)

    print("Done!")