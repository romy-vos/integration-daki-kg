import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

pd.set_option('display.max_rows', 200)
path_ddi_new = "all_interactions_kg_annotated.tsv"
path_bst922 = "BST922T.csv"
path_bst902 = "BST902T.csv"

ddi = pd.read_csv(path_ddi_new, sep = "\t").dropna()

mfbpnrs = list(ddi.MFBPNR.unique()) 

# Check tekstsoorten
bst902 = pd.read_csv(path_bst902)
bst902 = bst902[bst902.TSNR == 104]

# achtergrondteksten = 251 (texmod 600).
# load file with txts
bst922 = pd.read_csv(path_bst922)
bst922_bg = bst922[bst922.TXTSRT == 251]
bst922_bg = bst922_bg[bst922_bg.TXMODU == 600]

# combine all the paragraphs
bst922_bg = bst922_bg[bst922_bg.TXKODE.isin(mfbpnrs)]
group = ["BSTNUM", "MUTKOD", "THMODU", "TXMODU", "THTSRT", "TXTSRT", "TXKODE", "TXBLNR"] 
text_grouped = bst922_bg.groupby(group)["TXTEXT"].agg("".join).replace(r'\s+', ' ', regex=True).rename("full_text")
bst922_bg = bst922_bg.merge(text_grouped, on=group)

ddi_text = ddi.merge(bst922_bg[["TXKODE", "full_text"]], how = "left", left_on = "MFBPNR", right_on = "TXKODE").drop_duplicates()

missing_action = ddi_text[(ddi_text.full_text.isnull()) & (ddi_text.Action == True)][["MFBPOMS", "MFBPNR"]].drop_duplicates()

search_terms_new = {"to_check_nier": ["nier", "renaal", "renale"], 
                "to_check_creatinine": ["creatinine", "kreatinine"],
                "to_check_urea": ["urea"],
                "acute kidney injury": ["acuut nierfalen", "acute nierinsufficiëntie", "acute nierbeschadiging", "nierletsel", "nierschade", "schade nier", "schade nierstructuur"],
                "acute phosphate nephropathy": ["acute fosfaat nefropathie", "fosfaat nefropathie", "fosfaat nierbeschadiging"],
                "anuria": ["anurie"], 
                "azotaemia": ["azotemie", "stijging stikstofconcentratie"], 
                "foetal renal impairment": ["foetale nierfunctiestoornis", "foetaal nierfunctie"],
                "neonatal anuria": ["neonatale anurie", "neonataal anurie"],
                "nephropathy toxic": ["nefropathie", "nefrotoxiciteit", "niertoxiciteit", "toxische nefrose", "renale toxiciteit", "nefrotoxisch"],
                "oliguria": ["oligurie"], 
                "prerenal failure": ["prerenaal nierfalen", "prerenale nier falen", "pre-renaal nierfalen", "pre-renaal falen", "prerenaal falen", "prerenale azotemie", "pre-renale azotemie"],
                "renal failure": ["nierfalen", "progressie nierfalen"],
                "renal failure neonatal": ["nierfalen neonataal", "progressie neonataal nierfalen"],
                "renal impairment": ["stoornis nierfunctie", "nierfunctiestoornis", "daalt nierfunctie", "dalen nierfunctie", "nieraandoening", "nierfunctiestoornis", "verandering nierfunctie", "verminder nierfunctie", "verminder nieren", "verslechterde nierfunctie", "verslecht nierfunctie", "verstoord nierfunctie", "gestoord nierfunctie", "verminder nierwerking"],
                "renal impairment neonatal": ["calcificatie nieren zuigeling"],
                "subacute kidney injury": ["subacuut nierfalen", "subacute nierinsufficiëntie", "subacute nierbeschadiging"],
                "albuminuria": ["albuminurie"],
                "blood creatinine abnormal": ["creatinine afwijkend", "kreatinine afwijkend", "creatinine abnormaal", "kreatinine abnormaal", "creatinine buiten", "kreatinine buiten"],
                "blood creatinine increased": ["creatinine verhoging", "kreatinine verhoging", "creatinine verhoogd", "kreatinine verhoogd", "stijging creatinine", "stijging kreatinine", "toename creatinine", "toename kreatinine"],
                "blood urea abnormal": ["bloed ureum afwijkend", "bloed ureum abnormaal"],
                "blood urea increased": ["stijging ureum", "toename ureum", "ureum verhoogd", "ureum verhoging"],
                "blood urea nitrogen/creatinine ratio increased": ["BUN stijging", "BUN verhoging", "BUN verhoogd"],
                "creatinine renal clearance abnormal": ["creatinineklaring afwijkend", "kreatinineklaring afwijkend", "creatinineklaring abnormaal", "kreaitnineklaring abnormaal", "creatinineklaring buiten", "kreatinineklaring buiten"],
                "creatinine renal clearance decreased": ["creatinineklaring daling", "kreatinineklaring daling", "creatinineklaring verlaagd", "kreatinineklaring verlaagd", "creatinineklaring verlaging", "kreatinineklaring verlaging", "creatinineklaring verminder", "kreatinineklaring verminder", "renale klaring"],
                "creatinine urine abnormal": ["creatinine urine afwijkend", "creatinine urine abnormaal", "creatinine urine buiten"],
                "creatinine urine decreased": ["creatinine urine verlaagd", "creatinine urine verminder", "creatinine urine daling", "creatinine urine dalen"],
                "crystal nephropathy": ["kristal nieren", "kristalurie", "nierstenen kristal", "kristal-nefropathie", "kristal nefropathie"],
                "fractional excretion of sodium": ["fractionele excretie natrium", "fractionele uitscheiding natrium"],
                "glomerular filtration rate abnormal": ["glomerulaire filtratie afwijkend", "glomerulaire filtratie afwijkend", "glomerulaire filtratie buiten"],
                "glomerular filtration rate decreased": ["verminder glomerulaire filtratie", "verlaag glomerulaire filtratie", "verlaging glomerulaire filtratie"],
                "hypercreatininaemenia": ["hypercreatininemie"],
                "hyponatriuria": ["hyponatriëmie", "hyponatriemie"],
                "kidney injury molecule-1": ["kidney injury molecule-1", "KIM-1"],
                "nephritis": ["glomerulonefritis", "nefritis"],
                "neutrophil gelatinase-associated lipocalin increased": ["neutrofiel gelatinase-geassocieerd lipocaline verhoogd", "neutrofiel gelatinase-geassocieerd lipocaline verhoging", "neutrofiel gelatinase-geassocieerd lipocaline stijg"],
                "oedema due to renal disease": ["oedeem nier", "oedeem"],
                "protein urine present": ["eiwit urine"],
                "proteinuria": ["proteïnurie", "nefrotisch syndroom"],
                "renal function test abnormal": ["nier functie abnormaal", "nier functie afwijkend", "nier functie buiten"],
                "renal tubular disorder": ["aandoening niertubulie", "aandoening niertubulus", "niertubulusaandoening", "renale tubulaire acidose"],
                "renal tubular dysfunction": ["tubulaire disfunctie", "niertubulaire disfunctie"],
                "renal tubular injury": ["niertubulopathie", "proximale renale tubulopathie", "proximale tubulopathie"],
                "renal tubular necrosis": ["tubulaire necrose", "tubulaire niernecrose", "niertubulusnecrose"],
                "tubulointerstitial nephritis": ["interstitiële nefritis", "tubulo-interstitiële nefritis"],
                "urea renal clearance decreased": ["verminderd ureumklaring", "ureumklaring verlaagd", "ureumklaring daling"],
                "urine output decreased": ["afgenomen urineproductie", "urine retentie", "urineretentie", "verlaagd urine productie", "verlaging urine productie", "verminderd urine productie", "daling urine productie"],
                "dialysis": ["dialyse"],
                "haemodialysis": ["hemodialyse"],
                "peritoneal dialysis": ["peritoneale dialyse"],
                "haemofiltration": ["hemodialysis", "hemofiltratie", "hemodiafiltratie"],
                "continuous haemodiafiltration": ["continue hemofiltratie", "continue hemodiafiltratie"],
                "renal transplant": ["niertransplant", "niertransplantatie", "transplantatie"],
                "rabdomyolyse": ["rabdomyolyse"],
                "natriumverlies": ["natriumverlies", "verlies natrium"],
                "intradialytic parenteral nutrition": ["intradialytische parenterale voeding", "IDPN"]
                }

df = pd.DataFrame(search_terms_new.keys())

def find_matches(text, search_terms):

    matches = []
    text_lower = text.lower()

    for key, values in search_terms.items():
        for val in values:

            val_words = val.lower().split()

            if all(word in text_lower for word in val_words):
                # Find actual match in original case (optional)
                start = text.lower().find(val.lower())
                matched_text = text[start:start+len(val)]

                matches.append((key, matched_text))

    if not matches:
        return np.nan
    return matches

def clean_html(text):

    text = str(text)
    return BeautifulSoup(text).get_text()

# transform html text to nice looking readable text
ddi_text["clean_text"] = ddi_text["full_text"].apply(lambda x: clean_html(x))

# map to keyword list    
ddi_text["full_text_meddra_new"] = ddi_text["clean_text"].apply(lambda x: find_matches(x, search_terms_new) if pd.notna(x) else np.nan)
aki_new = ddi_text[ddi_text.full_text_meddra_new.notnull()]

# create a file with all MFBs, whether there is an action, the full text (if available), and if there is any potential nephrotoxic match
overview_mfbs = ddi_text[["MFBPNR", "MFBPOMS", "Action", "clean_text", "full_text_meddra_new"]]
overview_mfbs = overview_mfbs[~overview_mfbs.astype(str).duplicated()]

# get file with already evaluated mfbs
known = pd.read_excel("All_interactions_inclu_non_simple_kg_subset_JK20250913.xlsx")
known_2 = pd.read_excel("mfbs_checked_Joanna_20251008.xlsx")
known_3 = pd.read_excel("final_mfb_check_JK20251014.xlsx")

known_2.rename(columns = {"JK": "RELEVANT DAKI-KG"}, inplace=True)
known_3.rename(columns = {"JK": "RELEVANT DAKI-KG"}, inplace = True)
overview_mfbs = overview_mfbs.merge(known[['MFBPNR', 'ACTIE/INTERACTIE', 'RELEVANT DAKI-KG', 'KENNISBANK TERM', 'MOTIVATIE']], on = "MFBPNR", how = "left")
overview_mfbs = overview_mfbs.merge(known_2[['MFBPNR', 'RELEVANT DAKI-KG']], on = "MFBPNR", how = "left")
overview_mfbs = overview_mfbs.merge(known_3[["MFBPNR", "RELEVANT DAKI-KG", "JK opmerking"]], on = "MFBPNR", how = "left")
#overview_mfbs.to_csv("mfbs_nephrotoxicity_checked.tsv", sep = "\t", index = False)

# conduct manual agreement in excel, and then load file and add individual drugs
#### load the final file

df = pd.read_excel("final_mfb_nephrotoxicity.xlsx")
ddi_minimal = ddi[["MFBPNR", "MFBPOMS", "ATCODE_x", "ATCODE_y", "ATOMSE_x", "ATOMSE_y", 
"Action"]]
df_minimal = df[["MFBPNR", "MFBPOMS", "Action", "RELEVANT FINAL NORMALIZED"]]
final = ddi_minimal.merge(df_minimal, on = ["MFBPNR", "MFBPOMS", "Action"], how = "left").drop_duplicates()
#final.to_csv("all_ddis_kg_annotated_checked.tsv", sep = "\t", encoding = "utf-8", index = False)
