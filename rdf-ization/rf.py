import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF
from itertools import islice
from datetime import datetime
from typing import List, Tuple, Iterable, Optional
from RDFStarConverter import *

rf_file = "risk_factors.tsv"
rf = pd.read_csv(rf_file, sep = "\t")
rf["risk_property"] = "isRiskFactorFor"
rf["risk_object"] = "AKIConcept"
rf = rf[["parent", "risk_property", "risk_object"]].dropna().drop_duplicates()
rf.to_csv("test_rf.tsv", sep = "\t", index = False)
rf = "test_rf.tsv"

output_path = "rdf_files/final/rf_main.ttl"
with open(output_path, "w", encoding="utf-8") as f:

    conv = RdfStarConverter(
        labels = None,
        types = ["sct:138875005", "rdfs:Class"],
        ann_obj_types = [""], 
        prefixes= Prefixes(sub_ns = "sct:", ob_ns = "dakikg:", prop_ns = "dakikg:"), 
        ann_obj_prefixes = [],
        ann_prop_prefixes = [],
        skip_header=True
        )

    turtle_star = conv.convert_file(rf)
    f.write(turtle_star)
    print("Done!")