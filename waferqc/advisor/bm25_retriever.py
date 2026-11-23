import os
import glob
import re
import yaml
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

def tokenize(text: str) -> List[str]:
    """Simple lowercase regex tokenizer."""
    return [t.lower() for t in re.findall(r"\b\w+\b", text)]

class BM25SOPRetriever:
    """Retrieves relevant Standard Operating Procedures (SOPs) using BM25."""

    def __init__(self, sop_dir: str):
        self.sop_dir = sop_dir
        self.sops: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self._load_and_index()

    def _load_and_index(self):
        yaml_files = sorted(glob.glob(os.path.join(self.sop_dir, "*.yaml")))
        if not yaml_files:
            raise FileNotFoundError(f"No SOP YAML files found in {self.sop_dir}")

        for yf in yaml_files:
            with open(yf, "r", encoding="utf-8") as f:
                sop_data = yaml.safe_load(f)
                self.sops.append(sop_data)

                # Combine all searchable textual fields into document text
                doc_text = " ".join([
                    sop_data.get("sop_id", ""),
                    sop_data.get("title", ""),
                    sop_data.get("process_area", ""),
                    " ".join(sop_data.get("related_defect_classes", [])),
                    " ".join(sop_data.get("root_causes", [])),
                    " ".join(sop_data.get("checks", [])),
                    " ".join(sop_data.get("corrective_actions", []))
                ])
                tokens = tokenize(doc_text)
                self.corpus_tokens.append(tokens)

        self.bm25 = BM25Okapi(self.corpus_tokens)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top_k matching SOPs for a given query string."""
        query_tokens = tokenize(query)
        if not query_tokens:
            return self.sops[:top_k]

        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in ranked_indices[:top_k]:
            sop_copy = dict(self.sops[idx])
            sop_copy["bm25_score"] = float(scores[idx])
            results.append(sop_copy)
        return results

    def retrieve_for_defect(self, class_label: str, severity: str, area_px: int = 0, top_k: int = 3) -> List[Dict[str, Any]]:
        """Formulate domain query and retrieve relevant SOPs."""
        query = f"{class_label} defect {severity} area {area_px} px"
        return self.retrieve(query, top_k=top_k)
