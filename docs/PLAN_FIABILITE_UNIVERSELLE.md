# Plan de fiabilité universelle SeaMat

## Définition réaliste

La fiabilité universelle ne signifie pas qu'une même loi peut prévoir tous les matériaux sans données. Elle signifie que chaque matériau passe par le même contrat, les mêmes critères d'erreur et la même décision d'usage. Quand les preuves manquent ou échouent, SeaMat doit répondre « non qualifié » au lieu de transformer une courbe documentaire en résultat fiable.

## Règle commune mise en production

La porte `seamat-reliability-gate-1.0.0` applique à chaque résultat :

- au moins six prédictions réellement masquées ;
- MAPE inférieure ou égale à 10 % ;
- erreur relative maximale inférieure ou égale à 20 % ;
- couverture entre 80 et 100 % pour la bande calculée ;
- horizon entièrement compris dans la fenêtre publiée ;
- séparation des validations internes et des sources externes indépendantes ;
- exclusion des fiches documentaires de tout usage de durée de vie.

La qualification externe exige en plus au moins deux sources indépendantes et une correspondance documentaire d'au moins 80/100.

## États possibles

1. **Fiabilité démontrée dans le domaine publié** : critères numériques, domaine, correspondance et indépendance satisfaits.
2. **Fiabilité interne** : erreurs faibles dans une publication ou un corpus interne ; usage de présélection seulement.
3. **Profil publié exact** : lecture/interpolation aux conditions exactes, sans preuve prédictive indépendante.
4. **Non qualifié — extrapolation** : horizon après la dernière observation.
5. **Non qualifié — validation insuffisante** : erreur, couverture ou nombre de tests insuffisant.
6. **Non qualifié — données absentes** : fiche et module initial disponibles, mais aucune cinétique compatible.

## Ce qui est appliqué dans SeaMat 2.2

- décision de fiabilité attachée à chaque résultat et à son empreinte ;
- message principal du simulateur adapté à l'usage autorisé ;
- suppression de la formulation « estimation à retenir » pour les résultats non qualifiés ;
- statut, décision et version de la porte dans les exports Markdown, PDF, Excel et JSON ;
- API `/api/v2/coverage` pour les 75 matériaux ;
- API `/api/v2/coverage/{material_id}` pour le manque de points, d'expériences et de sources ;
- tests PP, IIR, extrapolation et repli documentaire ;
- séparation entre moteur numérique et porte de publication scientifique.

## Programme de données à appliquer à chaque matériau

### Étape 1 — Identité

Définir polymère, grade, formulation, charges, stabilisants, procédé, cristallinité, lot, géométrie et conditionnement. Une fiche de famille seule ne suffit pas.

### Étape 2 — Conditions et propriété

Conserver norme, vitesse d'essai, température de mesure, module initial, milieu, température, humidité, UV ou liquide, épaisseur, oxygène et cycles.

### Étape 3 — Corpus minimal

Réunir au moins douze points répartis sur trois séries temporelles. Chaque série comporte le temps initial et au moins deux temps vieillis. Les valeurs moyennes, répétitions et dispersions restent séparées.

### Étape 4 — Indépendance

Obtenir au moins deux sources, grades, lots ou laboratoires réellement indépendants. Une source complète est gelée et n'intervient ni dans le choix du modèle ni dans le réglage de la bande.

### Étape 5 — Modèle physique admissible

Comparer exponentiel, Weibull, plateau et modèle propre au mécanisme. Arrhenius n'est autorisé que si le mécanisme reste identique. Les composites hygroscopiques utilisent une route diffusion–saturation ou biphasique. Les réponses non monotones ne sont pas forcées dans une loi décroissante.

### Étape 6 — Validation imbriquée

Masquer successivement une formulation, une température, un lot, une source puis la source externe gelée. Publier MAE, MAPE, erreur maximale, biais, couverture et erreur sur le temps au seuil.

### Étape 7 — Bande prédictive

Calibrer la bande par couple matériau–milieu–protocole. Ajouter la dispersion publiée, l'erreur hors groupe, la pénalité de transfert et l'extrapolation. Aucune largeur uniforme n'est acceptée.

### Étape 8 — Domaine

Enregistrer les limites de température, humidité, épaisseur, milieu, grade et temps. Toute requête hors domaine devient automatiquement non qualifiée.

### Étape 9 — Publication

Geler données, code, paramètres, version, empreinte et jeu externe. Une nouvelle version doit reproduire tous les cas de référence sans dégradation des critères.

### Étape 10 — Surveillance

Ajouter les nouvelles campagnes comme tests externes avant de les incorporer à l'apprentissage. Recalibrer seulement après revue et conserver l'historique des performances.

## Priorités de corpus

1. **Lin/époxy** : revoir et accepter les dix points numérisés, ajouter une troisième température et une publication indépendante, puis installer une route biphasique.
2. **IIR** : ajouter des répétitions indépendantes à 80, 100 et 120 °C ; traiter séparément la réponse non monotone à 120 °C.
3. **PP** : ajouter un autre grade et une autre publication ou campagne, puis garder cette dernière entièrement externe.
4. **Autres polymères prioritaires** : PET, PA66, PLA, PE, époxy, PEEK, PVC, NBR et TPU ; sélectionner un grade exact et suivre le même corpus minimal.
5. **Reste du catalogue** : conserver les fiches comme données d'entrée, sans prétendre disposer d'une cinétique fiable avant constitution du corpus.

## Critère de fin

SeaMat pourra être déclaré fiable pour un matériau précis lorsque sa source externe gelée respecte MAPE ≤ 10 %, erreur maximale ≤ 20 %, biais absolu ≤ 5 % et couverture 80–95 % pour une cible de 90 %, dans le domaine annoncé. L'application entière ne sera dite « universelle » que lorsque chaque matériau du catalogue aura atteint ce niveau ; jusque-là, la couverture est publiée matériau par matériau.
