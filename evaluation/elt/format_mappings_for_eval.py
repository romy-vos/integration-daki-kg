import os
from pathlib import Path
import pandas as pd
import re
import json
import numpy as np

def contains_ambiguous_frequency(text):

    keywords = ["verder", "nader", "onbekend", "tevens", "eveneens", "niet bekend"]
    return any(word in keywords for word in text.lower().split())

def contains_percentage_in_brackets(text):
    """ For example: "Zeer vaak (> 10%)" """

    pattern = r"\([^\)]*\d+%?[^\)]*\)"
    return bool(re.search(pattern, text))

def is_frequency(text):

    if (contains_percentage_in_brackets(text) or contains_ambiguous_frequency(text)):
        return text

    return ""

def filter_frequencies(df, freq_column):

    df[freq_column] = df[freq_column].apply(is_frequency)

    print(df)


def convert_to_df_row(mapping, input_path):
    
    # get properties from the mapping based on file name
    atc, title, mapping_type, extraction_date, specific_type = extract_components(input_path)

    # filter frequency
    original_text = mapping["original"]

    try:
        frequency = original_text.split(":")[0]
        non_frequency = original_text.split(":")[1] # check for error
    except IndexError:
        frequency = ""

    # check if frequency matches expected frequencies and is not just a random :
    frequency = is_frequency(frequency)

    #content = [input_path, extraction_date, atc, title, mapping_type, specific_type, original_text, mapping["conceptid"], mapping["term"], mapping["similarity"], frequency]
    row = pd.DataFrame.from_records([{"filename": input_path, 
                        "extraction_date": extraction_date,
                        "atc": atc,
                        "title": title,
                        "mapping_type": mapping_type, 
                        "specific_type": specific_type, 
                        #"fragment": mapping["fragment"],
                        "original_text": original_text,
                        "mapping_snomed_id": mapping["conceptid"],
                        "mapping_snomed_term": mapping["term"],
                        "mapping_similarity_score": mapping["similarity"],
                        "frequency": frequency}])

    row = row.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return row

def extract_components(filename):
    """ Extract metadata from filename. """

    #r'mapped_(\w+)_([\w-]+)_(\d{2}-\d{2}-\d{4})(?:_(.+))?\.txt'
    pattern = r'mapped_(\w+)-([^_]+)_([\s*\w-]+)_(\d{2}-\d{2}-\d{4})(?:_(.+))?\.txt'
    match = re.search(pattern, filename)
    
    if match:
        atc_code = match.group(1)  # Extract ATC code
        title = match.group(2)
        mapping_type = match.group(3)    # Extract type
        date = match.group(4)     # Extract date
        specific_type = match.group(5) if match.group(4) else None  # Extract specific type if it exists

        return atc_code, title, mapping_type, date, specific_type
       
    else:
        print(f"Hm something seems wrong with filename {filename}.")
        return None


def sample_for_eval(df, group, frac):
    """ Sample randomly per group. This is so we can evaluate recall (so keep all mappings from one sentence together, 
    so we can evaluate whether things were not mapped that should have been. """

    grouped = df.groupby(group)
    num_groups_to_sample = int(frac * len(grouped))

    group_keys = list(grouped.groups.keys())
    np.random.shuffle(group_keys)
    sampled_groups = group_keys[:num_groups_to_sample]

    overlapping_group = sampled_groups[:int(len(sampled_groups)/2)]

    groups_to_split = sampled_groups[int(len(sampled_groups)/2):]
    group1 = groups_to_split[:int(len(groups_to_split)/2)]
    group2 = groups_to_split[int(len(groups_to_split)/2):]

    sampled_rows_overlap = df[df.set_index(group).index.isin(overlapping_group)]
    sampled_group1 = df[df.set_index(group).index.isin(group1)]
    sampled_group2 = df[df.set_index(group).index.isin(group2)]

    group1_agg = sampled_group1.groupby(["atc", "title", "mapping_type", "original_text"])["mapping_snomed_term"].agg(list)
    group2_agg = sampled_group2.groupby(["atc", "title", "mapping_type", "original_text"])["mapping_snomed_term"].agg(list)

    return sampled_rows_overlap.sort_values(by = "atc"), sampled_group1.sort_values(by = "atc"), sampled_group2.sort_values(by = "atc"), group1_agg, group2_agg


if __name__ == "__main__":
    
    eval_mode = False

    main_folder_df = []

    input_dir = "mapping/clean_output/"
    output_dir = "mapping/clean_output/complete/"
    # input_dir = "mapping/output_with_segments_all/"
    # output_dir = "mapping/output_with_segments_all/eval_segments/"

    for root, dirs, files in os.walk(input_dir):
        if not files:
            continue

        subfolder_mappings = []
        
        # Process each file in the current subfolder
        for file_name in files:

            if file_name.endswith(".txt") and "no_match" not in file_name and :
                input_path = os.path.join(root, file_name)
                print(f"Processing file: {input_path}")
                
                # Read and process the file line by line
                with open(input_path, 'r') as f:

                    for line in f:
                        mapping = json.loads(line)
                        # Convert each line to a DataFrame row
                        row = convert_to_df_row(mapping, input_path)
                        subfolder_mappings.append(row)
            else:
                continue
        
        if subfolder_mappings:
            subfolder_df = pd.concat(subfolder_mappings, ignore_index = True).drop_duplicates()
            main_folder_df.append(subfolder_df)

    final_mappings = pd.concat(main_folder_df)
    final_mappings.to_csv("complete_clean_output.tsv", sep = "\t")

    if eval_mode:

        print("Selecting rows for evaluation....")
        
        # group 1 J
        # group 2 C

        np.random.seed(42) # for sample reproducibility
        sampled_rows_overlap, sampled_group1, sampled_group2, group1_agg, group2_agg = sample_for_eval(final_mappings, ["filename", "original_text"], 0.05)
        print(sampled_rows_overlap)
        print(len(sampled_rows_overlap))
        print(len(sampled_group1))
        print(len(sampled_group2))

        # sampled_rows_overlap.to_csv(output_dir + "sample_overlap.tsv", sep = "\t")
        # sampled_group1.to_csv(output_dir + "sample_group1.tsv", sep = "\t")
        # sampled_group2.to_csv(output_dir + "sample_group2.tsv", sep = "\t")
        
        # group1_agg.to_csv(output_dir + "agg_group1.csv", sep = "$")
        # # group2_agg.to_csv(output_dir + "agg_group2.csv", sep = "$")
        # sampled_group1.to_csv(output_dir + "sample_group1_segments.tsv", sep = "\t")
        # group1_agg.to_csv(output_dir + "agg_group1_segments.tsv", sep = "\t")

