# Validation du moteur SeaMat V2.1

## Décision de version

La version 2.1 remplace l'intervalle visuel uniforme par une bande liée aux preuves disponibles. Elle produit une estimation pour chaque fiche du catalogue. Une estimation n'est classée comme calibrée que si des séries temporelles compatibles permettent de masquer des expériences, formulations ou températures entières. Les autres matériaux conservent le calcul documentaire et son niveau de preuve explicite.

Le moteur n'affirme donc pas une précision universelle. Il applique le même protocole de décision à tous les matériaux et adapte la largeur de la bande à la validation réellement disponible.

## Résultats reproductibles

Les valeurs suivantes sont recalculables par `GET /api/v2/benchmark`.

| Cas | Route | Valeur centrale | Test hors ajustement | Bande de base |
|---|---|---:|---:|---:|
| PP, extérieur, 23 °C, 120 jours | Ensemble du même matériau | 90,01 % conservés | 8 valeurs ; MAPE 2,75 % ; couverture 100 % | ±3,41 % |
| IIR, immersion Milform 64, 100 °C, 24 h | Courbe publiée exacte | 71,11 % conservés | Pas de température masquée pour cette route exacte | ±6,28 % issue de la dispersion publiée |
| IIR, immersion Milform 64, 90 °C, 24 h | Interpolation entre températures | 70,05 % conservés | 6 valeurs ; MAPE 11,31 % ; couverture 100 % | ±28,76 % |

Le cas PP montre qu'une bande serrée est possible lorsque les formulations masquées sont bien prédites. Le transfert IIR à une température non mesurée montre l'inverse : imposer ±5 % masquerait une erreur réelle de transfert. SeaMat conserve donc la grande bande et signale la route utilisée.

## Méthode de calcul

1. Les observations sont converties dans un schéma commun : jours, MPa, degrés Celsius, humidité relative et millimètres.
2. Les séries incompatibles, non finies ou non approuvées sont exclues.
3. Le routeur cherche une courbe aux conditions exactes, puis une interpolation admissible, puis un ensemble du même matériau.
4. Dans la fenêtre observée, une interpolation PCHIP monotone relie les points publiés sans oscillation polynomiale.
5. Après la dernière observation, plusieurs lois sont comparées : exponentielle, Weibull, exponentielle à plateau et prolongement local de fin de courbe.
6. Des groupes entiers sont laissés hors ajustement. Le quantile des erreurs logarithmiques résultantes calibre la bande.
7. La bande augmente au-delà du dernier temps observé et lors d'un transfert de température.
8. Le résultat conserve les sources, le domaine, la route, le modèle choisi, les métriques et l'empreinte du calcul.

## Conditions d'acceptation

Une route est considérée comme validée dans sa fenêtre lorsque six prédictions masquées au minimum sont disponibles, que la MAPE ne dépasse pas 15 %, qu'aucun écart relatif ne dépasse 20 % et que la couverture observée atteint 75 %. Ces seuils sont des critères de version contrôlés par les tests automatiques ; ils ne remplacent pas une qualification réglementaire.

Un horizon situé après la dernière observation est toujours indiqué comme extrapolation. Une température hors du domaine publié n'utilise pas la surface en température. Un grade ou procédé absent réduit le score de correspondance.

## Ajouter un nouveau matériau

Pour activer le moteur calibré, importer puis faire accepter au moins trois séries comparables avec :

- identité du matériau et du grade ;
- procédé et état ;
- module initial et série temporelle ;
- température, humidité, épaisseur et milieu ;
- protocole, nombre d'éprouvettes et dispersion si disponibles ;
- source primaire, DOI ou URL et emplacement exact ;
- identifiant d'expérience indépendant.

Les lignes en attente ou rejetées ne participent jamais au modèle. Après acceptation, elles passent par le même contrat de données et le même routage que le corpus livré avec SeaMat.

## Limites scientifiques

- La composition exacte, les stabilisants, la cristallinité et le procédé peuvent changer fortement la cinétique.
- Arrhenius n'est valide que si le mécanisme ne change pas dans la plage de température considérée.
- Une extrapolation longue reste plus incertaine qu'une interpolation dans la fenêtre publiée.
- Une couverture interne sur quelques groupes ne prouve pas une généralisation à tous les laboratoires.
- La qualification finale exige des essais indépendants sur le grade, le milieu et le protocole visés.

## Références méthodologiques

- Celina, *Review of polymer lifetime prediction methods and limitations*, disponible dans PubMed Central : https://pmc.ncbi.nlm.nih.gov/articles/PMC7599543/
- Revue sur le vieillissement environnemental et la prévision de durabilité des polymères : https://pmc.ncbi.nlm.nih.gov/articles/PMC8912441/
- Lei et al., *Distribution-Free Predictive Inference for Regression*, base du calibrage conforme : https://www.stat.berkeley.edu/~ryantibs/papers/conformal-jasa.pdf

## Vérifications de non-régression

La suite automatisée vérifie le contrat de données, la sélection multi-modèles, le routage, le contrôle de domaine, les valeurs PP et IIR ci-dessus, l'élargissement hors observations, la reproductibilité de l'empreinte et la présence des dix contrôles. Les rapports Markdown, PDF et Excel conservent la version du moteur.
