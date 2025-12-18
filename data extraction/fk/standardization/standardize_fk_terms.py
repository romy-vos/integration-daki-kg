from EL import EntityLinking
import os
import sqlite3 as sql_module
from collections import namedtuple
import json

def process_files_in_folder(input_folder, output_folder):

    # Loop through all directories and files in the input folder
    for root, dirs, files in os.walk(input_folder):
        # Determine the corresponding output folder path by preserving the subdirectory structure
        relative_path = os.path.relpath(root, input_folder)
        current_output_folder = os.path.join(output_folder, relative_path)

        # Create the output subdirectory if it doesn't exist
        os.makedirs(current_output_folder, exist_ok=True)
        
        # Process each file in the current directory
        for filename in files:

            # Construct full paths for input and output files
            input_path = os.path.join(root, filename)

            output_file = "mapped_" + filename
            output_path = os.path.join(current_output_folder, output_file)

            if len(str(output_path)) > 260: # max allowed file name length is 256. plus extension (.txt) = 260
                print(f"Oops, name string is too long for {output_path}.")
                output_path = output_path[0:256] + ".txt"
                print(f"Shortened output name is {output_path}.")

            # Only process files, not directories
            if os.path.isfile(input_path):
                # Check if the output file already exists
                if not os.path.exists(output_path):
                    if os.path.splitext(input_path)[1] == ".txt":
                        # Open the input and output files
                        with open(input_path, 'r') as file:
                            with open(output_path, 'w') as output:
                                # Process each file using the find_mappings_for_file function
                                find_mappings_for_file(file, output, output_dir)

                        print(f"Processed {input_path} -> {output_path}")
                else:
                    print(f"Skipped {input_path} as {output_path} already exists.")


def get_max_indices(scores):
    """ Returns list with indice(s) of the max score(s). """

    max_score = max(scores) 
    max_indices = [index for index, score in enumerate(scores) if score == max_score] 

    return max_indices

def extract_elements_with_indices(data_list, indices):
    """ Returns list of elements with the given list of indices. """

    return [data_list[i] for i in indices]


def check_concept_table(concept_id, db):

    cursor = db.cursor()
    cursor.execute("""
    SELECT category FROM ConceptCategories
    WHERE conceptId = ?;
    """, (concept_id,))
    
    result = cursor.fetchone()
    
    # only return if a result is found and the category is 'clinical finding'
    if result and result[0] == 'clinical finding':
        return True

    return False

def find_first_valid_item(lst, db, func = check_concept_table):

    for idx, item in enumerate(lst):

        if func(item.ConceptId, db):
            return idx, item

    return None  

def find_mappings_for_file(file, output_file, output_dir):

    no_match_file = os.path.join(output_dir, "no_matches.txt") # this is for debugging purposes
    mappings = []
    Mapping = namedtuple("Mapping", ["conceptid", "term", "similarity", "fragment", "original"])

    for line in file:

        final_entities_for_line = []
        final_concepts_for_line = []
        #Mapping = namedtuple("Mapping", ["conceptid", "term", "similarity", "original"])

        el = EntityLinking(line)

        if not el.AllCandidates:

            # if no candidate at all, write to additional file so that we can get an idea of which parts are not being mapped well
            print(f"Oops... No candidates for: {line}")
            with open(no_match_file, "a+") as f:
                f.write(line + "\t" + "(no candidate at all for this line)" + "\n")
                continue

        # get all candidates (candidate = part of sentence we want to map)
        for candidate in el.AllCandidates:

            # for one candidate, we only want a single match
            # if there a multiple with the same max similarity score,
            # we want the first item which is either the exact match (if exists), or the one with the most granularity
            # if this is not a clinical finding, then check the next

            # check if there are exact matches
            if (candidate.ExactMatches) and (find_first_valid_item(candidate.ExactMatches, db)):
                    idx, best_entity = find_first_valid_item(candidate.ExactMatches, db)
                    similarity = str(1)

                    if best_entity.ConceptId not in final_concepts_for_line:
                        final_concepts_for_line.append(best_entity.ConceptId)
                        mappings.append(Mapping(best_entity.ConceptId, best_entity.Term, similarity, str(candidate), line))

            else: 
                # get first item that is a clinical finding
                best_entity_check = find_first_valid_item(candidate.SimilarEntities, db)
                if best_entity_check:  
                    best_entity_idx = best_entity_check[0]
                    best_entity = best_entity_check[1]

                    if best_entity.ConceptId not in final_concepts_for_line:
                        similarity = str(candidate.similarities[best_entity_idx])

                        final_concepts_for_line.append(best_entity.ConceptId)
                        mappings.append(Mapping(best_entity.ConceptId, best_entity.Term, similarity, str(candidate), line))

                else:
                    with open(no_match_file, "a+") as f:
                        f.write(str(candidate) + "\t" + "(candidate is no clinical finding)" + "\n")

        #add to file
        # output_file.write("{}\t{}".format(",".join(map(str, final_entities_for_line)), line))
        # # convert to dict
        mapping_dict = [m._asdict() for m in mappings]
        
        for i in mapping_dict:
            output_file.write(json.dumps(i, ensure_ascii=False))
            output_file.write("\n")


if __name__ == "__main__":
    
    input_dir = "output/additionally_non_simple"
    output_dir = "additionally_non_simple/"
   
   # get access to local SQL database
    path = os.path.abspath('data/DutchSnomedCT.sqlite3')

    if not os.path.exists(path):
        raise IOError(
            'Database %s not available.'
            % path)

    db = sql_module.connect(path, check_same_thread=False)
    process_files_in_folder(input_dir, output_dir)

