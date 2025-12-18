import pandas as pd
from RDFStarConverter import *
import numpy as np

def interaction_type(term):

    term = term.lower()

    if term == "yes":
        return 2
    if term == "no":
        return 0
    if term == "risk factor":
        return 1

def interaction_groups():
    pass

def to_IRI(label):
    """ Removes "illegal" IRI characters.
    Returns clean IRIs. """
    label = label.lower()
    label = label.replace("+", "_en_").replace("/", "-").replace(" ", "").replace("(", "").replace(")", "").replace("'", "").replace(".", "").replace(">", "")
    return label

interactions_file = "all_ddis_kg_annotated_checked.tsv"

df = pd.read_csv(interactions_file, sep = "\t")
df["MFBPOMS_iri"] = df["MFBPOMS"].apply(to_IRI)
df["RELEVANT FINAL NORMALIZED"] = df["RELEVANT FINAL NORMALIZED"].str.lower()

# add per MFB whether an action is required
df_action = df[["MFBPOMS_iri", "Action", "MFBPOMS"]].drop_duplicates().copy()
df_action["predicate"] = "requiresAction"
df_action = df_action[["MFBPOMS_iri", "predicate", "Action", "MFBPOMS"]]
df_action.to_csv("ddi_action.tsv", sep = "\t", index = False)

# and whether its nephrotoxic (labels are already added)
df_nephro = df[["MFBPOMS_iri", "RELEVANT FINAL NORMALIZED"]].drop_duplicates().copy()
df_nephro["predicate"] = "hasNephrotoxicEffect"
df_nephro["nephrotoxicity"] = df_nephro["RELEVANT FINAL NORMALIZED"].apply(interaction_type)
df_nephro = df_nephro[["MFBPOMS_iri", "predicate", "nephrotoxicity"]]
df_nephro.to_csv("ddi_nephro.tsv", sep = "\t", index = False)

# and the member drug-drug interaction pairs per MFBPNR
df_members = df[["MFBPOMS_iri","ATCODE_x", "ATCODE_y", "ATOMSE_x", "ATOMSE_y"]].copy()
df_members["property"] = "hasInteractionWith"
df_members["property_star"] = "isMemberOfInteraction"
df_members["property_star_2"] = "source"
df_members = df_members[["ATCODE_x", "property", "ATCODE_y", "property_star", "MFBPOMS_iri"]]
df_members.to_csv("ddi_members.tsv", sep = "\t", index = False)

output_path = "rdf_files/final/ddi_main.ttl"
with open(output_path, "w", encoding="utf-8") as f:

    conv = RdfStarConverter(
        labels = "subject",
        prefixes= Prefixes(sub_ns = "dakikg:", ob_ns = "", prop_ns = "dakikg:"), 
        types = ["dakikg:DDI", ""],
        ann_obj_types = [],
        ann_obj_prefixes = [],
        ann_prop_prefixes = [],
        skip_header=True,
        tag="@nl"
        )

    turtle_star = conv.convert_file("ddi_action.tsv")
    f.write(turtle_star)

    conv = RdfStarConverter(
        labels = None,
        prefixes= Prefixes(sub_ns = "dakikg:", ob_ns = "", prop_ns = "dakikg:"), 
        types = ["dakikg:DDI", ""],
        ann_obj_types = [],
        ann_obj_prefixes = [],
        ann_prop_prefixes = [],
        skip_header=True
        )

    turtle_star = conv.convert_file("ddi_nephro.tsv")
    f.write(turtle_star)

    conv = RdfStarConverter(
        labels = None,
        prefixes= Prefixes(sub_ns = "atc:", ob_ns = "atc:", prop_ns = "dakikg:"), 
        types = ["dakikg:Drug", "dakikg:Drug"],
        ann_obj_types = ["dakikg:DDI"],
        ann_obj_prefixes = ["dakikg:"],
        ann_prop_prefixes = ["dakikg:"],
        skip_header=True,
        tag = "@nl"
        )

    turtle_star = conv.convert_file("ddi_members.tsv")
    f.write(turtle_star)

    print("Done!")