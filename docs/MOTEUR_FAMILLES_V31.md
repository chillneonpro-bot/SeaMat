# SeaMat 3.1 — calcul par mécanismes et famille

## Ce que cette version apporte

Les familles des 75 matériaux du catalogue sont reconnues et rattachées à six ensembles de mécanismes candidats : thermoplastiques, polymères sensibles à l’eau, réseaux thermodurcissables, élastomères, composites et polymères à haute stabilité. Un grade personnalisé peut utiliser sa famille ou son polymère de base.

La classification propose des mécanismes, pas des coefficients automatiques. La famille chimique et le module initial ne suffisent pas à déterminer une durée de vieillissement. Le modèle par mécanismes est activé explicitement ; sans activation, les voies documentaires, les analogues et les courbes publiées existantes restent disponibles avec leurs limites.

## Utilisation

Dans **Simuler → Paramètres avancés → Modèle par mécanismes**, activer le modèle, sélectionner les mécanismes pertinents ou demander une suggestion de famille, puis renseigner leurs coefficients et leur référence. On peut aussi enregistrer ces paramètres lors de la création d’un matériau personnalisé.

Les valeurs peuvent venir de publications ou de caractérisations antérieures ; il n’est pas nécessaire de réaliser soi-même les essais pour renseigner le modèle. SeaMat ne préremplit cependant aucun coefficient inconnu avec une valeur présentée comme vérifiée. Une hypothèse peut être déclarée comme telle pour préparer un protocole expérimental.

| Mécanisme | Calcul implémenté | Données nécessaires |
|---|---|---|
| Dégradation thermique | Vitesse à la référence, transfert d’Arrhenius | k en jour⁻¹, température de référence, Ea si transfert thermique |
| Photo-vieillissement | Vitesse multipliée par le rapport d’irradiance à une puissance documentée | k UV, irradiances réelle et de référence sur la même bande spectrale, exposant ; Ea si transfert thermique |
| Hydrolyse | Dommage cumulé proportionnel à l’intégrale de la teneur moyenne en eau | Diffusivité D, épaisseur, k d’hydrolyse à saturation, conditions de sorption ; énergies d’activation si transfert thermique |
| Plastification par l’eau | Réduction de module proportionnelle à la teneur moyenne en eau | D, épaisseur, fraction de perte à saturation |
| Rigidification | Gain saturant en fonction du temps | Vitesse, amplitude maximale, Ea si transfert thermique |

Une fraction résistante à la dégradation permet de définir un plateau. Le résultat conserve E(0)=E₀ et peut augmenter puis diminuer. Le module est considéré à la même température et dans le même état de mesure que le module initial : la modification instantanée du module lors d’un changement de température de mesure n’est pas prédite.

## Formulation et hypothèses

Avec des conditions constantes, le moteur combine des facteurs phénoménologiques :

`E(t)/E₀ = [r + (1−r) exp(−dommage)] × [1−p·eau(t)] × [1+g·(1−exp(−kᵣt))]`.

Le dommage additionne les contributions thermiques, UV et hydrolytiques choisies. Cette combinaison est une hypothèse de modèle réduit à valider ; elle n’est pas une loi universelle ni la reproduction intégrale d’un article.

La diffusion suit la solution moyenne de Fick dans une plaque initialement sèche, alimentée par ses deux grandes faces. D est exprimé en m²/s ; l’épaisseur saisie en mm et les temps en jours sont convertis. Le modèle ne résout pas une réaction-diffusion locale avec consommation d’eau, gonflement, fissuration ou diffusion anormale. En immersion, seul le milieu Eau est compatible avec cette voie ; l’humidité de l’air est ignorée. En air humide, la loi d’activité utilise l’exposant de sorption explicitement fourni.

Pour les composites, les coefficients doivent décrire le comportement effectif de l’éprouvette dans la direction mesurée. Le moteur n’effectue pas une homogénéisation des fibres et de la matrice, et ne déduit pas la délamination du seul taux de renfort.

Le transfert à travers Tg ou au-dessus de Tm est refusé lorsque ces transitions sont renseignées. Si elles sont inconnues, leur absence reste une limite de domaine ; leur non-saisie ne prouve pas qu’aucune transition n’est franchie. La fréquence, la contrainte, l’oxygène, le pH, les additifs et les cycles de climat ne sont pas des variables résolues par ce modèle réduit.

## Bornes, précision et expérimentation

Les bornes facultatives des coefficients permettent de calculer les combinaisons extrêmes (jusqu’à huit coefficients, soit 256 combinaisons et le scénario central). La bande correspond aux scénarios calculés ; elle n’est pas un intervalle probabiliste ni une garantie d’extrêmes globaux d’une fonction non linéaire. Sans bornes connues, le logiciel affiche uniquement la courbe centrale et « incertitude non quantifiée ».

La précision du modèle par mécanismes n’emprunte jamais le score de validation d’une autre route, même pour le PP. Les tests analytiques du logiciel vérifient l’implémentation ; ils ne sont pas comptabilisés comme des essais expérimentaux. Figer le résultat avant les essais conserve ses paramètres, hypothèses et version pour une comparaison indépendante ultérieure.

Le franchissement du seuil est recherché uniquement dans la durée demandée, avec prise en compte des courbes non monotones. « Non atteint » signifie non atteint pendant cette durée, pas durée de vie infinie. Une hausse de module peut accompagner une fragilisation : le logiciel ne prédit pas l’allongement à rupture ou la résistance à partir du module seul.

## Sources des formes de modèles — pas des coefficients de votre matériau

- [NIST, Hunston et White — cinétiques de dégradation des mastics](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=922362) : relaxation vers un plateau pour des modules de relaxation, et hypothèses de cinétique. Aucun module de relaxation n’est importé comme un module de Young.
- [Applied Sciences 2020, 10, 3618](https://doi.org/10.3390/app10103618) : solution moyenne de diffusion de Fick et effet de l’épaisseur. Aucune résistance à la traction n’est transformée en module de Young.
- [NIST — effet de la température et de l’intensité lumineuse sur le HDPE](https://www.nist.gov/publications/temperature-and-light-intensity-effects-photodegradation-high-density-polyethylene) : observation d’une augmentation de rigidité concomitante à la fragilisation.

L’extension à une famille scientifiquement qualifiée nécessite des coefficients représentatifs du grade et des validations indépendantes de la loi couplée, dans les conditions visées. Aucun objectif « zéro erreur pour tout matériau » n’est revendiqué par cette version.
