"""
Indexes the corpus of procgen papers using sentence-transformers embeddings.

The vector search approach is cleaner than a "librarian agent" because it's
deterministic and fast. Rather than having an LLM guess which document is
relevant, we compute semantic similarity directly.

Supports incremental indexing:
- Drop new papers in ./corpus/
- Run this script
- New papers get embedded and moved to ./corpus/indexed/
- Only new papers are processed, not the entire corpus
"""

import json
import pickle
import shutil
from pathlib import Path
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed.")
    print("Run: pip install sentence-transformers")
    exit(1)

CORPUS_DIR = Path(__file__).resolve().parents[4] / "corpus"
INDEXED_DIR = CORPUS_DIR / "indexed"
INDEX_PATH = Path(__file__).resolve().parents[4] / ".claude" / "rlm_state" / "corpus_index.pkl"
MODEL_NAME = "multi-qa-MiniLM-L6-dot-v1"

def load_existing_index():
    if INDEX_PATH.exists():
        with open(INDEX_PATH, "rb") as f:
            return pickle.load(f)
    return None

def get_new_documents():
    new_docs = []
    for fpath in CORPUS_DIR.glob("*.txt"):
        content = fpath.read_text(encoding="utf-8", errors="ignore")
        new_docs.append({
            "original_path": fpath,
            "filename": fpath.name,
            "content": content,
            "preview": content[:500]
        })
    return new_docs

def move_to_indexed(doc):
    INDEXED_DIR.mkdir(parents=True, exist_ok=True)
    src = doc["original_path"]
    dest = INDEXED_DIR / doc["filename"]
    shutil.move(str(src), str(dest))
    return str(dest)

def create_index():
    existing_index = load_existing_index()
    new_docs = get_new_documents()

    if not new_docs and not existing_index:
        print(f"No documents found in {CORPUS_DIR}")
        print("Add .txt files to get started.")
        return

    if not new_docs:
        print("No new documents to index.")
        print(f"Existing index has {len(existing_index['documents'])} documents.")
        return

    print(f"Found {len(new_docs)} new document(s) to index")
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    texts = [d["content"] for d in new_docs]
    print("Computing embeddings...")
    new_embeddings = model.encode(texts, show_progress_bar=True)

    for i, doc in enumerate(new_docs):
        indexed_path = move_to_indexed(doc)
        new_docs[i]["path"] = indexed_path
        del new_docs[i]["original_path"]
        del new_docs[i]["content"]

    if existing_index:
        all_docs = existing_index["documents"] + new_docs
        all_embeddings = np.vstack([existing_index["embeddings"], new_embeddings])
        print(f"Merged with existing index: {len(existing_index['documents'])} + {len(new_docs)} = {len(all_docs)} total")
    else:
        all_docs = new_docs
        all_embeddings = new_embeddings

    index = {
        "model": MODEL_NAME,
        "documents": all_docs,
        "embeddings": all_embeddings
    }

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(index, f)

    print(f"Index saved to: {INDEX_PATH}")
    print(f"Total indexed: {len(all_docs)} documents")

    manifest_path = INDEX_PATH.parent / "corpus_manifest.json"
    manifest = [{"filename": d["filename"], "path": d["path"], "preview": d["preview"]} for d in all_docs]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to: {manifest_path}")

if __name__ == "__main__":
    create_index()
