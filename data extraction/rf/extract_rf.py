import pandas as pd
import os
import sqlite3 as sql_module
import numpy as np

def get_descendants(concept_id, conn, exceptions = []):

    """Gets descendants of all depths given a concept_id, and excludes any exceptions (if given) and their children.
    Returns a list of the descendants."""

    cursor = conn.cursor()
    seen = set()
    to_visit = [concept_id]

    descendants = []
    missing = set()
    while to_visit:
        current = to_visit.pop()
        
        query = """
            SELECT sourceId FROM Relationship
            WHERE destinationId = ? AND typeId = 116680003 AND active = 1
        """
        cursor.execute(query, (current,))
        children = [row[0] for row in cursor.fetchall()]

        for child in children:
            if child not in seen:
                if child not in exceptions:
                    seen.add(child)

                    # get the human-readable label for the concept
                    term_query = """
                        SELECT term FROM Description
                        WHERE conceptId = ? AND active = 1 AND typeId = 900000000000003001 AND languageCode IN ('nl', 'en')
                    """
                    cursor.execute(term_query, (child,))
                    term_child = cursor.fetchone()
                    if term_child is None:
                        term_child = "Geen Nederlandse term beschikbaar."
                        missing.add(child)
                    else:
                        term_child = term_child[0]
                    descendants.append((child, term_child))
                    to_visit.append(child)

    return list(descendants)

# load database

path = os.path.abspath('data/DutchSnomedCT.sqlite3')
if not os.path.exists(path):
    raise IOError(
        'Database %s not available.'
        % path)

db = sql_module.connect(path, check_same_thread=False)

# load file with risk factors
path = "/AKI_Risk_Factors_KG20250710.xlsx"
rf = pd.read_excel(path)

all_rf = {}

# add descendants
for idx, row in rf.iterrows():

    concept_id = row["SNOMED ID"]
    concept_term = row["SNOMED term"]

    # if no kids we still add itself
    all_rf[concept_id] = [((str(concept_id), concept_term))]

    # deal with multiple exceptions

    if type(row["Except SNOMED ID"]) == str: # it is a string but should be interpreted as list of ints
        exceptions = [float(i) for i in row["Except SNOMED ID"].split(", ")]

    elif type(row["Except SNOMED ID"]) == int: # single value
        exceptions = [row["Except SNOMED ID"]]

    else:
        exceptions = []

    # add kids
    if row["All children?"] == 'yes':
        descs = get_descendants(str(concept_id), db, exceptions)
        all_rf[concept_id] = descs


# put all in df
rows = []

for parent, pairs in all_rf.items():

    if parent:

        if not pairs:
            rows.append((parent, None, None))
        for pair in pairs:
            rf_id, rf_term = tuple(pair)
            if not pd.isna(parent):
                #print(parent)
                rows.append((int(parent), rf_id, rf_term))
                print(int(parent))
            else:
                rows.append((parent, rf_id, rf_term))

def clean_numeric_column(col):
    try:
        return pd.to_numeric(col, errors="raise").astype("Int64")
    except:
        return col  # leave it unchanged if it's a true string column


df = pd.DataFrame(rows, columns=["parent", "rf_id", "rf_term"])


df = df.assign(type = df.rf_term.str.extract(r'\(([^()]*)\)(?!.*\([^()]*\))')) 
snomed_aki = 14669001
df = df.assign(risk = snomed_aki)

df["parent_term"] = df.merge(rf[["SNOMED term", "SNOMED ID"]], how = "left", left_on = "parent", right_on = "SNOMED ID")["SNOMED term"]
df["risk_term"] = "acuut nierfalen"

df = df.apply(clean_numeric_column)

output_path = "risk_factors.tsv"
df.to_csv(output_path, sep = "\t")

