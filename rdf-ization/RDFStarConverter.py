import pandas as pd
from datetime import datetime
import re
from typing import List, Tuple, Iterable, Optional

class Prefixes:
    def __init__(self, sub_ns: str = "", ob_ns: str = "", prop_ns: str = ""): 
        self.sub_ns = sub_ns  
        self.ob_ns = ob_ns
        self.prop_ns = prop_ns 

    def qname_subject(self, token: str) -> str:
        return f"{self.sub_ns}{token}"

    def qname_object(self, token: str) -> str:
         return f"{self.ob_ns}{token}"

    def qname_property(self, token: str) -> str:
        return f"{self.prop_ns}{token}"

class Node:
    def n3(self) -> str: 
        raise NotImplementedError

class IRI(Node):
    def __init__(self, qname: str): self.qname = qname
    def n3(self) -> str:
        return self.qname

class Literal(Node):

    def __init__(self, value: str, tag: str = "@nl"): 

        self.value = value
        self.tag = tag
        
    def is_number(self, value: str):
        try:
            float(self.value)
            return 1

        except ValueError:
            return 0

    def n3(self):
        if self.is_number(self.value):
            s = float(self.value)
            return s
        else:
            s = self.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'\"{s}\"{self.tag}' 

class Triple:
    def __init__(self, s: Node, p: IRI, o: Node):
        self.s, self.p, self.o = s, p, o

    def n3(self) -> str: 
        return f"{self.s.n3()} {self.p.n3()} {self.o.n3()} ."

    def n3_embedded(self) -> str: 
        return f"<< {self.s.n3()} {self.p.n3()} {self.o.n3()} >>"

class RdfStarConverter:
    def __init__(self, prefixes: Prefixes, ann_prop_prefixes: list, ann_obj_prefixes: list = [], labels: object = None, types: object = None, ann_obj_types: list = [], skip_header: bool = True, tag: str = "@nl", schema_declarations = None):

        self.px = prefixes
        self.pxs_prop = ann_prop_prefixes
        self.pxs_obj = ann_obj_prefixes
        self.skip_header = skip_header
        self.types = types
        self.ts_types = ann_obj_types
        self.labels = labels
        self.tag = tag
        self.schema_declarations = schema_declarations

        # De-dup emitted metadata
        self._seen_types = set()
        self._seen_labels = set()
        self._labeled = set()  # which IRIs already got an rdfs:label
        self._typed = set()

    def convert_file(self, in_path: str) -> str:
        lines = self._read_lines(in_path)

        if self.skip_header and lines: lines = lines[1:]

        out: List[str] = []
        out.extend(self._prefix_block())

        if self.schema_declarations:
            out.extend(self.schema_declarations)

        for raw in lines:

            row = self._split_tsv(raw)
            if len(row) < 3: continue # check if triple

            # Main triple
            s = self._term_resource_or_literal(row[0], role = "subject")
            p = self._term_property(row[1])

            if self.px.ob_ns == "":
                o = self._term_resource_or_literal(row[2], role = "object", literal = True)
            else:
                o = self._term_resource_or_literal(row[2], role = "object")

            t = Triple(s, p, o)

            # rdf-ize the trple
            out.append(t.n3())

            # Ensure rdf:type for nodes/preds
            if self.types:
                out.extend(self._ensure_type(s, self.types[0]))
                #out.extend(self._ensure_type(p, self.types[ 1]))
                out.extend(self._ensure_type(o, self.types[1]))

            idx = 3
            # Optional labels: subject_label, object_label (only if the node is an IRI)
            if self.labels == "subject":
                subj_label  = row[3].strip()
                out.extend(self._ensure_label(s, subj_label))
                idx = 4
            
            elif self.labels == "object":
                obj_label  = row[3].strip()
                out.extend(self._ensure_label(o, obj_label))
                idx = 4

            elif self.labels == "both":
                subj_label = row[3].strip()
                obj_label  = row[4].strip()
                out.extend(self._ensure_label(s, subj_label))
                out.extend(self._ensure_label(o, obj_label))
                idx = 5

            elif self.labels == None:
                idx = 3

            else:
                raise ValueError("Please specify the labels in your file. Options are:\n -subject: only a subject label is given;\n -object: only an object label is given;\n -both: both subject and object labels are given;\n -None: no labels.")
            
            # Remaining cells are RDF★ annotation pairs: (ann_pred, ann_obj)
            if len(row) > idx:
                curr_idx = 0
                for ann_pred, ann_obj in self._pairs(row[idx:]):
                    # if one/both are nan, don't include the pair
                    
                    # Map to property prefixes
                    ap = self._star_term_property(curr_idx, ann_pred)

                    # check the kind of literal
                    ao = self._star_term_object(curr_idx, ann_obj)
                    #ao = Literal(ann_obj, lang_tag=self.lang_tag)
                    out.append(f"{t.n3_embedded()} {ap.n3()} {ao.n3()} .")

                    curr_idx += 1

        return "\n".join(out) + "\n"

    # ----- helpers -----
    def _prefix_block(self) -> List[str]:
        return [
            "@prefix dakikg: <http://w3id.org/dakikg#> .",
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix atc: <http://purl.bioontology.org/ontology/ATC/> .",
            "@prefix sct: <http://snomed.info/id/> .",
            "@prefix dcterms: <http://purl.org/dc/terms/> .",
            "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
            "",
        ]

    def _read_lines(self, path: str) -> List[str]:
        with open(path, "r", encoding="utf-8") as f:
            return [line.rstrip("\n\r") for line in f]

    def _split_tsv(self, line: str) -> List[str]:
        return [c.strip() for c in line.split("\t") if c.strip() != ""]

    def _term_property(self, token: str) -> IRI:
        return IRI(self.px.qname_property(self._strip_quotes(token)))
    
    def _star_term_property(self, idx, token: str) -> IRI:
        current_term_prop = Prefixes(prop_ns = self.pxs_prop[idx])
        return IRI(current_term_prop.qname_property(self._strip_quotes(token)))
    
    def _star_term_object(self, idx, token: str) -> Node:
    
        local_px = self.pxs_obj[idx]

        if local_px: # "" implies no prefix --> literal
            current_term_obj = Prefixes(ob_ns = self.pxs_obj[idx])
            return IRI(current_term_obj.qname_object(self._strip_quotes(token)))

        return self._term_resource_or_literal(token, role = "object", literal = True)

    def _term_resource_or_literal(self, token: str, role: str, literal: bool = False) -> Node:
        t = token.strip()

        # subject can never be a literal so first check for that
        if role == "subject": 
            # turn it into a strig (e.g. no .0)
            t = self._remove_floating_point(t)
            return IRI(self.px.qname_subject(self._strip_quotes(t))) # IRI for IDs

        # check if object is literal and what type
        if self._contains_special_characters(t):

            if self._is_date(t): # special case
                return Literal(t, tag="^^xsd:date")
                
            return Literal(t, tag=self.tag)

        if self._is_quoted(t):         
            return Literal(self._unquote(t), tag=self.tag)

        if self._contains_spaces(t):
            return Literal(t, tag=self.tag)
        
        if self._is_bool(t):
            return Literal(t, tag="^^xsd:boolean")

        if literal == True:
            return Literal(t, tag = self.tag)

        # if none, then return IRI
        if role == "object":          
            return IRI(self.px.qname_object(self._strip_quotes(t))) # IRI for IDs

    def _ensure_label(self, node: Node, label: str) -> List[str]:
        """Emit rdfs:label for an IRI node using the provided label (if non-empty)."""
        if not isinstance(node, IRI): 
            return []
        if not label: 
            return []
        q = node.qname
        if q in self._labeled: 
            return []
            
        return [self._emit_label(q, label)]

    def _ensure_type(self, node: Node, type: str) -> List[str]:
        """Emit rdf:type for an IRI node using the provided type (if non-empty)."""
        if not isinstance(node, IRI): 
            return []
        if not type: 
            return []
        q = node.qname
        if q in self._typed: 
            return []
            
        return [self._emit_type(q, type)]

    def _emit_label(self, qname: str, label: str) -> str:
        # escape quotes/backslashes/newlines in label
        s = label.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        self._labeled.add(qname)
        return f'{qname} rdfs:label "{s}"{self.tag} .'
    
    def _emit_type(self, qname: str, type: str) -> str:

        self._typed.add(qname)
        #pfx of type == px of entity we are typing
        pfx = qname.split(":")[0] + ":"
        return f'{qname} rdf:type {type} .'

    def _pairs(self, cells: List[str]) -> Iterable[Tuple[str, str]]:
        for i in range(0, len(cells) - 1, 2):
            yield cells[i], cells[i + 1]

    # --- tiny string utils ---
    def _is_quoted(self, s: str) -> bool: return len(s) >= 2 and s[0] == '"' and s[-1] == '"'

    def _contains_spaces(self, s: str) -> bool: return " " in s

    def _unquote(self, s: str) -> str: return s[1:-1]

    def _strip_quotes(self, s: str) -> str: return self._unquote(s) if self._is_quoted(s) else s
    
    def _is_date(self, s: str) -> bool: # checks for dcterms approved date format
        try:
            return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d") == s
        except ValueError:
            return False

    def _is_number(self, s) -> bool:
        try: float(s); return True
        except ValueError: return False
    
    def _is_bool(self, s) -> bool:
        return (s.lower() == "true") or (s.lower() == "false")
    
    def _contains_special_characters(self, t):
        return bool(re.search(r'[^a-zA-Z0-9\s]', t))
    
    def _remove_floating_point(self, t: float): 
        if self._is_number(t):
            return str(int(float(t)))
        return t