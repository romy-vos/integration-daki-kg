import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF
from itertools import islice
from datetime import datetime
from typing import List, Tuple, Iterable, Optional
from RDFStarConverter import *
from TSVConverter import *
import numpy as np

# preprocessing indications, contra-indications, ades
# three files (from several extraction "rounds"), here we combine them all
cf_file = "complete_clean_output_freq_standardized_with_freqs_numeric.tsv"
cf_file2 = "complete_clean_output_freq_standardized_with_freqs_numeric_full_non_simple.tsv"
cf_file3 = "complete_clean_output_freq_standardized_with_freqs_numeric_full_simple.tsv"

cf1  = pd.read_csv(cf_file, sep = "\t")
cf2  = pd.read_csv(cf_file2, sep = "\t")
cf3  = pd.read_csv(cf_file3, sep = "\t")

cf = pd.concat([cf1, cf2])
cf = pd.concat([cf, cf3])

preds_mapping = {"bijwerkingen": "hasAdverseEvent", "contra-indicaties": "isContraIndicatedFor", "indicaties": "isIndicatedFor"}
cf["mapping_type"] = cf["mapping_type"].map(preds_mapping)
cf["similarity_pred"] = "hasSimilarityScore"
cf["og_pred"] = "mappedFromFragment"
cf["frequency_pred"] = np.where(cf["frequency_numeric"].notna(), "hasFrequency", None)
cf["date_pred"] = "dateRetrieved"
cf["extraction_date"] = cf["extraction_date"].apply(lambda x: datetime.strptime(x, "%d-%m-%Y").date())

# main graph
cf_main = cf[["atc", "mapping_type", "mapping_snomed_id", "frequency_pred", "frequency_numeric"]].copy()
cf_elt = cf[["atc", "mapping_type", "mapping_snomed_id", "similarity_pred", "mapping_similarity_score", "og_pred", "fragment",  "date_pred", "extraction_date"]].copy()

cf_main.to_csv("fk_main.tsv", sep = "\t", index = False)
cf_elt.to_csv("fk_elt.tsv", sep = "\t", index = False)

cf_main = "fk_main.tsv"
output_path = "rdf_files/final/fk_main.ttl"
with open(output_path, "w", encoding="utf-8") as f:

    conv = RdfStarConverter(
        prefixes = Prefixes(sub_ns = "atc:", ob_ns = "sct:", prop_ns = "dakikg:"),
        labels = None,
        types = ["dakikg:Drug", "sct:138875005"],
        ann_obj_types= [""],
        ann_obj_prefixes = [""], # literals 
        ann_prop_prefixes = ["dakikg:"],
        tag = "@nl",
        skip_header = True
    )

    turtle_star = conv.convert_file(cf_main)
    f.write(turtle_star)

    print("Done!")

cf_elt = "fk_elt.tsv"
output_path = "rdf_files/final/fk_elt.ttl"
with open(output_path, "w", encoding="utf-8") as f:

    conv = RdfStarConverter(
        prefixes = Prefixes(sub_ns = "atc:", ob_ns = "sct:", prop_ns = "dakikg:"),
        labels = None,
        types = ["dakikg:Drug", "sct:138875005"],
        ann_obj_types= ["", "", ""],
        ann_obj_prefixes = ["", "", ""], 
        ann_prop_prefixes = ["dakikg:", "dakikg:", "dcterms:"],
        tag = "@nl",
        skip_header = True
    )

    turtle_star = conv.convert_file(cf_elt)
    f.write(turtle_star)

    print("Done!")
