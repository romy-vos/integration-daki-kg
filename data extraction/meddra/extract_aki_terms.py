import pandas as pd

path = "meddra_aki_to_snomed.xlsx" # file with automated mappings + manual annotations

aki = pd.read_excel(path)
aki = aki.dropna(subset = ["meddra term"])
terms = [i for i in aki["final mapping"] if pd.notna(i)]

# additional terms
aki_extra = pd.read_excel(path, sheet_name="additional_terms_fk")["final mapping"]
extra_terms = [i for i in aki_extra]

terms = terms + extra_terms

full_terms = []
for term in terms:

    term = str(term)
    
    if len(term.split(", ")) > 0:
        for t in term.split(", "):
            full_terms.append(t)
    else:
        full_terms.append(term)

full_terms = list(set(full_terms))

# dataframe with triples
result = pd.DataFrame({"s": full_terms, "p": "subClassOf", "o": "AKIConcept"})
print(result)

output_path = "akiconcept_terms.tsv"
result.to_csv(output_path, sep = "\t", index = False, encoding = "utf-8")