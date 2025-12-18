import pandas as pd
from RDFStarConverter import *

# aki file
aki_file = "akiconcept_terms.tsv"

# preprocessing ckd smq file
ckd_file = "ckd_smq_mappings.tsv"
ckd = pd.read_csv(ckd_file, sep = "\t")
ckd["ckd_property"] = "subClassOf"
ckd["ckd_object"] = "CKDConcept"
ckd = ckd[["Mapping", "ckd_property", "ckd_object"]].drop_duplicates()
ckd.to_csv("ckd_main.tsv", sep = "\t", index = False)
ckd = "ckd_main.tsv"

output_path = "rdf_files/final/nephrotoxic_classes.ttl"
with open(output_path, "w", encoding="utf-8") as f:

    # add SMQ AKI
    conv = RdfStarConverter(
        labels = None,
        types = ["sct:138875005", "rdfs:Class"],
        prefixes = Prefixes(sub_ns = "sct:", ob_ns = "dakikg:", prop_ns = "rdfs:"),
        ann_obj_prefixes=[],
        ann_prop_prefixes= [],
        skip_header = True
        )

    turtle_star = conv.convert_file(aki_file)
    f.write(turtle_star)

    # add SMQ CKD
    conv = RdfStarConverter(
        labels = None,
        types = ["sct:138875005", "rdfs:Class"],
        prefixes = Prefixes(sub_ns = "sct:", ob_ns = "dakikg:", prop_ns = "rdfs:"),
        ann_obj_prefixes=[],
        ann_prop_prefixes= [],
        skip_header = True
        )
    turtle_star = conv.convert_file(ckd)
    f.write(turtle_star)
    print("Done!")