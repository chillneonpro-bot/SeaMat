# SeaMat 3.0 — moteur et précision

Le moteur distingue une estimation du vieillissement, sa validation sur les références et son applicabilité au matériau saisi. Il ne transforme jamais la complétude d’une fiche en probabilité de justesse.

## Utilisation

1. Dans **Simuler**, choisir le matériau, le milieu, la température et l’horizon.
2. Ouvrir **Paramètres avancés** pour renseigner le grade, le procédé, le module initial, l’humidité et l’épaisseur.
3. Dans **Composition et propriétés du matériau**, saisir les propriétés connues : masse volumique, Tg, Tm, cristallinité, masse molaire, renfort, contenu recyclé, stabilisants. Laisser les inconnues vides.
4. Choisir l’erreur acceptable : ±5 %, ±10 % ou ±20 %. Ce réglage change le critère d’évaluation, pas les courbes ni leurs bornes.
5. Cliquer **Calculer** après toute modification.
6. Lire la précision sur les références, le statut du grade et les contrôles dans **Ce qui influence le calcul et sa précision**.

Les mêmes informations sont conservées dans le résultat enregistré, le JSON, le classeur Excel, le rapport PDF et le rapport étudiant. Excel contient les comparaisons masquées individuelles.

## Signification du pourcentage

Précision observée = nombre de prédictions masquées à une erreur relative inférieure ou égale à la tolérance / nombre de prédictions masquées examinées.

L’erreur est calculée sur la rétention E/E₀, hors temps zéro. Seuls les points à une durée inférieure ou égale à l’horizon demandé sont comptés. Les temps d’une même formulation ne sont pas des essais indépendants ; le nombre de groupes est affiché.

Exemple du corpus PP actuel, horizon 120 jours : 8 prédictions sur 4 formulations, erreur relative moyenne 2,75 %, maximum 3,41 %. Le score est donc 100 % à la tolérance ±5 %, sur ce petit contrôle interne. Ce n’est ni une probabilité de réussite pour un PP arbitraire ni une validation à 95 %.

Pour un grade ou des conditions insuffisamment documentés, **Précision du grade non établie** reste affiché. Une absence de test est distincte d’une précision de 0 %. La complétude est un indicateur séparé.

## Routage du calcul

- Séries publiées compatibles : interpolation des courbes et extrapolation explicitement signalée.
- Corpus permettant d’identifier les effets : ajustement conjoint d’une cinétique avec température de type Arrhenius et, lorsqu’ils sont documentés, humidité, épaisseur, cristallinité, masse molaire ou renfort.
- Matériau personnalisé : transfert documenté depuis un analogue admissible, avec sa pénalité et sans emprunter la qualification du grade source.
- Corpus insuffisant : scénario documentaire existant, sans précision expérimentale inventée.

L’expert environnemental exige au moins six séries admissibles, au moins trois sources ou trois grades identifiés, un plan d’expérience identifiable, une combinaison de paramètres dans le domaine conjoint, et une validation où chaque source ou grade est entièrement masqué. Les seuils internes d’activation sont une erreur moyenne ≤10 % et une erreur maximale ≤20 %. Ils ne constituent pas une qualification industrielle.

La loi exponentielle n’est pas appliquée aux séries avec une rigidification ou des changements de régime incompatibles. Les séries difficiles ne sont pas supprimées des cibles de validation pour améliorer artificiellement le score. Les propriétés non identifiables sont indiquées comme renseignées mais non apprises.

## Limites concrètes

Le corpus livré ne suffit pas encore à apprendre tous ces effets pour tous les matériaux. Ajouter Tg ou une masse volumique ne suffit pas à identifier une vitesse de vieillissement. Les effets de diffusion, d’UV, de réactions chimiques couplées et de contraintes mécaniques ne sont pas des solveurs multiphysiques implémentés par cette version. Le moteur conserve les mécanismes et données disponibles sans inventer leurs coefficients.

Les bandes sont empiriques ou indicatives selon la route. Elles ne sont pas resserrées en fonction d’un objectif visuel. Leur couverture future exige un jeu indépendant après gel du modèle et des bornes. Les quatre formulations du contrôle interne PP ne sont pas comptées comme quatre succès d’un tel test externe.

## Reproductibilité

Le manifeste enregistre les entrées, la description matérielle, la tolérance, les sources, la version, la loi utilisée, les coefficients éventuels, les prédictions masquées et l’empreinte SHA-256. Les anciens résultats restent des instantanés : recalculer pour bénéficier de la version 3.0.

Les tests numériques synthétiques vérifient l’implémentation et restent dans les tests. Ils n’entrent jamais dans la base documentaire ni dans les pourcentages de précision proposés aux utilisateurs.

Pour étendre les capacités : importer des séries traçables avec temps zéro, conditions d’exposition, grade, procédé et propriétés mesurées ; contrôler unités et extraction ; séparer les groupes ; puis réserver des campagnes externes avant toute nouvelle qualification.
