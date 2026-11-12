import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
KB=Path(__file__).resolve().parents[1]/"data/base_connaissances.json"
class Knowledge:
    def __init__(self):
        self.docs=json.loads(KB.read_text(encoding="utf-8"))
        self.v=TfidfVectorizer(strip_accents="unicode")
        self.m=self.v.fit_transform([d["title"]+" "+d["text"] for d in self.docs])
    def search(self,q,k=2):
        scores=cosine_similarity(self.v.transform([q]),self.m)[0]
        return [self.docs[i] for i in scores.argsort()[::-1][:k]]
