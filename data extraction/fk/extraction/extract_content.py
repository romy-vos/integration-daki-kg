from bs4 import BeautifulSoup
import requests
import os
from datetime import datetime
import re

def extract_atc(soup):
    """ Extract ATC from web page. ATC can be found directly under the title (h1) with class= "byline-item". """

    bylines = soup.findAll(class_ = "byline-item")
    atc = bylines[1].text
    return atc

def extract_title(soup):
    """ Extract title from web page. """

    main_content = soup.find(id = "main-content")
    title = main_content.find("h1").text
    title = title.replace("/", "-")
    return title

def get_section_content(soup, subsection_id):

    subsection = soup.find(id = subsection_id)
    return subsection

def remove_external_links(content):

    for link_list in content.find_all("ul", class_="link-list"):

        #  remove the title of the linked list
        previous_sibling = link_list.find_previous_sibling()
        if previous_sibling and previous_sibling.name == "h3":
            previous_sibling.decompose()

        # and remove the actual list
        link_list.decompose()
    return content

def remove_inline_tags(html_content):

    for tag in html_content.find_all(['i', 'em', 'b']):
        if tag:
            tag.replace_with(tag.get_text())
    return html_content


def remove_title(content):

    title = content.find("h2")
    title.decompose()
    return content

def remove_dosage(content):
    """ mg is also a disease --> to prevent confusion during the mapping process we replace it with the full word. """

    pattern = r"([0-9]+)[ \t]*mg"
    matches = re.findall(pattern, content)

    if matches:

        filtered_text = re.sub(pattern, r"\1 milligram", content)
        return filtered_text
    return content

def filter_content_on_html_tag(subsection):

    # remove links to other internal pages (e.g. related diseases) and external pages
    subsection = remove_external_links(subsection)
    subsection = remove_title(subsection)
    subsection = remove_inline_tags(subsection)
    return subsection

def write_content_to_file(content, output_path):

    lines = []
    for line in content.splitlines():
        stripped_line = line.strip()
        if stripped_line:  # Avoid blank lines
            lines.append(stripped_line)
    cleaned_content = "\n".join(lines)

    cleaned_content_filtered = remove_dosage(cleaned_content)

    with open(output_path + ".txt", "w") as file:

        file.write(cleaned_content_filtered)


def parse_h4_content(subsection, output_path):

    # Find all h4 headers and content
    h4_headers = subsection.find_all("h4")
    
    # Find introductory content (everything before the first <h4>)
    intro_content = ""
    if h4_headers:
        for tag in subsection.find_all(True):  # Find all tags
            if tag == h4_headers[0]:  # Stop at the first <h4>
                break

            intro_content += tag.get_text().strip()

        if intro_content:
            updated_path_intro = output_path + "_" + "Algemeen"
            write_content_to_file(intro_content, updated_path_intro)
    

    # Iterate over all h4 headers to create separate files
    for i, h4 in enumerate(h4_headers):
        # Collect content for this h4 section

        section_content = ""
        current = h4
        while current.next_sibling:
            current = current.next_sibling

            if current.name == "h4":  # stop at the next <h4>
                break
            if current.name:
                section_content += current.get_text().strip() + "\n" # add \n to seperate paragraphs to a new line since we process line by line in this case

        # Write this section to a separate file
        h4_title = h4.get_text().replace("/", "_").strip()

        updated_path = output_path + "_" + h4_title

        if len(str(updated_path)) > 256: # max allowed file name length
            updated_path = updated_path[0:256]
            
        write_content_to_file(section_content, updated_path)



def parse_content(subsection, output_path):

    # Extract all the text cleanly
    text = subsection.get_text().strip()
    write_content_to_file(text, output_path)


def extract(soup, entity_type, url, output_dir_atc, output_file, title, today):

    all_types = ["indication", "contraindication", "adverseevent"]

    if entity_type == "indication":
        subsection_id = "indicaties"

    elif entity_type == "contraindication":
        subsection_id = "contra-indicaties"

    elif entity_type == "adverseevent":
        subsection_id = "bijwerkingen"

    elif entity_type == "all":

        for i in all_types:
            # recursive loop over all types to extract all entities for a drug
            extract(soup, i, url, output_dir_atc, output_file, title, today)
        return
    
    else:
        print(f"Oops, it seems you entered an incorrect entity type. The options are: {all_types}.")
        return
    
    output_path = os.path.join(output_dir_atc, output_file + "-" + title + "_" + subsection_id + "_" + today)
 
    if os.path.isfile(output_path + ".txt"):
        print(f"Oops, this is already extracted for {output_path}. We skip this one.")
        return

    subsection = get_section_content(soup, subsection_id)

    if not subsection:
        print(f"Oops, the section {entity_type} does not exist for {output_dir_atc}.")
        return 

    subsection = filter_content_on_html_tag(subsection) # remove the html tags we are not interested in
    
    if subsection.find_all("h4"):
        parse_h4_content(subsection, output_path)

    else:
        parse_content(subsection, output_path)

def start_extraction(urls):

    today = datetime.today().strftime('%d-%m-%Y') # day month year

    for url in urls:

        print("....extracting from url....", url)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html5lib")
        atc = extract_atc(soup)
        title = extract_title(soup)

        output_dir = "additionally_non_simple"
        output_dir_atc = os.path.join(output_dir, atc)

        # check if dir exists, otherwise make it
        if not os.path.exists(output_dir_atc):
            os.makedirs(output_dir_atc)
            print(f"Made new directory for {atc}.")

        extract(soup, entity_type, url, output_dir_atc, atc, title, today)


if __name__ == "__main__":

    #url_file = 'DDI_in_fk.txt'
    #url_file = 'DDI_in_fk_additionally_simple.txt'
    url_file = 'DDI_in_fk_additionally_non_simple.txt'

    with open(url_file, 'r') as file:

        urls = file.read().splitlines()
        entity_type = "all" # all = indications, contra-indications, side effects

        start_extraction(urls)
            
        