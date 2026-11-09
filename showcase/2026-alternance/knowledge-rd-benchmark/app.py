"""Moteur de recherche lexical et évaluation retrieval@k."""
import math,re
from collections import Counter
def tokens(txt):return re.findall(r"[a-zà-ÿ0-9]+",txt.lower())
def search(query, documents, k=3):
    corpus=[Counter(tokens(d["text"])) for d in documents]
    q=Counter(tokens(query));df=Counter(t for bag in corpus for t in bag)
    ranks=[]
    for d,bag in zip(documents,corpus):
        score=sum(q[t]*bag[t]*math.log(1+(len(corpus)+1)/(df[t]+1)) for t in q)
        ranks.append((score,d))
    return [d for score,d in sorted(ranks,key=lambda x:(-x[0],x[1]["id"]))[:k] if score>0]
def recall_at_k(questions,docs,k=3):
    if not questions: raise ValueError("Jeu d'évaluation vide")
    return sum(q["relevant_id"] in {d["id"] for d in search(q["question"],docs,k)} for q in questions)/len(questions)
if __name__=="__main__":
    docs=[{"id":"1","text":"Guide de maintenance Python et Linux"},
          {"id":"2","text":"CI CD tests de qualité logicielle"},
          {"id":"3","text":"Gouvernance des données et catalogues"}]
    qa=[{"question":"tests qualité logicielle","relevant_id":"2"}]
    print([d["id"] for d in search("tests qualité logicielle",docs)],recall_at_k(qa,docs))
