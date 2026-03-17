# Dataset DocuFlow v2

## Résumé
Ce dataset contient **60 documents synthétiques** générés pour tester la pipeline DocuFlow v2 :
- OCR
- classification documentaire
- extraction d'entités
- vérifications de cohérence
- détection de fraude

## Répartition par type
- **attestation_urssaf** : 13
- **devis** : 10
- **facture** : 25
- **kbis** : 6
- **rib** : 6

## Répartition par scénario
- **expiree** : 5
- **fake_amounts** : 5
- **fake_siret** : 5
- **legitime** : 15
- **standard** : 22
- **valide** : 8

## Documents suspects / frauduleux attendus
- **Nombre total attendu** : 15

### Scénarios de fraude inclus
- factures avec **SIRET invalide**
- factures avec **montants HT / TVA / TTC incohérents**
- attestations URSSAF **expirées**

## Dégradations simulées
Les documents ont été dégradés pour simuler des scans ou photos smartphone :
- rotation aléatoire entre **5° et 15°**
- flou gaussien
- bruit gaussien
- bruit sel / poivre
- faible résolution
- variations légères de contraste / luminosité
- compression JPEG pour certains fichiers

### Répartition des niveaux
- **clean** : 10
- **medium** : 26
- **hard** : 24

## Structure du dossier
- `images/` : documents rendus en PNG / JPG
- `texts/` : texte source utilisé pour fabriquer le document
- `labels/` : annotations JSON document par document
- `metadata/manifest.json` : index complet du dataset
- `README.md` : documentation du dataset

## Format des labels
Chaque fichier `labels/DOC-XXXX.json` contient notamment :
- `doc_id`
- `doc_type`
- `variant`
- `expected_class`
- `expected_fraud`
- `fraud_reasons`
- les champs métier attendus (SIREN, SIRET, montants, dates, IBAN, etc.)
- `degradation_level`
- `degradations_applied`
- `group_member_names_used`

## Personnalisation avec les noms du groupe
Les noms suivants ont été injectés dans certains champs :
- signataires
- responsables dossier
- conseillers commerciaux
- représentants légaux
- interlocuteurs / titulaires de compte

**Noms utilisés** :
Jules Araud, James MBA FONGANG, Mathieu CHRETIEN, Boubaker OMRI, Romain PINTRE, Ivan Noël, Hajar MOUSSAOUI, David CIRAKAZA

## Notes
- Les documents sont **synthétiques** et destinés au test / démonstration.
- Les données sont plausibles mais ne correspondent pas à des pièces officielles réelles.
- Les annotations servent de **ground truth** pour évaluer les résultats OCR et IA.
