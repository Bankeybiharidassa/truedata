import pandas as pd
import spacy
from deep_translator import GoogleTranslator
import json


def extract_verbs():
    xl = pd.read_excel('category_tree_report.xlsx')
    cols = [c for c in xl.columns if c != 'Catid']
    nlp = spacy.load('nl_core_news_sm')
    texts = [str(val) for val in xl[cols].fillna('').values.flatten() if val]
    verbs = {}
    for doc in nlp.pipe(texts, batch_size=1000):
        for token in doc:
            if token.pos_ == 'VERB':
                lemma = token.lemma_.lower()
                entry = verbs.setdefault(lemma, {'lemma': lemma, 'nouns': set(), 'synonyms': set()})
                entry['nouns'].add(token.text.lower())
    verbs_nl = {k: {'lemma': v['lemma'], 'nouns': sorted(v['nouns']), 'synonyms': []} for k, v in verbs.items()}
    translator = GoogleTranslator(source='nl', target='en')
    verbs_en = {}
    for lemma in verbs_nl:
        try:
            trans = translator.translate(lemma)
        except Exception:
            trans = lemma
        verbs_en[trans] = {'lemma': trans, 'nouns': [], 'synonyms': []}
    with open('src/taxonomy/verbs_nl.json', 'w', encoding='utf-8') as f:
        json.dump(verbs_nl, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open('src/taxonomy/verbs_en.json', 'w', encoding='utf-8') as f:
        json.dump(verbs_en, f, ensure_ascii=False, indent=2, sort_keys=True)
    print('extracted', len(verbs_nl), 'verbs')


if __name__ == '__main__':
    extract_verbs()
