# Matériaux manuels et transfert par analogues

## Objectif

SeaMat 2.3 calcule la meilleure estimation possible pour un matériau sans série de vieillissement propre. Le module de Young initial fixe l’échelle verticale de la courbe ; il ne suffit pas à déterminer sa vitesse de dégradation. Cette vitesse ne peut venir que d’un analogue possédant des séries temporelles revues et compatibles.

## Informations demandées

- famille chimique et polymère de base ;
- sous-type ou formulation ;
- module initial et référence du grade ;
- mécanismes de vieillissement attendus ;
- procédé et morphologie ;
- renfort ou charge et son taux ;
- contenu recyclé, additifs et stabilisants ;
- milieu d’utilisation visé.

## Décision automatique

Le moteur classe uniquement les matériaux du catalogue qui possèdent des mesures de vieillissement revues dans le milieu demandé. Il calcule un score sur 100 à partir de la famille, de l’identité du polymère, des mécanismes, du module initial, du procédé, du renfort et du milieu.

Le transfert est autorisé à partir de **85/100**. Le modèle source doit aussi satisfaire la porte commune de validation : au moins six prédictions masquées, erreur relative moyenne au plus 10 %, erreur maximale au plus 20 %, et couverture empirique comprise entre 80 et 100 %. L’horizon demandé doit rester dans la fenêtre observée.

Si une condition échoue, SeaMat conserve le scénario générique pour l’enseignement mais affiche **non qualifié** et donne la cause : analogue absent, similarité trop faible, validation insuffisante ou horizon trop long.

## Incertitude

La bande du matériau personnalisé combine l’erreur mesurée sur les données masquées de l’analogue et une pénalité qui augmente lorsque le score de similarité diminue. Elle n’est jamais remplacée par la plage visuelle uniforme de 10 % appliquée aux simples scénarios documentaires.

## Interprétation

Le statut **Analogue documenté · usage limité** autorise la valeur centrale pour comparer et présélectionner dans le domaine publié. Il ne prouve pas le comportement du grade réel et ne convient pas au dimensionnement de sécurité, à une garantie ou à une qualification industrielle.

Avec le corpus actuel, un PP personnalisé correctement décrit peut utiliser le cas PP extérieur sur 0–120 jours. Les autres familles restent bloquées tant qu’elles ne disposent pas d’un analogue assez proche et validé. Cette restriction empêche SeaMat de fabriquer une précision inexistante.
