import pandas as pd
from RDFStarConverter import *

# inclusions file preprocessing
inc_file = "all_atc_no_DDI.txt"
inc = pd.read_csv(inc_file, sep = "\t", names = ["atc", "reason"])
inc["property"] = "includedBecause"
inc = inc[["atc", "property", "reason"]]
inc.to_csv("test_inc.tsv", sep = "\t", index = False)

mapping = {"Hypertension": "38341003", "Diabetes": "73211009", "Heart Failure": "84114007", "Chronic Kidney Disease": "709044004"}

def map_conditions(text):
    codes = set()  # avoid duplicates
    for key, code in mapping.items():
        # Match if any word in the key appears in the text
        if key in text:
            codes.add(code)
    return list(codes) if codes else None

inc["snomeds"] = inc["reason"].apply(map_conditions)
inc = inc.explode("snomeds", ignore_index = True)
inc = inc.explode("reason", ignore_index = True)

# we also include those reasons as indications/risk factors so some extra work here is needed
extra_risk = inc[inc["reason"].str.contains("NEED")].copy()
extra_risk["property"] = "isRiskFactorFor"
extra_risk["object"] = "AKIConcept"
extra_risk = extra_risk[["atc", "property", "object"]].drop_duplicates()
extra_risk.to_csv("test_extra_risk.tsv", sep = "\t", index = False)

# indications
extra_ind = inc[inc.snomeds.notnull()].copy()
extra_ind["property_new"] = "isIndicatedFor"
extra_ind = extra_ind[["atc", "property_new", "snomeds"]].drop_duplicates()
extra_ind.to_csv("test_extra_ind.tsv", sep = "\t", index = False)

inc = "test_inc.tsv"
extra_ind = "test_extra_ind.tsv"
extra_risk = "test_extra_risk.tsv"

output_path = "rdf_files/final/inclusions.ttl"

with open(output_path, "w", encoding="utf-8") as f:

    # add inclusion metadata
    conv = RdfStarConverter(
        labels = None,
        prefixes=Prefixes(sub_ns = "atc:", ob_ns = "", prop_ns = "dakikg:"),  # tweak namespaces if needed
        types = ["dakikg:Drug", ""],
        ann_obj_prefixes=[],
        ann_prop_prefixes=[],
        skip_header=True,
        tag = "@en"
    )

    turtle_star = conv.convert_file(inc)
    f.write(turtle_star)

output_path = "rdf_files/final/fk_main_extra.ttl"

with open(output_path, "w", encoding = "utf-8") as f:
    # add inclusions as indications
    conv = RdfStarConverter(
        labels = None,
        prefixes=Prefixes(sub_ns = "atc:", ob_ns = "sct:", prop_ns = "dakikg:"),  # tweak namespaces if needed
        types = ["dakikg:Drug", "sct:138875005"],
        ann_obj_prefixes=[],
        ann_prop_prefixes=[],
        skip_header=True,
    )

    turtle_star = conv.convert_file(extra_ind)
    f.write(turtle_star)

output_path = "rdf_files/final/rf_main_extra.ttl"

with open(output_path, "w", encoding = "utf-8") as f:
    # add inclusions as risk factors
    conv = RdfStarConverter(
        labels = None,
        prefixes=Prefixes(sub_ns = "atc:", ob_ns = "dakikg:", prop_ns = "dakikg:"),  # tweak namespaces if needed
        types = ["dakikg:Drug", "rdfs:Class"],
        ann_obj_prefixes=[],
        ann_prop_prefixes=[],
        skip_header=True,
    )

    turtle_star = conv.convert_file(extra_risk)
    f.write(turtle_star)
    print("Done!")
