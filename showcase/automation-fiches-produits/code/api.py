"""API démonstrative non authentifiée. Ne pas exposer publiquement sans protection."""
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from .scraper import scrape_local
from .llm_enrichment import enrich
from .storage import store
from .bot_handler import Support
app=FastAPI(title="Envie — démo automatisation")
bot=Support()
class Product(BaseModel):
    produit_id:str
    nom:str
    marque:str=""
    description:str=""
    etat:str="moyen"
    defauts_declares:str="aucun"
    prix_reference_eur:float=Field(ge=0)
    use_llm:bool=False
class Message(BaseModel):
    question:str=Field(min_length=1,max_length=600)
    use_llm:bool=False
@app.get("/health")
def health():return {"status":"ok"}
@app.get("/api/scrape-demo")
def scrape():
    return scrape_local(Path(__file__).resolve().parents[1]/"examples/exemple_fiche.html")
@app.post("/api/enrich")
def enrichment(req:Product):
    item=req.model_dump()
    llm=item.pop("use_llm")
    return enrich(item,use_llm=llm)
@app.post("/api/store")
def save(x:dict):
    if "produit_id" not in x:raise HTTPException(422,"produit_id absent")
    store(x)
    return {"stored":True}
@app.post("/api/support")
def sav(m:Message):return bot.respond(m.question,m.use_llm)
