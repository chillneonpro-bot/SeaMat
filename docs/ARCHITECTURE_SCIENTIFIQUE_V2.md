# Architecture scientifique SeaMat V2

## Objectif

SeaMat doit produire, pour chaque matériau documenté, une courbe centrale de vieillissement, une plage d'incertitude justifiée et une explication courte de la valeur à utiliser. Le logiciel doit rester utilisable sans essai préalable de l'utilisateur, tout en indiquant clairement ce qui provient de mesures publiées, d'un transfert entre matériaux proches ou d'une extrapolation.

## Principe directeur

Une plage uniforme de ±5 % peut servir à l'affichage et à la comparaison, mais elle ne constitue pas une incertitude scientifique universelle. Le moteur V2 doit conserver cette vue simple et calculer en parallèle une incertitude fondée sur la qualité des sources, la proximité du grade, le domaine couvert et les erreurs mesurées en validation externe.

## Données minimales d'un matériau

- famille, polymère, grade, formulation, charges et additifs ;
- module initial, norme d'essai, vitesse, température et conditionnement ;
- géométrie, épaisseur, procédé et état de cristallinité lorsque disponible ;
- environnement : température, humidité, UV, oxygène, liquide, concentration et cycles ;
- série temporelle de la propriété avec dispersion, nombre d'éprouvettes et protocole ;
- source primaire, tableau ou figure, DOI ou URL, date d'accès et licence ;
- statut de revue, niveau de preuve et domaine d'emploi autorisé.

## Bibliothèque de modèles

Le moteur choisit le modèle selon le mécanisme dominant et les données disponibles :

1. modèle cinétique simple pour une série temporelle homogène ;
2. Arrhenius pour le transfert en température lorsque plusieurs températures existent ;
3. Williams-Landel-Ferry près de la transition vitreuse lorsque les hypothèses sont satisfaites ;
4. modèles humidité-diffusion pour absorption et plastification ;
5. modèles UV ou thermo-oxydatifs lorsque dose, irradiance ou oxygène sont documentés ;
6. modèles hiérarchiques pour partager l'information entre grades proches sans les confondre ;
7. apprentissage automatique seulement si la validation par publication et par famille démontre un gain réel.

Chaque prédiction conserve l'identifiant du modèle, ses paramètres, sa version, ses sources et son domaine de calibration.

## Sélection automatique

Avant le calcul, SeaMat attribue un score de correspondance au cas demandé :

- identité du grade et de la formulation ;
- proximité du protocole et de la propriété mesurée ;
- recouvrement des conditions environnementales ;
- distance entre l'horizon demandé et la fenêtre observée ;
- qualité, indépendance et nombre des sources.

Le routage retient le modèle admissible le mieux documenté. Si aucun modèle n'est admissible, SeaMat fournit une estimation documentaire explicitement classée comme telle, avec le cas analogue utilisé.

## Incertitude

La plage prédictive doit combiner :

- dispersion expérimentale publiée ;
- incertitude des paramètres ajustés ;
- erreur observée sur des publications laissées hors apprentissage ;
- pénalité de transfert entre grades, protocoles ou environnements ;
- pénalité d'extrapolation temporelle.

La vue principale affiche la valeur centrale, la borne prudente et le niveau de confiance. La plage ±5 % reste une convention visuelle seulement tant qu'une couverture statistique de 80 ou 90 % n'est pas démontrée.

## Validation obligatoire

La publication d'un modèle exige :

- validation croisée par publication, grade et laboratoire ;
- comparaison à une référence simple ;
- MAE, erreur relative médiane, biais, erreur au seuil et couverture de l'intervalle ;
- résultats séparés en interpolation et extrapolation ;
- au moins un jeu externe jamais utilisé pour l'ajustement ;
- tests de non-régression sur chaque famille prise en charge.

## Niveaux de résultat

1. **Documentaire** : transfert depuis une famille ou un grade analogue.
2. **Calibré** : ajustement sur une ou plusieurs séries du même grade.
3. **Validé externe** : performances mesurées sur une publication indépendante.
4. **Qualifié** : protocole, domaine et critères d'acceptation validés par l'établissement.

L'interface doit toujours afficher ce niveau à côté du résultat.

## Feuille de route

### Phase 1 — Socle isolé

- dupliquer et renommer l'application ;
- isoler base, secrets, port, Docker et lanceurs ;
- conserver le catalogue, les exports et les tests existants.

### Phase 2 — Schéma scientifique

- versionner les matériaux, protocoles, environnements et séries ;
- ajouter les champs de formulation et de traçabilité manquants ;
- automatiser les contrôles d'unités et de cohérence.

### Phase 3 — Moteur de routage

- implémenter la bibliothèque de modèles ;
- choisir automatiquement le modèle selon le domaine ;
- produire une fiche de calcul reproductible.

### Phase 4 — Incertitude calibrée

- mesurer les erreurs hors échantillon ;
- calibrer la couverture des intervalles ;
- séparer l'affichage simple de la plage scientifique.

### Phase 5 — Qualification

- constituer des cas de référence multi-familles ;
- publier les cartes de validité ;
- geler les versions de modèle utilisées dans les rapports.

## Critère de fonctionnement pour un nouveau matériau

Un nouveau matériau devient calculable après validation de son identité, de ses unités, de son module initial et d'au moins une source de vieillissement compatible. Sans série propre au grade, SeaMat peut utiliser un transfert documenté, mais doit le signaler et augmenter l'incertitude en fonction de la distance au cas source.
