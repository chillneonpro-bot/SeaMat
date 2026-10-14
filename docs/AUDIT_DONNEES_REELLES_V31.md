# Audit SeaMat avec des données réelles

## Objet

Cet audit contrôle toute la chaîne SeaMat : lecture des observations acceptées, calcul, paramètres avancés, traçabilité, gel avant essai et exports Excel, PDF, Markdown et JSON.

Commande de contrôle :

```bash
python -m pytest -q tests/test_real_data_e2e.py
```

Le rapport exécutable est également disponible par `GET /api/v3/audit-donnees-reelles`.

## Cas PP : prédiction sans vieillissement de la formulation cible

Source : *Natural Aging of Reprocessed Polypropylene Composites Filled with Sustainable Corn Fibers*, DOI [10.3390/polym16131788](https://doi.org/10.3390/polym16131788), tableau 2, quatre formulations et sept éprouvettes par point.

Protocole de validation interne : une formulation est retirée entièrement. SeaMat conserve uniquement son module initial, puis estime ses rétentions à 30 et 120 jours avec les trois autres formulations. Cette opération est répétée pour les quatre formulations.

| Mesure | Résultat |
|---|---:|
| Prédictions masquées | 8 |
| Erreur relative moyenne | 2,75 % |
| Erreur relative maximale | 3,41 % |
| Couverture empirique de la bande interne | 100 % |

Ces chiffres valident le fonctionnement du cas PP H301 sur 0–120 jours. Ils ne valident pas tous les grades PP, tous les climats ou une durée de vie de plusieurs années.

## Cas IIR : restitution et transfert de température

Source : *Butyl Rubber-Based Composite: Thermal Degradation and Prediction of Service Lifetime*, DOI [10.3390/jcs3020048](https://doi.org/10.3390/jcs3020048), tableau 2, immersion dans Milform 64 SST à 80, 100 et 120 °C pendant 24 h.

Les 21 valeurs publiées sont restituées sans erreur numérique aux temps mesurés. Il s’agit d’un contrôle d’interpolation et d’extraction, pas d’une validation prédictive indépendante.

Lorsque la courbe 100 °C est masquée et reconstruite avec 80 et 120 °C :

| Mesure | Résultat |
|---|---:|
| Prédictions masquées | 6 |
| Erreur relative moyenne | 11,31 % |
| Erreur relative maximale | 28,76 % |
| R² | -2,15 |
| Décision SeaMat | transfert non validé |

La courbe à 120 °C augmente d’abord fortement puis diminue. Une simple loi monotone ou un transfert d’Arrhenius ne suffit donc pas. SeaMat conserve ces données, mais refuse de présenter le transfert comme qualifié.

## Paramètres avancés

| Paramètre | Effet contrôlé |
|---|---|
| Module initial E₀ | Multiplie exactement la courbe en MPa ; la rétention reste identique. |
| Seuil conservé | Change le temps de franchissement ; ne change jamais la courbe. |
| Tolérance de précision | Le score PP passe de 0 % à ±2 % à 100 % à ±5 % ; la courbe ne change pas. |
| Température IIR | Sélectionne ou interpole les courbes publiées ; un transfert non validé reste signalé. |
| Humidité en immersion | Sans effet, car l’humidité de l’air n’a pas de sens pour l’éprouvette immergée. |
| Épaisseur PP documentaire | Sans effet inventé ; le rapport indique « Non caractérisé ». |
| Épaisseur, humidité et température du modèle par mécanismes | Agissent sur la diffusion et l’hydrolyse lorsqu’une diffusivité et des vitesses explicites sont fournies. |
| Bande visible | Convention uniforme de vitesse ×0,95/×1,05 ; la bande scientifique d’origine reste dans la traçabilité. |

Le contrôle numérique du modèle par mécanismes sert à vérifier les équations et l’influence des champs. Ses coefficients de test ne sont pas présentés comme des mesures réelles.

## Exports

Le classeur Excel contient la courbe, le graphique natif, les paramètres, l’empreinte, le DOI et une feuille **Mesures source** avec les lignes expérimentales utilisées. Le PDF contient quatre pages pour un calcul complet. Le Markdown et le JSON conservent la même empreinte et les mêmes paramètres.

Une prédiction IIR 100 °C a aussi été figée, exportée, puis relue avec les sept temps du tableau publié. Le cycle complet restitue les sept points avec une erreur numérique nulle.

## Conclusion publiable

Le logiciel est fonctionnel sur les chemins testés et les exports sont exploitables. Le cas PP atteint 2,75 % d’erreur moyenne dans une validation interne hors formulation. Le cas IIR montre que le système sait aussi refuser un transfert insuffisamment fiable.

Il n’existe pas encore de preuve scientifique permettant d’annoncer 95 % de fiabilité pour n’importe quel matériau. Une telle affirmation exige plusieurs campagnes externes, des grades identifiés, les mêmes milieux et des horizons comparables. SeaMat distingue donc le bon fonctionnement informatique, la validation interne d’un cas et la qualification externe d’un grade.
