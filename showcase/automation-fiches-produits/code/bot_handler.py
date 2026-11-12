import os,json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
FAQ=Path(__file__).resolve().parents[1]/"data/faq_sav.json"
class Support:
    def __init__(self):
        self.items=json.loads(FAQ.read_text(encoding="utf-8"))
        self.vec=TfidfVectorizer(strip_accents="unicode")
        self.matrix=self.vec.fit_transform([i["question"]+" "+i["intent"] for i in self.items])
    def respond(self,question,use_llm=False):
        if any(x in question.lower() for x in ("surchauffe","fumée","étincelles","câble abîmé")):
            return {"intent":"securite","reponse":"Arrêtez d'utiliser l'appareil et contactez un professionnel ou le SAV.","escalade":True}
        scores=cosine_similarity(self.vec.transform([question]),self.matrix)[0]
        ix=int(scores.argmax());score=float(scores[ix])
        if score<0.30:return {"intent":"inconnu","reponse":"Question transmise à un conseiller SAV.","escalade":True}
        faq=self.items[ix]
        answer={"intent":faq["intent"],"reponse":faq["reponse"],"escalade":faq["escalade"],"source":faq["id"]}
        if use_llm:
            from openai import OpenAI
            if not os.getenv("OPENAI_API_KEY"):raise RuntimeError("OPENAI_API_KEY requis")
            res=OpenAI().responses.create(model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"),input=[
             {"role":"system","content":"Reformuler uniquement le texte SAV vérifié sans inventer de conditions de garantie ni de procédure dangereuse."},
             {"role":"user","content":json.dumps({"question":question,"texte_valide":faq["reponse"]},ensure_ascii=False)}])
            answer["reponse_llm"]=res.output_text[:600]
        return answer
