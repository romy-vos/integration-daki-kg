import pandas as pd
from rapidfuzz import process, fuzz, utils
from rapidfuzz.distance import JaroWinkler
import numpy as np
import re
from mapping_report import write_mapping_report
from sklearn.metrics import cohen_kappa_score

def precision(filename, column):
    """
    - Filename of the evaluation file
    - Column name that consist of correctness evaluation
    - Returns precision value: (corr preds + (0.5*partially correct preds)) / n preds
    """
    correct = len(filename[filename[column] == "yes"])
    partial = len(filename[filename[column] == "partial"])
    total = (len(filename))

    precision = (correct + (0.5*partial)) / total
    return precision

path = "EL_linker_evaluation/"
gs = pd.read_excel(path + "golden_standard_atc.xlsx")

r1 = pd.read_excel(path + "group1_joanna_20250210.xlsx", sheet_name = "Evaluating precision", skiprows=1)
r1["correct"] = r1["correct"].str.lower().str.strip()
pc_r1 = precision(r1, "correct")
print("precision r1", pc_r1)

r2 = pd.read_excel(path + "cornelis_evaluation_precision CB.xlsx", skiprows = 1)
r2["correct"] = r2["correct"].str.lower().str.strip()
pc_r2 = precision(r2, "correct")
print("precision r2", pc_r2)
print("average precision", (pc_r2 + pc_r1)/2)

################################################ PER GROUP ###################################################

cat = "contra-indicaties"
r1_cat = r1[r1["mapping type"] == cat].copy()
pc_r1_cat = precision(r1_cat, "correct")
r2_cat = r2[r2["mapping type"] == cat].copy()
pc_r2_cat = precision(r2_cat, "correct")
print(f"precision for {cat}", ((pc_r2_cat + pc_r1_cat) / 2))


################################################ AGREEMENT ###################################################
# we use cohen's kappa k
# ( k = (p0 - pe) / (1 - pe) ), with p0 observed agreement, pe expected agreement by chance.
# convert to numeric for ordinal scale
numeric_mapping = {"no": 0, "partial": 1, "yes": 2}

y1 = list(r1["correct"].str.lower().str.strip().map(numeric_mapping))
y2 = list(r2["correct"].str.lower().str.strip().map(numeric_mapping))

unweighted_kappa = cohen_kappa_score(y1, y2)
quad_kappa = cohen_kappa_score(y1, y2, weights="quadratic")
lin_kappa = cohen_kappa_score(y1, y2, weights="linear")

print("Cohen's kappa score", "\nUnweighted:", unweighted_kappa, "\nQuadratic:", quad_kappa, "\nLinear: ", lin_kappa)
