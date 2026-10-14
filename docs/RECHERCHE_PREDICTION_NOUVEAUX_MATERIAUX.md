# Prédire le vieillissement d'un matériau ajouté à SeaMat

Étude de faisabilité et proposition scientifique — 12 octobre 2026.

Statut : recherche bibliographique ciblée et inspection du moteur existant. Ce document propose une architecture ; il ne constitue ni son implémentation ni une nouvelle validation expérimentale. Les calculs de production n'ont pas été modifiés pendant cette étude. Périmètre initial : polymères et composites à matrice polymère.

## Décision recommandée

Développer un moteur hybride qui apprend les paramètres de vieillissement à partir de la composition, des propriétés initiales, du procédé et d'essais publiés sur des matériaux apparentés, puis calcule des trajectoires avec des modèles physiques spécialisés. L'utilisateur peut ne fournir aucun essai de vieillissement de son propre grade. Le système, lui, doit disposer de données de vieillissement pertinentes et de validations de transfert vers des grades absents de l'apprentissage.

Une fiche donnant seulement E0, une densité et un nom de famille ne détermine pas une cinétique unique. Plusieurs formulations peuvent partager ces caractéristiques initiales et diverger après exposition. Il faut donc augmenter l'information utile et mesurer l'erreur de transfert. Une estimation est souvent possible ; une précision uniforme pour toute formulation et toute exposition ne peut pas être promise.

## 1. Résultats de la recherche

### Dose environnementale et lois physiques

Les travaux NIST sur le vieillissement accéléré mesurent séparément le rayonnement, la température et l'humidité pour construire des modèles de durée de service et les confronter au terrain. Cela justifie de remplacer le seul choix « extérieur » par une exposition quantifiée. La vérification du lien entre laboratoire et terrain fait partie du modèle, plutôt qu'une conversion universelle heures/années. [NIST, programme de métrologie](https://www.nist.gov/programs-projects/metrology-accelerated-laboratory-weathering).

Une prépublication de Hong et Gu (août 2026) compare une approche statistique physique et du deep learning sur des composants photovoltaïques, avec observations extérieures dans plusieurs environnements. Les auteurs trouvent l'approche physique plus robuste entre jeux de données. Les sorties sont le jaunissement et des changements chimiques : leur performance ne prouve pas celle d'une prédiction du module de Young. [Texte des auteurs](https://arxiv.org/html/2608.21148v1).

### Hydrolyse : relier la chimie à la mécanique

Une étude de PA 6-6 immergé à 60–90 °C relie l'hydrolyse, la masse molaire, la cristallinité et la fragilisation. Le modèle porte sur le régime où la diffusion d'eau ne contrôle pas la cinétique ; il ne s'applique donc pas automatiquement aux pièces épaisses. C'est une base pour un expert hydrolyse avec contrôle du régime de diffusion. [Étude primaire, 2012](https://doi.org/10.1016/j.polymdegradstab.2012.03.003).

### Le module peut augmenter pendant la dégradation

Les essais NIST sur HDPE exposé aux UV montrent une hausse du module pendant que l'allongement à rupture diminue. Le calcul doit autoriser rigidification, palier, induction puis chute selon les mécanismes. Une hausse de E n'est pas une amélioration générale de la durée de vie. [Hsueh et al., 2020, article accessible au NIST](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=926912).

### Prédiction depuis la structure chimique

Le projet des auteurs de *Revealing factors influencing polymer degradation with rank-based machine learning* fournit du code Python, des données expérimentales et des données de littérature. Il apprend un classement de dégradabilité à partir de représentations moléculaires. Son score ne donne pas directement E(t) ni un temps de rupture. C'est une piste réutilisable pour représenter les matériaux et contrôler la proximité chimique, après vérification de la compatibilité des données. [Dépôt des auteurs](https://github.com/tsudalab/Polymer-degradability-ranking).

PolymerGNN apprend des propriétés de polyesters, notamment Tg et viscosité intrinsèque. Cela soutient la possibilité de compléter certaines caractéristiques initiales depuis la composition, avec incertitude. Ce travail ne constitue pas un modèle validé de vieillissement mécanique. [Étude primaire, 2023](https://www.nature.com/articles/s41524-023-01034-3).

### Une étude récente proche du besoin, avec une limite instructive

Ni, Amamoto et Kikuchi étudient sept polyesters biodégradables : PBS, PBSA, PCL, PBAT, PES, P(3HB), PHBH. Ils associent structure, NMR, thermique et mécanique au vieillissement en milieu estuarien. Le R² annoncé de 0,81 ne signifie pas 81 % de fiabilité. La validation laissant un polymère entièrement de côté est plus prudente, et les auteurs limitent explicitement la généralisation. Les données incluent une caractérisation initiale avancée, ce qui dépasse une fiche commerciale simple. [Étude primaire, 2026](https://www.nature.com/articles/s41529-026-00764-1).

Une publication sur un modèle statistique informé par la physique sous données rares, DOI 10.1016/j.polymdegradstab.2026.112254, a également été repérée. Seuls le résumé et la notice éditeur étaient accessibles ; les performances annoncées n'ont pas été reproduites et ne sont pas retenues comme engagement pour SeaMat. [Notice éditeur](https://www.sciencedirect.com/science/article/abs/pii/S0141391026003356).

## 2. Ce que le moteur SeaMat actuel permet réellement

Inspection de `seamat/analog_model.py`, `seamat/engine_v2.py`, `seamat/reliability.py` sur la version 2.4, commit 1b76d42.

| Élément | Implémentation observée | Limite à traiter |
|---|---|---|
| Recherche d'analogue | Score composé de poids fixes et de correspondances de mots ; seuil 85/100 | Ce score n'est ni appris ni une probabilité de succès |
| Transfert | Meilleur matériau du catalogue, puis transfert des rétentions et remise à l'échelle par E0 | Les effets de formulation et de procédé ne sont pas appris quantitativement |
| Bande d'analogue | Pénalité fixée par formule depuis le score | L'erreur réelle de nouveaux grades ne calibre pas cette pénalité |
| Courbe publiée | Interpolation PCHIP puis loi de prolongement | Reproduire des points connus ne valide pas une prédiction sur un grade inconnu |
| Humidité et épaisseur | Conservées dans la requête et le manifeste du moteur de preuves | Aucun modèle de leur influence sur la courbe dans cette route |
| Température | Interpolation entre courbes quand le corpus le permet | Le corpus PP extérieur sans températures renseignées ne donne pas une loi thermique |
| Domaine | Principalement fenêtre temporelle, milieu et correspondance documentaire | Détection multidimensionnelle et stricte des conditions hors domaine à construire |
| Qualification 95/95 | Borne binomiale sur des groupes de validation interne | Ne démontre pas une couverture externe après calibration sur ces mêmes erreurs |

Contrôle reproductible effectué directement sur `predict_from_evidence`, avec corpus PP extérieur, E0 = 1 500 MPa, horizon 120 jours :

| Température demandée | Humidité demandée | Épaisseur demandée | Module à 120 j calculé |
|---:|---:|---:|---:|
| 23 °C | 50 % | 2 mm | 1 350,083567 MPa |
| 23 °C | 20 % | 2 mm | 1 350,083567 MPa |
| 23 °C | 90 % | 2 mm | 1 350,083567 MPa |
| 23 °C | 50 % | 0,5 mm | 1 350,083567 MPa |
| 23 °C | 50 % | 10 mm | 1 350,083567 MPa |
| 50 °C | 50 % | 2 mm | 1 350,083567 MPa |

Ces valeurs sont des sorties du logiciel, pas de nouveaux résultats de laboratoire. Leur invariance montre une absence de modèle de ces effets dans ce cas ; elle ne prouve pas une insensibilité physique du PP. Corriger cela est plus utile que réduire graphiquement la bande.

## 3. Données à demander à chaque ajout

Le formulaire doit distinguer « fourni », « extrait d'une source », « estimé » et « inconnu ». Une caractéristique inconnue ne devient jamais zéro. Les caractéristiques estimées sont propagées comme distributions ou scénarios, pas comme constantes exactes.

| Bloc | Champs proposés | Utilité |
|---|---|---|
| Identité | Polymère de base, grade, fabricant, copolymère/mélange, composition | Choisir une famille de réactions et éviter les faux analogues |
| Propriétés initiales | E0 en traction, résistance, allongement, densité ; normes, température d'essai, conditionnement | Définir correctement la cible et son état de référence |
| État physique | Tg, Tm si pertinent, cristallinité, masse molaire, état de réticulation | Distinguer mobilités et réseaux susceptibles de vieillir différemment |
| Formulation | Charges/fibres, teneur et orientation, stabilisants UV, antioxydants, plastifiants, fraction recyclée | Estimer induction, oxydation, interface et dispersion |
| Fabrication | Injection/extrusion/impression, recuit, cure, orientation, porosité | Décrire l'état réellement utilisé |
| Géométrie | Épaisseur, surface exposée, revêtement | Calculer transport d'eau, d'oxygène et absorption lumineuse |
| Usage | Température ou historique, humidité/immersion, fluide, pH, salinité, UV, oxygène, contrainte si modélisée | Décrire les causes et doses de vieillissement |
| Résultat attendu | Propriété, horizon, seuil et condition de mesure future | Éviter de confondre module résiduel, rupture et fin de service |

Le premier écran doit rester court : fiche PDF ou grade, E0, milieu, température, épaisseur, horizon. Le logiciel propose ensuite les champs supplémentaires réellement utiles au mécanisme choisi, avec indication de leur provenance.

## 4. Architecture proposée pour atteindre le meilleur transfert possible

### A. Corpus de séries temporelles traçables

Une ligne relie une mesure à son grade, sa formulation, son lot, sa campagne, son laboratoire et sa source. Stocker les répétitions ou au minimum effectif/écart-type, les unités, la méthode, la température de vieillissement ET celle de mesure, le conditionnement avant mesure, la géométrie et l'exposition.

Les références primaires doivent être retrouvables au tableau ou à la figure. Conserver l'incertitude de numérisation. Dédupliquer les données réutilisées dans plusieurs articles : deux DOI ne garantissent pas deux expériences indépendantes. Évaluer la qualité du protocole, sans attribuer une certification automatique au nom d'un éditeur.

### B. Représentation du matériau et choix des analogues

Associer des descripteurs chimiques, des fractions de composition et des propriétés initiales. Apprendre une relation entre distance des matériaux et erreur de transfert. Chercher plusieurs grades réellement comparables, plutôt qu'un matériau choisi par son nom ou E0. Un polymère de base commun ne suffit pas si le renfort ou la stabilisation change le mécanisme.

### C. Modèle hiérarchique avec experts physiques

Proposition d'ingénierie, à comparer aux références simples :

- Paramètres communs à une famille, ajustements par formulation/grade, effets de laboratoire et de lot.
- Expert thermo-oxydation : réactions, épuisement des stabilisants, transport de l'oxygène lorsque nécessaire ; loi thermique calibrée dans un régime identifié.
- Expert eau/hydrolyse : diffusion et sorption, plasticisation réversible, coupures irréversibles, effets du pH lorsque documentés.
- Expert UV : spectre, intensité/dose, température de surface et cycles ; vérifier la réciprocité avant de cumuler une dose simplement.
- Expert élastomères : compétition réticulation/coupure et indicateurs adaptés, dont allongement et éventuellement compression rémanente si des données compatibles existent.
- Expert composites : matrice, fibres, fraction/orientation et dégradation des interfaces.
- Vieillissement physique, fluage et fatigue : sous-modèles distincts, activés seulement si les entrées et données correspondantes existent.

Pour un nouveau grade, le modèle hiérarchique prédit une distribution de paramètres depuis sa description. Une intégration temporelle génère E(t), et les autres propriétés disponibles. Un modèle statistique de correction peut apprendre les écarts résiduels, en conservant contraintes physiques, positivité et état initial cohérent.

Il faut commencer avec un modèle hiérarchique ou un processus gaussien et des références simples, puis n'adopter un réseau plus complexe que si la validation externe prouve un gain. Le niveau de complexité doit suivre la quantité de données indépendantes.

### D. Incertitude et résultat individuel

Propager l'incertitude des entrées, des paramètres transférés, des modèles et de la variabilité entre lots. Distinguer la courbe moyenne d'une prédiction pour une éprouvette individuelle. Une bande de confiance de moyenne ne représente pas la dispersion des pièces.

Calculer un ensemble de trajectoires physiquement plausibles. Le temps au seuil est calculé pour chaque trajectoire ; les trajectoires sans franchissement restent censurées. La médiane des temps de franchissement n'est pas forcément le franchissement de la courbe médiane. Une bande point par point à 95 % n'est pas automatiquement une bande simultanée sur toute la courbe.

Un système d'applicabilité estime si le nouveau grade ET son exposition sont proches du domaine testé. Pour un cas lointain, la sortie est une estimation exploratoire, avec information prioritaire à compléter. Le système ne promet pas une courbe précise en masquant cette absence d'information.

## 5. Validation compatible avec « aucun essai fourni à l'ajout »

Le test principal doit imiter exactement cet usage : retirer toutes les mesures de vieillissement d'un grade, conserver uniquement les caractéristiques disponibles au moment de l'ajout, prédire puis comparer aux valeurs retirées.

Prévoir séparément :

1. Grades nouveaux dans une famille connue.
2. Publication ou laboratoire entièrement inconnu.
3. Polymère de base inconnu, test plus difficile qui ne doit pas être mélangé au premier.
4. Exposition/épaisseur nouvelles, avec mesure explicite de l'extrapolation.

Séparer apprentissage, calibration des bornes et test final gelé. L'extraction et la sélection des variables doivent aussi respecter cette séparation : aucune propriété mesurée après vieillissement de la cible ne devient une entrée d'une prédiction sans essais.

Rapporter erreur absolue en MPa, erreur relative (avec traitement des modules proches de zéro), biais, erreur par grade, erreur de temps au seuil, couverture, largeur des bornes et taux de cas refusés. Les résultats globaux ne doivent pas masquer les mauvais domaines. Les tolérances doivent être définies à partir de l'usage et de la répétabilité des essais.

### Correction du raisonnement 95/95 précédent

Le calcul « 59 succès sur 59 » donne une borne binomiale unilatérale supérieure à 95 % sous des hypothèses précises : système et intervalle figés auparavant, essais indépendants et représentatifs, même définition du succès. Ce n'est pas une règle universelle de quantité de données d'apprentissage.

Les quatre formulations PP actuelles sont utilisées en validation croisée et leurs erreurs servent à calibrer la bande. Leurs couvertures ne sont donc pas quatre succès d'un test externe indépendant d'un intervalle préalablement fixé. Les valeurs précédemment affichées « 47,3 % » et « 55 supplémentaires » sont des calculs conditionnels illustratifs, pas une preuve externe acquise ni un reste à faire certifié. Il faudra revoir cette présentation et réserver un vrai jeu externe.

En split-conformal standard, le rang théorique du quantile peut dépasser le nombre de scores quand la calibration est trop petite pour 95 %. Le rabattre au maximum observé ne préserve pas automatiquement la garantie. SeaMat le fait actuellement ; l'appellation « 95 % calibrée » doit être traitée comme une cible empirique interne, pas une couverture établie. La calibration doit ensuite respecter la structure par groupes et les décalages de distribution. [Angelopoulos et Bates](https://arxiv.org/abs/2107.07511), [Barber et al.](https://arxiv.org/abs/2202.13415).

Enfin, « 95 % dans l'intervalle » et « 95 % à moins de 5 % d'erreur » sont deux objectifs différents. Pour viser une courbe précise, il faut imposer aussi une largeur acceptable et tester directement la fréquence d'erreurs inférieures à une tolérance fixée. Élargir un intervalle n'améliore pas la courbe centrale.

## 6. Sources candidates et accessibilité

| Ressource | Usage utile | Statut et limite |
|---|---|---|
| [NIST HDPE, 2020](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=926912) | UV, température, rigidification/fragilisation | Article primaire accessible ; extraction des données à réaliser et contrôler |
| [PA 6-6, 2012](https://doi.org/10.1016/j.polymdegradstab.2012.03.003) | Hydrolyse et lien chimie/mécanique | Résumé éditeur consulté ; paramètres complets à récupérer avant implémentation |
| [Sept polyesters, 2026](https://www.nature.com/articles/s41529-026-00764-1) | Structures, caractérisation initiale, dégradation et propriétés mécaniques | Article accessible ; les auteurs renvoient vers RIKEN et une demande aux auteurs pour les données brutes |
| [Tsuda Lab, classement](https://github.com/tsudalab/Polymer-degradability-ranking) | Représentation chimique et classement de dégradabilité | Code Python et fichiers de données repérés ; pas un modèle E(t) |
| [MicroWPC](https://zenodo.org/records/14591484) | Vieillissement UV de LDPE, LLDPE, HDPE, PP recyclés | Dépôt identifié ; vérifier fichiers, licence et cibles avant intégration, pas de conversion automatique en module |
| [PoLyInfo](https://polymer.nims.go.jp/en/) | Propriétés, structure, procédé et conditions de mesure | Accès enregistré ; collecte massive et scraping explicitement interdits, accord nécessaire pour une intégration massive |
| [PoLyInfo Knowledge Collection](https://mdr.nims.go.jp/collections/a51b1ec2-8614-47b0-b251-f82c778994db?locale=en) | Ontologie de description des matériaux | Schéma sous CC BY ; cette licence n'ouvre pas toute la base de valeurs |
| [Données d'extrusion PLA](https://zenodo.org/records/10600929) | Effet du procédé sur la dégradation initiale | Jeu brut et notebooks disponibles ; vieillissement en procédé, pas durée de service extérieure |

Les données de propriétés statiques servent à enrichir les entrées. Les données de perte de masse ou de jaunissement peuvent renseigner des mécanismes. Seules des relations validées permettent de les traduire en module mécanique ; elles ne doivent pas être étiquetées comme des mesures de E(t).

## 7. Plan d'action et critères d'acceptation

| Ordre | Travail | Critère de fin |
|---|---|---|
| 1 | Revoir les labels d'incertitude, le calcul 95/95 et les paramètres non pris en compte | Aucun effet non modélisé présenté comme calculé ; aucune validation interne présentée comme externe |
| 2 | Fiche structurée, origine et inconnues de chaque valeur | Chaque simulation reconstituable, y compris ses hypothèses |
| 3 | Corpus initial ciblé : polyoléfines/UV, polyamides/eau, puis composites/humidité et élastomères | Plusieurs grades et campagnes séparables, propriétés et conditions compatibles |
| 4 | Tests de transfert automatisés laissant un grade complet absent | Rapport public des erreurs, intervalles et limites par domaine |
| 5 | Modèles hiérarchiques et experts physiques | Gain externe sur la simple médiane des analogues ; effets des entrées contrôlés |
| 6 | Calibration indépendante et détection du domaine | Couverture et largeur mesurées sur un test final gelé, avec taux de refus |
| 7 | Formulaire progressif et sortie courte | Ajout sans essai de vieillissement, une courbe lisible, niveau de preuve, limite temporelle et sources accessibles |

Le premier objectif doit être un transfert démontré vers des grades nouveaux de quelques familles bien couvertes. La même architecture pourra ensuite accueillir d'autres familles ; leur précision devra être mesurée à leur tour. Le nombre de fiches ne constitue pas le nombre de domaines validés.
