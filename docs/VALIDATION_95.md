# Qualification statistique 95/95 — SeaMat 2.4

Date de l'audit : 12 octobre 2026.

## Ce que signifie « fiable à 95 % »

SeaMat utilise désormais une règle vérifiable : l'intervalle doit couvrir au moins 95 % des futurs groupes comparables, et la borne basse statistique calculée avec un niveau de confiance de 95 % doit elle-même atteindre 95 %. Cette règle est appelée **95/95**.

L'unité de validation est une formulation, un grade ou une campagne entièrement cachée au moteur. Plusieurs temps mesurés sur la même éprouvette ou la même formulation sont corrélés et ne comptent donc pas comme autant de preuves indépendantes.

La borne est l'intervalle binomial exact unilatéral de Clopper-Pearson. Même avec zéro échec, il faut **59 groupes indépendants tous couverts** pour que la borne basse dépasse 95 %. Deux publications ou laboratoires indépendants au minimum sont aussi exigés. Une erreur moyenne faible ne remplace pas ce volume de preuve.

Cette notion diffère de « moins de 5 % d'erreur ». Une bande prédictive à 95 % peut être plus large que ±5 % si les essais réels sont dispersés. SeaMat affiche donc séparément l'erreur de la courbe centrale et la couverture de l'intervalle.

## Comparaison aveugle aux essais de laboratoire publiés

| Système réel | Protocole aveugle | Points prédits | Groupes indépendants | MAPE | Erreur maximale | R² | Conclusion |
|---|---|---:|---:|---:|---:|---:|---|
| PP H301, vieillissement naturel 0–120 j | Une formulation entière masquée à tour de rôle | 8 | 4 | 2,75 % | 3,41 % | 0,854 | Courbe centrale précise dans ce corpus ; preuve 95/95 insuffisante |
| IIR/BRC, Milform 64 SST, 80–120 °C | Un temps intérieur masqué | 15 | 3 campagnes de température | 8,35 % | 51,38 % | 0,810 | Pic à 120 °C mal reconstruit ; intervalle 95 % trop large pour un usage précis |
| IIR/BRC, courbe 100 °C | Température entière masquée | 6 | 1 | 11,31 % | 28,76 % | -2,154 | Transfert en température rejeté |
| Lin/époxy, 90 % HR, 20–40 °C | Une campagne de température masquée | 8 | 2 | 5,41 % | 11,40 % | 0,975 | Résultat encourageant dans 0–38 j ; points numérisés et corpus trop petit |

### PP H301

Les valeurs sont les modules de Young publiés pour quatre formulations à 0, 30 et 120 jours. Pour chaque tour, SeaMat ne conserve que le module initial de la formulation cible et utilise la rétention des trois formulations restantes. Les huit valeurs à 30 et 120 jours sont couvertes par une bande interne de ±3,41 %.

La couverture observée est de 4 groupes sur 4, soit 100 %, mais la borne basse exacte à 95 % n'est que de **47,3 %**. Il faut encore **55 groupes sans échec**, dans le meilleur cas, pour atteindre 59 groupes. La source primaire est *Effect of Natural Aging on the Properties of Recycled Polypropylene and Corn Husk Fiber Composites*, DOI [10.3390/polym16131788](https://doi.org/10.3390/polym16131788).

### Composite IIR/BRC

Les 21 valeurs exactes du tableau 2 couvrent 0 à 24 h, 80, 100 et 120 °C dans le fluide Milform 64 SST. La chute brutale après le pic à 120 °C produit une erreur de 51,38 % à 4 h. Pour atteindre une couverture cible de 95 % sur les quinze points masqués, la bande empirique doit donc atteindre **±51,38 %**. Cette largeur est honnête mais non exploitable pour une prédiction précise ; le moteur doit utiliser la courbe exacte ou refuser le transfert.

La source primaire est Nguyen-Tri, Triki et Nguyen, *Butyl Rubber-Based Composite: Thermal Degradation and Prediction of Service Lifetime*, DOI [10.3390/jcs3020048](https://doi.org/10.3390/jcs3020048).

### Composite lin/époxy

Le transfert croisé entre 20 et 40 °C donne 5,41 % d'erreur moyenne et 11,40 % au maximum. Les points intermédiaires proviennent toutefois d'une numérisation de figure avec environ 3 % d'incertitude de lecture. Ils restent donc une validation secondaire, pas une qualification de production. La source primaire est Scida et al., *Influence of hygrothermal ageing on the damage mechanisms of flax-fibre reinforced epoxy composite*, DOI [10.1016/j.compositesb.2012.12.010](https://doi.org/10.1016/j.compositesb.2012.12.010).

## Décision actuelle

Le moteur **n'est pas encore qualifié à 95 % pour n'importe quel matériau**. Il est précis pour les formulations PP étudiées dans leur fenêtre publiée, il est encourageant pour le lin/époxy, et il échoue à fournir une précision utile sur le transitoire IIR lorsqu'il doit le reconstruire.

SeaMat 2.4 empêche désormais une fausse déclaration de fiabilité :

- chaque résultat conserve la cible de couverture, le nombre de groupes cachés, le nombre couvert et la borne statistique basse ;
- la qualification externe exige l'objectif 95/95, au moins deux sources indépendantes et une correspondance documentaire supérieure ou égale à 80/100 ;
- les bandes internes sont calibrées pour une cible de 95 %, même si cela révèle une largeur importante ;
- une formulation complète compte pour un groupe, quels que soient ses nombreux temps de mesure ;
- un résultat hors fenêtre publiée ou un transfert qui échoue aux seuils est refusé comme résultat qualifié.

## Plan de qualification

1. Constituer un jeu externe gelé d'au moins 59 groupes indépendants par domaine revendiqué, provenant d'au moins deux laboratoires ou publications.
2. Répartir ces groupes par polymère de base, formulation, mécanisme de vieillissement, milieu, température, humidité, épaisseur et procédé. Une qualification PP extérieur ne vaut pas pour un IIR immergé.
3. Définir avant calcul les critères : couverture 95/95, MAPE ≤ 10 %, erreur maximale ≤ 20 %, aucune extrapolation au-delà de la fenêtre observée.
4. Garder le jeu de qualification invisible pendant le développement ; une nouvelle version du moteur déclenche une nouvelle évaluation complète.
5. Publier les prédictions individuelles, les résidus, les exclusions motivées et les empreintes de données afin que le résultat soit reproductible.
6. Calibrer des modèles distincts par mécanisme lorsque les résidus montrent un changement de phase, comme le pic IIR à 120 °C.
7. Ajouter progressivement de nouveaux domaines. Chaque domaine conserve sa propre décision : qualifié, limité à l'interpolation, ou non qualifié.

Une revendication universelle ne peut pas être obtenue par réglage logiciel seul. Elle nécessite ces essais externes indépendants. Le moteur peut en revanche appliquer automatiquement le même protocole à chaque nouveau matériau et refuser de présenter comme fiable un domaine qui n'a pas encore fourni cette preuve.
