import json
import re
import pathlib

HERE = pathlib.Path(__file__).parent
EN = json.loads((HERE / "verbs_en.json").read_text("utf-8"))
NL = json.loads((HERE / "verbs_nl.json").read_text("utf-8"))

BASIC_EN_SYNONYMS = {
    "fasteners": ["screw", "bolt", "nut"],
    "laptop": ["notebook", "computer"],
    "printer": ["laser", "inkjet"],
}

BASIC_NL_SYNONYMS = {
    "bevestigers": ["schroef", "bout", "moer"],
    "laptop": ["notebook", "computer"],
    "printer": ["laser", "inkjet"],
}

def tokenize(text: str):
    return re.findall(r"[a-z0-9]+", (text or "").lower())

def detect_lang(tokens):
    nl_sw = {"de", "het", "een", "en", "voor", "met", "op", "onder", "boven"}
    return "nl" if any(t in nl_sw for t in tokens) else "en"

def expand_tokens(tokens):
    lang = detect_lang(tokens)
    out = set(tokens)
    maps = (EN, BASIC_EN_SYNONYMS) if lang == "en" else (NL, BASIC_NL_SYNONYMS)

    verbmap, basemap = maps
    for t in list(out):
        base = t[:-1] if t not in verbmap and t.endswith("s") and t[:-1] in verbmap else t
        if base != t:
            out.discard(t)
            out.add(base)
        if base in verbmap:
            v = verbmap[base]
            out.add(v["lemma"])
            out.update(v.get("nouns", []))
            out.update(v.get("synonyms", []))
    for t in list(out):
        base = t[:-1] if t.endswith("s") and t[:-1] in basemap else t
        if base != t:
            out.discard(t)
            out.add(base)
        out.update(basemap.get(base, []))
    return list(dict.fromkeys(out))

def build_queries(subject: str, max_terms=6):
    tokens = tokenize(subject)
    expanded = expand_tokens(tokens)
    expanded.sort(key=len, reverse=True)
    for orig in tokens:
        base = orig[:-1] if orig.endswith("s") else orig
        if base in expanded:
            expanded.remove(base)
            expanded.insert(0, base)
    queries = []
    for k in range(min(max_terms, len(expanded)), 0, -1):
        q = " ".join(expanded[:k])
        if q not in queries:
            queries.append(q)
    return queries
