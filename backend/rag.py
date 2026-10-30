"""Dependency-free TF-IDF retrieval over policy and loan clauses (English + Hindi)."""
import json
import math
import re
from pathlib import Path

CL = json.loads((Path(__file__).parent / "data/clauses.json").read_text(encoding="utf-8"))
STOP = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "what", "which", "who", "how", "when",
    "kya", "hai", "hain", "ka", "ki", "ke", "ko", "se", "me", "mein", "of", "for", "to", "in", "on",
    "and", "or", "please", "tell", "about", "covered", "cover", "kya-kya", "mujhe", "btao", "batao",
    "samjhao", "this", "that", "these", "those", "you", "your", "may", "can", "with", "from", "after",
    "only", "like", "treatment", "included", "year", "years", "per", "any", "them", "they", "their",
    "whole", "mean", "also", "into", "than", "then", "will", "just", "have", "has",
}
tok = lambda s: [t for t in re.findall(r"[\w\u0900-\u097F]+", s.lower()) if t not in STOP and len(t) > 1]
DOCS = [tok(f"{c['title']} {c['title']} {c['kw']} {c['en']} {c['hi']}") for c in CL]
N = len(DOCS)
DF: dict[str, int] = {}
for d in DOCS:
    for t in set(d):
        DF[t] = DF.get(t, 0) + 1
idf = lambda t: math.log((N + 1) / (DF.get(t, 0) + 1)) + 1


def score(q, d):
    if not q or not d:
        return 0.0
    overlap = set(q) & set(d)
    if not overlap:
        return 0.0
    if len(overlap) == 1:
        t = next(iter(overlap))
        if DF.get(t, 0) > 2 and len(t) < 8:
            return 0.0
    return sum(idf(t) * (1 + math.log(d.count(t))) for t in overlap) / math.sqrt(len(d))


def retrieve(query: str, plan: str | None = None, k: int = 2, threshold: float = 0.35):
    q = tok(query)
    ranked = sorted(
        ((score(q, DOCS[i]), CL[i]) for i in range(N) if not plan or CL[i]["plan"] == plan),
        key=lambda x: -x[0],
    )
    return [dict(c, score=round(s, 2)) for s, c in ranked[:k] if s >= threshold]
