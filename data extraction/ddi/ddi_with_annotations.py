import pandas as pd
import os
import numpy as np

########################### FASE 1 GET DATA ##########################
# 1. download converted files
dir = "g-standaard/"
bst690 = pd.read_csv(dir + "BST690T.csv") 
bst691 = pd.read_csv(dir + "BST691T.csv") 
bst692 = pd.read_csv(dir + "BST692T.csv") 
bst696 = pd.read_csv(dir + "BST696T.csv") 
bst699 = pd.read_csv(dir + "BST699T.csv", low_memory = False) 
bst698 = pd.read_csv(dir + "BST698T.csv")
bst711 = pd.read_csv(dir + "BST711T.csv")
bst801 = pd.read_csv(dir + "BST801T.csv")
bst693 = pd.read_csv(dir + "BST693T.csv")

########################## FASE 2 metadata filtering ##########################
# 2. filter out and only keep items with itemnummer label = 5, which represents the interactions
bst698_label5 = bst698[bst698.MFBLBLNR == 5.]

# 3.1 filter on recent version numbers
bst698_label5 = bst698_label5.sort_values("MFBPNRV", ascending = False).drop_duplicates(["MFBPNR"])

# 3.2 then only keep the active protocols in file 690
bst690_nietvv = bst690[bst690.MFBPDVV == 0]

# 4. select active interaction mfbs
bst690_nietvv_ia = bst690_nietvv.merge(bst698_label5[["MFBPNR", "MFBPNRV"]], on = ["MFBPNR", "MFBPNRV"], how = "inner")

# 5. select "ja"-action numbers
bst693_ja = bst693[bst693.MFBAJN == "J"]

########################### FASE 3 flow filtering ############################
# 6. filter relevent protocols
bst691_ia_huidigev = bst691.merge(bst690_nietvv_ia, on = ["MFBPNR", "MFBPNRV"])

# 7. Identify which terminal steps  with action "yes"
bst691_ia_huidigev["A"] = bst691_ia_huidigev.MFBPJA.isin(bst693_ja.MFBANR)
bst691_ia_huidigev["B"] = bst691_ia_huidigev.MFBPNA.isin(bst693_ja.MFBANR)

# 8. Add column denoting any action "yes" (= either column A or B is True meaning there is some action somewhere through the MFB)
bst691_ia_huidigev["Action"] = bst691_ia_huidigev.A | bst691_ia_huidigev.B

# 8.1 create a dictionary per MFBPNR, if at some point in the MFB, an action exists
actions = (
    bst691_ia_huidigev.groupby('MFBPNR')['Action']
    .apply(lambda x: True if (x == True).any() else False)
    .to_dict()
)

bst691_ia_huidigev = bst691_ia_huidigev.drop(columns = ["A", "B", "Action"])

############################ FASE 4 waardelijsten ##############################
# 9.1 Filter out the codes that represent gpks (srtcode == 40)
bst699_gpk = bst699[bst699.SRTCODE == 40] 

# 9.2 Get mfbs with active products
active_gpk = bst699_gpk.MFBWNR.unique()

# 10. filter our questions on function number == 19 
question_numbers = list(bst691_ia_huidigev.MFBVNR.unique())
bst692_all_questions = bst692[bst692.MFBVNR.isin(question_numbers)] 
bst692_starting_points = bst692_all_questions[bst692_all_questions.MFBFUNNR == 19]

bst691_ia_huidigev_starting_points = bst691_ia_huidigev.merge(bst692_starting_points[["MFBVNR", "MFBFUNNR"]], on = ["MFBVNR"], how = "left")

# 11.1 Add the waardelijsten and the mfbfuns 2 (denoting which of the drugs within an mfb actually have the interaction)
bst696_19 = bst696[bst696.MFBFUNNR == 19] 
bst691_ia_huidigev_starting_points = bst691_ia_huidigev_starting_points.merge(bst696_19[["MFBVNR", "MFBFUNNR", "MFBFUNS2", "MFBWNR"]], on = ["MFBVNR", "MFBFUNNR"])

# 11.2 check if they are active waardelijsten
bst691_ia_huidigev_starting_points_active = bst691_ia_huidigev_starting_points[bst691_ia_huidigev_starting_points.MFBWNR.isin(active_gpk)]

# 12. And then finally match the mfbfuns2 with the actual gpks
bst699_gpk = bst699[bst699.SRTCODE == 40]
interactions_gpk = bst691_ia_huidigev_starting_points_active.merge(bst699_gpk[["MFBWNR", "CODENV"]], on = "MFBWNR", how = "left")
interactions_gpk = interactions_gpk.rename(columns = {"CODENV": "GPKODE"})

# 13.1 Then add ATC from file 711

# ATC discrepancies
#L04AH01	https://www.farmacotherapeutischkompas.nl/bladeren/preparaatteksten/s/sirolimus	L04AA1
bst711.ATCODE = bst711.ATCODE.str.strip()
bst711.loc[bst711.ATCODE == 'L04AA10', "ATCODE"] = 'L04AH01'

interactions_atc = interactions_gpk.merge(bst711[["GPKODE", "ATCODE"]], on = "GPKODE", how = "left")

# 13.2 and the ATC description from file 801 (ATC codes)\
bst801.ATCODE = bst801.ATCODE.str.strip()
bst801.loc[bst801.ATCODE == 'L04AA10', "ATCODE"] = 'L04AH01'

interactions_atc = interactions_atc.merge(bst801[["ATCODE", "ATOMSE", "ATOMS"]], on = "ATCODE")
#print(interactions_atc[interactions_atc.ATCODE == 'L04AH01'].MFBPNR.unique())

# 14. Put back the actions from the dictionary
# Actions are on MFBPNR level (it denotes whether there is ANY action for an MFB at ANY point in the MFB)
interactions_atc["Action"] = interactions_atc['MFBPNR'].map(actions)

# 15. Clean up
interactions_subset = interactions_atc[["MFBPNR", "MFBVNR", "MFBPOMS", "MFBFUNS2", "ATCODE", "MFBWNR", "ATOMSE", "Action"]].drop_duplicates().dropna()
interactions_atc_A = interactions_subset[interactions_subset.MFBFUNS2 == 1]
interactions_atc_B = interactions_subset[interactions_subset.MFBFUNS2 == 2]
interactions_combined = interactions_atc_A.merge(interactions_atc_B, on = ["MFBPNR", "MFBVNR", "MFBPOMS", "Action"], how = "left")
just_mfb = interactions_combined[["MFBPNR", "Action"]].drop_duplicates().dropna()

############################ FASE 5 MFBs relevant to DAKI-KG ############################

# 16. get list of nephrotoxic drugs + drugs indicated for a common comorbodity of ckd
with open("all_atc_no_DDI.txt", "r") as file:
    ckd_drugs = set([atc.split("\t")[0].strip() for atc in file.readlines()])

# 17. Subset drugs in scope for DAKI-KG
# subset interactions such that either the head or the tail is part of the atcs in scope
interactions_KG = interactions_combined[(interactions_combined["ATCODE_x"].isin(ckd_drugs)) | (interactions_combined.ATCODE_y.isin(ckd_drugs))]
# then select all new unique atcs following from these interactions and check if any interactions exist between the drugs indirectly in scope
new_ckd_drugs = set(list(interactions_KG.ATCODE_x.unique()) + list(interactions_KG.ATCODE_y.unique()))
interactions_KG_new = interactions_combined[(interactions_combined["ATCODE_x"].isin(new_ckd_drugs)) & (interactions_combined.ATCODE_y.isin(new_ckd_drugs))]
interactions_KG_new = interactions_KG_new[(interactions_KG_new.ATCODE_x.notnull()) & (interactions_KG_new.ATCODE_y.notnull())]
interactions_KG_all = pd.concat([interactions_KG, interactions_KG_new])

# extract all MFBs for text analysis and then come back here
#interactions_KG_all.to_csv("all_interactions_annotated.tsv", sep = "\t")

# 19. check if we extracted FK data for all included drugs
all_included = set(list(new_ckd_drugs) + list(new_ckd_drugs))

folder_path = "mapping/output_with_segments_all"
folder_path_2 = "mapping/additionally_simple"
folder_path_3 = "additionally_non_simple"

# List only immediate subfolders (not files, not deeper subfolders)
subfolders = [name for name in os.listdir(folder_path)
              if os.path.isdir(os.path.join(folder_path, name))]

subfolders2 = [name for name in os.listdir(folder_path_2)
                if os.path.isdir(os.path.join(folder_path_2, name))]

subfolders3 = [name for name in os.listdir(folder_path_3)
                if os.path.isdir(os.path.join(folder_path_3, name))]

diff = set(set(all_included) - set(subfolders) - set(subfolders2) - set(subfolders3))

# these all do not exist in FK (12-oct-25) hence we do not include these DDIs
interactions_KG_all = interactions_KG_all[(~interactions_KG_all.ATCODE_x.isin(diff)) & (~interactions_KG_all.ATCODE_y.isin(diff))]

#interactions_KG_all.to_csv("all_interactions_kg_annotated.tsv", sep = "\t")
