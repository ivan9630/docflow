"""Contrôles indépendants sur un scénario fictif équivalent aux données SAS.
Ne remplace pas l'exécution du programme SAS lui-même."""
actions=[
 (101,'ACC','REALISEE'),(102,'ATEL','REALISEE'),(103,'FORM','PREVUE'),
 (104,'ACC','REALISEE'),(105,'ATEL','ANNULEE'),(106,'FORM','REALISEE'),
 (107,'ACC','REALISEE'),(108,'ATEL','REALISEE'),(109,'FORM','PREVUE'),(110,'ACC','REALISEE')
]
suivis=[(1,101,1),(2,101,0),(3,102,1),(4,104,1),(5,106,0),
        (6,106,1),(7,107,1),(8,108,1),(9,110,0),(10,110,1)]
assert len(set(x[0] for x in actions))==len(actions)
assert all(x[1] in {a[0] for a in actions} for x in suivis)
planned=sum(status!='ANNULEE' for _,_,status in actions)
done=sum(status=='REALISEE' for _,_,status in actions)
followup=sum(s for _,_,s in suivis)
assert (planned,done,len(suivis),followup)==(9,7,10,7)
assert 0<=done/planned<=1 and 0<=followup/len(suivis)<=1
print(f"Contrôles OK | actions {done}/{planned} | suivis {followup}/{len(suivis)}")
