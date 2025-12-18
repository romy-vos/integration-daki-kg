import pandas as pd
from rapidfuzz import process, fuzz, utils
from rapidfuzz.distance import JaroWinkler
import numpy as np
import re
from mapping_report import write_mapping_report
from sklearn.metrics import cohen_kappa_score

# helper functions
_punct = re.compile(r"[^\w\s]+", flags=re.UNICODE)
def _norm(s: str) -> str:
    if pd.isna(s):
        return ""
    s = utils.default_process(str(s))  # lower + trim + collapse whitespace
    s = _punct.sub(" ", s)             # strip punctuation
    return re.sub(r"\s+", " ", s).strip()


def jw_hybrid_scorer(a, b, *, score_cutoff=None, **kwargs):
    # handle JaroWinkler separately (0–1 scale)
    jw_cut = None if score_cutoff is None else score_cutoff / 100.0
    jw = JaroWinkler.normalized_similarity(a, b, score_cutoff=jw_cut)

    # fuzz.partial_token_set_ratio uses 0–100
    pts = fuzz.partial_token_set_ratio(a, b, score_cutoff=score_cutoff)

    # Blend
    return 0.6 * (jw * 100) + 0.4 * pts   # scale jw back to 0–100

def best_match(row, cand_by_atc, scorer=jw_hybrid_scorer, threshold=50):
    atc = row["atc"]
    query = row["snomed_norm"]
    choices = cand_by_atc.get(atc, [])

    if not choices or not query:
        return pd.Series({"best_match": pd.NA, "score": pd.NA})

    choices_for_search = [c[0] for c in choices]

    matched, score, idx = process.extractOne(query, choices_for_search, scorer=scorer)
    
    if score < threshold:
        return pd.Series({"best_match": pd.NA, "score": score})
    return pd.Series({"best_match": choices[idx][1], "score": score})

def recall_metric(filename, column, max_recall, max_recall_snomed = None):
    """
    - Filename of the evaluation file
    - Column that consist of correctness evaluation
    - Returns precision value: (corr preds + (0.5*partially correct preds)) / n preds
    """
    
    filename[column] = filename[column].str.lower().str.strip()
    correct = len(filename[filename[column] == "yes"])
    partial = len(filename[filename[column] == "partial"])

    recall = (correct + (0.5*partial)) / (max_recall)

    if max_recall_snomed:
        recall_snomed = (correct + (0.5*partial)) / (max_recall_snomed)
        return recall, recall_snomed
    return recall

################################################ RECALL ######################################################

# match the mappings to the golden standard based on the matched snomed term and a fuzzy match with the golden standard
# we do this, because we have to compare the prediction to some part of the golden standard, but those are not pre-given to the ELT.
# the goal is, to get for each ELT prediction, the fragment from the golden standard that is the most fitting.

def calc_recall(df_gs, df_prec):

    df_prec["snomed_norm"] = df_prec["snomed description"].map(_norm)
    df_gs["gold_norm"] = df_gs["golden_standard"].map(_norm)

    # group candidates per ATC
    cand_by_atc = (
        df_gs.groupby("atc")[["gold_norm", "golden_standard"]]
            .apply(lambda g: list(map(tuple, g.values.tolist())))
            .to_dict()
    )

    # we fuzzy match with a super low threshold and manually check if this is ok.
    # low threshold to catch cases such as steven-johnson-syndroom == sjs and any overlap is what we are looking for, we already look per ATC per text so we know there is a match already.
    # We do NOT yet judge correctness here! For that, we use the expert evaluation. We are simply mapping golden standards to mappings given by the tool.
    df_prec[["golden_standard", "score"]] = df_prec.apply(lambda row: best_match(row, cand_by_atc=cand_by_atc), axis=1)
    recall = df_gs.merge(df_prec[["atc", "snomed id", "snomed description", "correct", "snomed_norm", "golden_standard", "score"]], on = ["atc", "golden_standard"], how = "left")

    # since it is possible that there are multiple mappings provided by the ELT per golden standard item:
    # check that there is max 1 !correct! per "atc, golden standard" tuple (if more are correct, then unfair positive estimation of the recall so then this should be counted on top of the max_recall
    # 1) Count unique correct SNOMEDs per (atc, gs)
    is_correct = (
        recall["correct"].astype(str).str.strip().str.lower()
        .isin(["yes", "partial"])
    )

    tmp = (recall.loc[is_correct, ["atc", "golden_standard", "snomed id"]]
            .drop_duplicates()
            .groupby(["atc", "golden_standard"])["snomed id"]
            .nunique()
            .rename("n_correct"))


    # 2) Map counts back to every row (index-aligned via keys)
    recall["n_correct"] = (
        pd.Index(zip(recall["atc"], recall["golden_standard"]))
        .map(dict(tmp.items()))
        .fillna(0).astype(int)
    )

    # 3) Mark violators
    # here we calculate the max number of correct recalls.
    # if more mappings are seen as correct by the expert, but these are not all (separately) in the gs, then the length of the gs should be changed as well according to the expert judgement.
    # this to prevent an overly positive estimate of the recall by counting more as correct for a fragment that is counted only once in the gs ( = denumerator).
    recall["violates_at_most_one"] = is_correct & recall["n_correct"].gt(1)
    violating = recall[recall["violates_at_most_one"]]

    recall_none = recall[recall.golden_standard.isnull()]
    max_recall = len(violating[violating["correct"] == "correct"]) + (0.5 * len(violating["correct"] == "partial")) + len(df_gs) - len(recall_none)

    # for the recall*, we (partially) substract from the denumerator the golden standard elements which do not (or partially) exist in snomed
    # here we count it only as "no snomed term", if the given SNOMED CT mapping is judged as wrong by the expert 

    #n_not_snomed = (0.5 * len(df_gold[df_gold.SNOMED == "partial"])) + len(df_gold[df_gold.SNOMED == "no"])
    #n_not_snomed = (0.5 * len(recall_jo[(recall_jo.SNOMED == "partial") & (recall_jo.correct.isin(["no", "partial"]))])) + len(df_gold[(df_gold.SNOMED == "no") & (recall_jo.correct.isin(["no", "partial"]))])
    n_not_snomed_partial = 0.5 * (len(recall[(recall.correct == "partial") & (recall.SNOMED.isin(["partial", "no"]))]))
    n_not_snomed_no_partial = 0.5 * (len(recall[(recall.correct == "no") & (recall.SNOMED.isin(["partial"]))]))
    n_not_snomed_no_no = 1 * (len(recall[(recall.correct == "no") & (recall.SNOMED.isin(["no"]))]))
    n_not_snomed_no_missing = 1 * (len(recall[(recall.correct.isnull()) & (recall.SNOMED.isin(["no"]))]))
    n_not_snomed_partial_missing = 0.5 * (len(recall[(recall.correct.isnull()) & (recall.SNOMED.isin(["partial"]))]))

    n_not_snomed = n_not_snomed_partial + n_not_snomed_no_no + n_not_snomed_no_partial + n_not_snomed_no_missing + n_not_snomed_partial_missing

    max_recall_snomed = max_recall - n_not_snomed

    final_recall, recall_star = recall_metric(recall, "correct", max_recall = max_recall, max_recall_snomed=max_recall_snomed)

    return final_recall, recall_star

path = "EL_linker_evaluation/"
gs = pd.read_excel(path + "golden_standard_atc.xlsx")
r1 = pd.read_excel(path + "group1_joanna_20250210.xlsx", sheet_name = "Evaluating precision", skiprows=1)
r1["correct"] = r1["correct"].str.lower().str.strip()

r2 = pd.read_excel(path + "cornelis_evaluation_precision CB.xlsx", skiprows = 1)
r2["correct"] = r2["correct"].str.lower().str.strip()

recall1, recall_star1 = calc_recall(gs, r1)
recall2, recall_star2 = calc_recall(gs, r2)
print("recall", ((recall1 + recall2)/2))
print("recall_star", ((recall_star1 + recall_star2) / 2))

# per category
cats = ["indicaties", "bijwerkingen", "contra-indicaties"]
for cat in cats:

    gs_cat = gs[gs.type == cat].copy()
    r1_cat = r1[r1["mapping type"] == cat].copy()
    r2_cat = r2[r2["mapping type"] == cat].copy()
    recall1, recall_star1 = calc_recall(gs_cat, r1_cat)
    recall2, recall_star2 = calc_recall(gs_cat, r2_cat)
    print(f"recall for {cat}:", ((recall1 + recall2)/2))
    print(f"recall_star {cat}:", ((recall_star1 + recall_star2) / 2))
