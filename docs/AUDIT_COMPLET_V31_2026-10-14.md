# Audit complet SeaMat 3.1

Date : 14 octobre 2026

## Conclusion

SeaMat 3.1 est fonctionnel pour un usage local de recherche et de présélection. Aucun défaut bloquant n'a été détecté dans la suite actuelle. La qualité logicielle est bonne, mais la qualification scientifique reste limitée par le nombre de domaines possédant des cinétiques indépendantes. Le logiciel ne doit donc pas être présenté comme précis à 95 % pour tous les matériaux.

## Vérifications exécutées

| Contrôle | Résultat |
|---|---:|
| Tests Python | 178 réussis sur 178 |
| Modules importés et compilés | 28 sur 28 |
| Dépendances Python | aucune incompatibilité détectée |
| Pages testées en bureau | 16 sur 16, aucune erreur navigateur |
| Pages testées en mobile | 16 sur 16, aucun débordement horizontal |
| Points d'API testés | 13 sur 13 |
| Matériaux inconnus | rejet HTTP 404 conforme |
| Catalogue | 75 identifiants uniques |
| Intégrité SQLite | OK, clés étrangères actives |
| Parcours interactifs | simulation, paramètres avancés, comparaison et menu Ressources opérationnels |
| Recherche Crossref | 8 résultats retournés, pertinence perfectible |
| Charge 30 utilisateurs | 90 requêtes, 0 erreur, p95 3,67 s |
| Charge 100 utilisateurs | 300 requêtes, 0 erreur, p95 8,50 s |

## Couverture scientifique constatée

| Niveau | Nombre de matériaux | Interprétation |
|---|---:|---|
| Corpus prêt pour benchmark | 1 | PP, validation interne hors formulation |
| Preuve limitée | 1 | IIR, courbes exactes mais transfert thermique refusé |
| Fiche documentaire seulement | 73 | scénario calculable, sans précision expérimentale démontrée |

Les 43 observations publiées vérifiées alimentent les routes PP et IIR. Les 21 profils fabricants renseignent des valeurs initiales mais ne déterminent pas une cinétique. Le statut « 0 observation acceptée » concerne les contributions utilisateur passées par la revue ; son libellé doit être clarifié dans l'interface pour ne pas être confondu avec les 43 preuves publiées.

## Corrections recommandées

### Priorité 1 avant une bêta publique

1. Mettre en cache le catalogue, la couverture et les audits, avec invalidation lors d'une revue de données. Cible : p95 inférieur à 2 s avec 30 utilisateurs.
2. Distinguer explicitement l'état local, l'état pilote et l'état institutionnel. L'API `/health/readiness` renvoie actuellement `ready` alors que `institution_ready` est faux.
3. Ajouter un test automatique de restauration d'une sauvegarde complète, puis vérifier la base et les documents restaurés.
4. Renommer les compteurs de données : « contributions utilisateur acceptées » et « observations publiées vérifiées ».
5. Ajouter des tests directs pour `deployment`, `literature`, `document_ui` et `prediction_quality`, même si ces fonctions sont déjà exercées indirectement.

### Priorité 2 pour un pilote en école

1. Ajouter une suite navigateur en intégration continue pour les parcours étudiant et enseignant, sur bureau, tablette et mobile.
2. Ajouter une mesure de couverture de code. Cible : au moins 85 % sur le moteur scientifique et 70 % sur l'ensemble du projet.
3. Exposer une documentation d'API versionnée. `/openapi.json` est actuellement capturé par l'interface HTML.
4. Améliorer la recherche bibliographique : filtres article scientifique, propriété, matériau, environnement, accès ouvert et tri par pertinence.
5. Déployer PostgreSQL, stockage objet, SSO institutionnel, HTTPS, supervision, quotas et journalisation structurée.
6. Tester les lanceurs macOS et Windows dans la chaîne de publication, en plus de la matrice Python déjà présente.

### Priorité 3 pour la qualification scientifique

1. Construire un corpus par domaine matériau, grade, environnement et horizon avec plusieurs laboratoires.
2. Geler le modèle et les intervalles avant chaque validation externe.
3. Réserver des groupes complets pour le test ; ne jamais séparer aléatoirement des points d'une même courbe.
4. Comparer chaque expert à des références simples et refuser tout modèle qui ne les dépasse pas.
5. Calibrer les intervalles par domaine et publier simultanément MAPE, RMSE, erreur maximale, couverture, largeur et taux de refus.
6. Pour une revendication 95/95 sans échec, viser au moins 59 groupes externes indépendants entièrement couverts dans le domaine annoncé.
7. Ajouter une validation dédiée aux familles prioritaires : polyoléfines, polymères hydrolysables, thermodurcissables, élastomères, composites et matériaux haute stabilité.

## Critères de sortie

### Version bêta publique

- 178 tests actuels maintenus et nouveaux tests directs ajoutés.
- p95 inférieur à 2 s pour 30 utilisateurs.
- sauvegarde et restauration testées.
- aucune ambiguïté entre données documentaires, observations publiées et contributions acceptées.
- zéro erreur navigateur sur les parcours principaux.

### Pilote école

- accès HTTPS et identité institutionnelle ;
- PostgreSQL et stockage durable ;
- supervision et alertes ;
- restauration répétée avec succès ;
- test réel d'une classe complète pendant une séance.

### Modèle scientifiquement qualifié

- domaine d'emploi déclaré ;
- jeu externe indépendant ;
- modèle et bornes gelés ;
- performance et couverture conformes au seuil fixé ;
- limites et taux de refus publiés.

## Décision actuelle

SeaMat peut être utilisé pour l'enseignement, la présélection, la comparaison et la préparation d'essais. Les résultats PP dans la fenêtre publiée sont correctement reproduits. Le transfert IIR non fiable est correctement refusé. Pour les 73 autres matériaux, le fonctionnement informatique est démontré, mais la précision scientifique reste à établir domaine par domaine.
