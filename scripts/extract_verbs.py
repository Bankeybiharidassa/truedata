import pandas as pd
import spacy
import json
from transformers import MarianMTModel, MarianTokenizer


def extract_verbs():
    xl = pd.read_excel('category_tree_report.xlsx')
    cols = [c for c in xl.columns if c != 'Catid']
    nlp = spacy.load('nl_core_news_sm')
    texts = [str(val) for val in xl[cols].fillna('').values.flatten() if val]
    verbs = {}
    for doc in nlp.pipe(texts, batch_size=1000):
        for token in doc:
            if token.is_alpha:
                lemma = token.lemma_.lower()
                entry = verbs.setdefault(lemma, {'lemma': lemma, 'nouns': set(), 'synonyms': set()})
                entry['nouns'].add(token.text.lower())
    verbs_nl = {k: {'lemma': v['lemma'], 'nouns': sorted(v['nouns']), 'synonyms': []} for k, v in verbs.items()}
    tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-nl-en")
    model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-nl-en")
    def translate_words(words, batch_size=32):
        out = []
        words = list(words)
        for i in range(0, len(words), batch_size):
            batch_words = words[i:i + batch_size]
            batch = tokenizer(batch_words, return_tensors="pt", padding=True)
            gen = model.generate(**batch, max_new_tokens=40, num_beams=1)
            out.extend([tokenizer.decode(g, skip_special_tokens=True).lower() for g in gen])
        return out

    verbs_en = {}
    lemmata = list(verbs_nl)
    translations = translate_words(lemmata)
    for lemma, trans in zip(lemmata, translations):
        verbs_en[trans] = {"lemma": trans, "nouns": [], "synonyms": []}

    overrides_nl = {
        "boren": {"nouns": ["boor", "kolomboor", "accuboormachine"], "synonyms": ["gat", "boring"]},
        "schroeven": {"nouns": ["schroef", "bout", "bevestiger"], "synonyms": ["vastzetten"]},
        "zagen": {"nouns": ["zaag", "handzaag", "decoupeerzaag"], "synonyms": ["afzagen", "snijden"]},
        "schuren": {"nouns": ["schuurmachine", "schuurpapier"], "synonyms": ["gladmaken", "polijsten"]},
        "verven": {"nouns": ["verf", "kwast", "roller"], "synonyms": ["schilderen", "coaten"]},
    }
    overrides_en = {
        "drill": {"lemma": "drill", "nouns": [], "synonyms": []},
        "screw": {"lemma": "screw", "nouns": ["screw", "bolt", "fastener"], "synonyms": []},
        "saw": {"lemma": "saw", "nouns": ["handsaw", "jigsaw"], "synonyms": []},
        "paint": {"lemma": "paint", "nouns": ["brush", "roller"], "synonyms": []},
    }

    for lemma, data in overrides_nl.items():
        entry = verbs_nl.setdefault(lemma, {"lemma": lemma, "nouns": [], "synonyms": []})
        entry["nouns"] = sorted(set(entry.get("nouns", [])) | set(data["nouns"]))
        entry["synonyms"] = sorted(set(entry.get("synonyms", [])) | set(data["synonyms"]))
    for lemma, data in overrides_en.items():
        verbs_en[lemma] = data
    verbs_en.pop("screws", None)
    with open('src/taxonomy/verbs_nl.json', 'w', encoding='utf-8') as f:
        json.dump(verbs_nl, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open('src/taxonomy/verbs_en.json', 'w', encoding='utf-8') as f:
        json.dump(verbs_en, f, ensure_ascii=False, indent=2, sort_keys=True)
    print('extracted', len(verbs_nl), 'verbs')


if __name__ == '__main__':
    extract_verbs()
