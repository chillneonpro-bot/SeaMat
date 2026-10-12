# Comparaison de SeaMat V2.1 aux essais publiés

Date de l'évaluation : 12 octobre 2026  
Moteur : `seamat-evidence-router-2.1.0`

## Protocole

Une formulation, une température ou un point temporel est retiré du corpus avant la prédiction. La valeur calculée sans cette information est ensuite comparée à la valeur publiée. Les points simplement reproduits par une interpolation qui les a déjà vus ne sont pas comptés comme validation.

Critères de présélection : MAPE ≤ 10 %, erreur maximale ≤ 20 %, biais limité, couverture cohérente avec la bande annoncée et au moins six valeurs masquées. Une validation externe exige en plus une publication, un grade ou un laboratoire indépendant.

## Polypropylène PP H301 — formulation entière masquée

Source primaire : https://www.mdpi.com/2073-4360/16/13/1788

| Formulation masquée | Temps (j) | Mesuré (MPa) | Prédit (MPa) | Erreur relative |
|---|---:|---:|---:|---:|
| RPP1X | 30 | 561,8 | 549,7 | 2,15 % |
| RPP1X | 120 | 555,8 | 537,7 | 3,26 % |
| RPP3X | 30 | 465,2 | 480,7 | 3,33 % |
| RPP3X | 120 | 454,9 | 470,4 | 3,41 % |
| RPP3X + 3 % fibres | 30 | 504,9 | 488,8 | 3,20 % |
| RPP3X + 3 % fibres | 120 | 488,8 | 478,0 | 2,20 % |
| RPP3X + 5 % fibres | 30 | 492,4 | 503,2 | 2,20 % |
| RPP3X + 5 % fibres | 120 | 481,6 | 492,4 | 2,25 % |

MAE : 13,72 MPa. RMSE : 13,99 MPa. MAPE : 2,75 %. Erreur maximale : 3,41 %. Couverture par la bande ±3,41 % : 100 % des huit valeurs masquées.

**Verdict : fiable pour la présélection du PP H301 apparenté, sous le même protocole et entre 0 et 120 jours.** Le transfert vers un autre grade, un autre climat ou une durée supérieure n'est pas encore validé.

## Composite caoutchouc butyle IIR — temps intérieur masqué

Source primaire : https://www.mdpi.com/2504-477X/3/2/48

La courbe PCHIP est recalculée après retrait de chaque point intérieur.

| Température exacte | Valeurs masquées | MAPE | Erreur maximale | Verdict |
|---:|---:|---:|---:|---|
| 80 °C | 5 | 4,75 % | 9,54 % | Exploitable dans 0–24 h |
| 100 °C | 5 | 2,41 % | 4,03 % | Exploitable dans 0–24 h |
| 120 °C | 5 | 17,04 % | 52,45 % | Non fiable : réponse non monotone |
| Ensemble | 15 | 8,07 % | 52,45 % | Ne pas mutualiser une bande unique |

**Verdict : fiable aux températures exactes 80 et 100 °C dans la fenêtre publiée ; non fiable à 120 °C avec la loi actuelle.** La remontée initiale du module à 120 °C suggère un mécanisme ou un artefact que la cinétique monotone ne peut pas représenter.

## IIR — courbe 100 °C reconstruite depuis 80 et 120 °C

| Temps (h) | Mesuré (MPa) | Prédit (MPa) | Erreur relative |
|---:|---:|---:|---:|
| 1 | 2,510 | 3,232 | 28,76 % |
| 2 | 2,520 | 3,190 | 26,60 % |
| 4 | 2,330 | 2,167 | 7,01 % |
| 6 | 2,180 | 2,163 | 0,80 % |
| 14 | 2,010 | 2,085 | 3,72 % |
| 24 | 1,920 | 1,901 | 0,99 % |

MAPE : 11,31 %. Erreur maximale : 28,76 %. R² : -2,15.

**Verdict : non fiable pour le transfert entre températures.** Le routeur doit conserver les courbes exactes et refuser de qualifier l'interpolation thermique actuelle.

## Composite lin/époxy — données encore en attente

Source primaire : https://doi.org/10.1016/j.compositesb.2012.12.010

Les dix valeurs numérisées sont encore en attente de revue et ne sont donc pas utilisées par le moteur de production. La loi documentaire générique a été comparée aux huit valeurs vieillies :

| Température | Temps (j) | Mesuré (MPa) | Prédit actuellement (MPa) | Erreur relative |
|---:|---:|---:|---:|---:|
| 20 °C | 1 | 24 400 | 26 579 | 8,93 % |
| 20 °C | 3 | 17 800 | 26 537 | 49,08 % |
| 20 °C | 9 | 12 700 | 26 411 | 107,96 % |
| 20 °C | 38 | 12 000 | 25 810 | 115,08 % |
| 40 °C | 1 | 24 000 | 26 516 | 10,48 % |
| 40 °C | 3 | 17 400 | 26 348 | 51,43 % |
| 40 °C | 9 | 11 400 | 25 851 | 126,76 % |
| 40 °C | 38 | 11 200 | 23 579 | 110,52 % |

MAPE : 72,53 %. MAE : 9 591 MPa. Erreur maximale : 126,76 %. Le modèle sous-estime fortement la chute hygrothermique rapide.

Le transfert exploratoire entre les deux campagnes réelles donne pourtant une MAPE de 5,41 %, une erreur maximale de 11,40 % et R² = 0,975. Ce résultat est prometteur, mais il repose sur deux courbes numérisées d'une seule publication et ne peut pas encore être activé comme modèle validé.

**Verdict : le résultat de production actuel n'est pas fiable pour ce composite.** Il faut d'abord accepter les données après revue et remplacer le repli documentaire par une route hygrothermique propre au matériau.

## Conclusion globale

SeaMat V2.1 est fiable dans un domaine étroit lorsque le matériau, la formulation, la température, le milieu et l'horizon sont couverts par des essais compatibles. Il n'est pas encore fiable pour n'importe quel matériau du catalogue. Le logiciel prend correctement la décision PP, refuse le transfert IIR insuffisant, mais le repli documentaire des matériaux sans corpus peut rester très faux.

## Plan d'action

1. **Bloquer l'usage décisionnel du repli documentaire.** Le conserver pour l'exploration, sans l'appeler prédiction fiable ni lui donner une bande scientifique.
2. **Valider le corpus lin/époxy.** Contrôler les dix points numérisés, la géométrie, le protocole et l'incertitude de ±3 %, puis les accepter dans la file de revue.
3. **Ajouter une route hygrothermique.** Représenter la chute rapide puis le plateau du lin/époxy avec un modèle à deux phases ou diffusion-saturation, sélectionné par validation masquée.
4. **Scinder l'IIR par température exacte.** Conserver les routes 80 et 100 °C ; marquer 120 °C comme non monotone et interdire le prolongement monotone automatique.
5. **Remplacer l'interpolation thermique IIR.** Tester Arrhenius sur des paramètres cinétiques uniquement après vérification d'un même mécanisme ; sinon exiger une courbe exacte ou une troisième campagne indépendante.
6. **Ajouter des validations externes PP.** Intégrer au moins deux grades et deux publications ou laboratoires compatibles, en gardant une publication entièrement hors apprentissage.
7. **Calibrer une bande par route.** Une bande distincte pour chaque couple matériau–milieu–protocole ; aucun intervalle universel de ±5 %.
8. **Appliquer des portes de qualité automatiques.** Présélection : MAPE ≤ 10 %, erreur maximale ≤ 20 %, biais absolu ≤ 5 %, au moins six prédictions masquées et couverture 80–95 % pour une cible de 90 %.
9. **Limiter l'extrapolation.** Ne jamais qualifier une durée située au-delà de la fenêtre observée ; limiter l'affichage initial à 1,5 fois cette fenêtre avant validation externe.
10. **Geler un banc de non-régression.** Recalculer PP, IIR et lin/époxy à chaque version et refuser la publication si une erreur, une couverture ou un statut se dégrade.

## Critère de version publiable

Une famille devient publiable comme « validée pour la présélection » lorsqu'elle possède au minimum deux sources indépendantes, un groupe externe jamais utilisé pour le réglage, des conditions et grades explicitement couverts, MAPE ≤ 10 %, erreur maximale ≤ 20 % et une bande à 90 % couvrant entre 80 et 95 % des valeurs externes. Tout le reste reste « exploratoire » ou « non couvert ».
