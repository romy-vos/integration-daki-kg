import sqlite3 
import os

path = os.path.abspath('data/DutchSnomedCT.sqlite3')

if not os.path.exists(path):
    raise IOError(
        'Database %s not available.'
        % path)

db_connection = sqlite3.connect(path, check_same_thread=False)

def create_table():
    """ We create a new table, ConceptCategories, which finds all descendants of "clinical finding", which are the PT and active. 
    We also add a column which shows the depth: how many steps the concept is from the root ( = clinical finding).
    """

    cursor = db_connection.cursor()
    
    # Drop the table if it exists and create a fresh one
    cursor.execute("DROP TABLE IF EXISTS ConceptCategories;")
    
    # Create the ConceptCategories table with an additional depth column
    cursor.execute("""
    CREATE TABLE ConceptCategories (
        conceptId INTEGER PRIMARY KEY,
        category TEXT NOT NULL,
        depth INTEGER NOT NULL
    );
    """)
    
    db_connection.commit()

def classify_clinical_findings_by_depth():

    depth = 1  # Start at depth = 1
    
    # Initial step: Find all direct children of Clinical Finding (depth 1)
    cursor = db_connection.cursor()
    
    cursor.execute("""
    INSERT OR REPLACE INTO ConceptCategories (conceptId, category, depth)
    SELECT sourceId, 'clinical finding', 1
    FROM Relationship
    WHERE destinationId = '404684003'  -- "Clinical Finding" concept in SNOMED
        AND typeId = '116680003';  -- "is_a" relation in SNOMED
    """)
    db_connection.commit()

    # Print initial count of classified concepts
    cursor.execute("""
    SELECT COUNT(*) FROM ConceptCategories 
    WHERE category = 'clinical finding' AND depth = 1;
    """)
    classified_count = cursor.fetchone()[0]
    print(f"Depth {depth}: {classified_count} clinical findings classified")

    while True:
        # Find all direct children of the concepts at the current depth level
        cursor.execute("""
        INSERT OR REPLACE INTO ConceptCategories (conceptId, category, depth)
        SELECT r.sourceId, 'clinical finding', ?
        FROM Relationship r
        INNER JOIN ConceptCategories c ON r.destinationId = c.conceptId
        WHERE c.depth = ? AND r.typeId = '116680003';
        """, (depth + 1, depth))
        db_connection.commit()

        # Check how many new categories were inserted at this depth level
        cursor.execute("""
        SELECT COUNT(*) FROM ConceptCategories 
        WHERE category = 'clinical finding' AND depth = ?;
        """, (depth + 1,))
        new_classified_count = cursor.fetchone()[0]

        # Print the classified count for this depth level
        print(f"Depth {depth + 1}: {new_classified_count} clinical findings classified")

        # If no new categories were inserted, stop the loop (end of recursion)
        if new_classified_count == classified_count:
            print(f"No new concepts found at depth {depth + 1}. Stopping the process.")
            break
        
        # Update the classified count for the next iteration
        classified_count = new_classified_count
        depth += 1  # Increment depth and process the next level

# Create the table (if it doesn't exist) and start the classification process for clinical findings
create_table()
classify_clinical_findings_by_depth()

# Close the database connection after the process is complete
db_connection.close()

