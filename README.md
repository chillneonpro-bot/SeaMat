# SeaMat

**Python 3.11–3.13 · Windows · macOS · Linux · Docker**

Version actuelle : **3.1.0**. SeaMat est la nouvelle branche de développement scientifique issue de Materia 0.46. Elle possède son propre code, sa propre base SQLite, ses propres secrets et son propre port. Materia reste disponible sur le port 8087 ; SeaMat utilise le port 8088 et les deux logiciels peuvent fonctionner simultanément.

La version 3.1 ajoute un [modèle par mécanismes et familles](docs/MOTEUR_FAMILLES_V31.md) avec coefficients explicites, diffusion d’eau, UV, thermique et rigidification.

Le moteur 3.0 ajoute une précision mesurée à une tolérance choisie (±5 %, ±10 % ou ±20 %), les conditions d’applicabilité au grade saisi et la description détaillée du matériau. Les effets environnementaux sont appris uniquement quand des séries compatibles permettent de les identifier et de les tester par groupes masqués. Une propriété renseignée ne fait pas augmenter artificiellement la précision. Voir [le fonctionnement et les limites du moteur](docs/MOTEUR_PRECISION_V3.md).

SeaMat conserve le catalogue, les simulations, les comparaisons, les exports, l'espace classe et les validations existantes. Le moteur V2 et ses dix contrôles sont décrits dans [l'architecture scientifique](docs/ARCHITECTURE_SCIENTIFIQUE_V2.md) et leurs résultats chiffrés dans [la validation du moteur V2.1](docs/VALIDATION_MOTEUR_V2.1.md). Voir aussi [l'installation complète](docs/INSTALLATION.md), [la comparaison aux essais réels](docs/COMPARAISON_ESSAIS_REELS_V0.46.md) et [la qualification statistique 95/95](docs/VALIDATION_95.md).

Application Python de découverte et d'exploration du vieillissement des polymères. Interface NiceGUI, graphiques Plotly, calcul NumPy/SciPy et persistance SQLite.

**État : moteur V2 fonctionnel pour l’exploration, la comparaison et un pilote de classe.** Lorsqu’un corpus compatible existe, SeaMat reproduit les points publiés par interpolation PCHIP, sélectionne une loi de prolongement parmi plusieurs modèles, masque des séries entières pour mesurer l’erreur et calibre une bande prédictive sur ces erreurs. Sans données temporelles compatibles, le logiciel conserve une estimation documentaire de famille et l’identifie clairement comme telle.

Depuis la version 2.2, une [porte de fiabilité universelle](docs/PLAN_FIABILITE_UNIVERSELLE.md) applique les mêmes seuils à tous les matériaux. Une fiche sans cinétique acceptée reste calculable comme scénario pédagogique, mais aucune durée issue de cette courbe n'est présentée comme exploitable. La couverture réelle des 75 matériaux est disponible par `/api/v2/coverage`.

Depuis la version 2.3, un matériau ajouté manuellement peut utiliser une cinétique d’analogue documenté sans disposer de ses propres essais. Le calcul exige une correspondance d’au moins 85/100 sur la famille, le polymère de base, les mécanismes, le module, le procédé, le renfort et le milieu. Il reste limité à la fenêtre publiée de l’analogue et sa bande inclut une pénalité de transfert. Les règles sont décrites dans [l’ajout manuel par analogues](docs/AJOUT_MANUEL_ANALOGUES.md).

Depuis la version 2.4, chaque résultat affiche aussi l’audit **95/95** : SeaMat ne déclare une couverture de 95 % démontrée que si sa borne binomiale unilatérale à 95 % atteint elle-même 95 %, sur des groupes entièrement masqués et au moins deux sources indépendantes. Les points temporels corrélés d’une même formulation ne gonflent plus artificiellement la taille de validation.

## Ouvrir SeaMat

### Sur l'ordinateur de chaque étudiant

1. Téléchargez le ZIP du dépôt GitHub et décompressez-le.
2. Installez [Python 3.13](https://www.python.org/downloads/) si nécessaire.
3. **macOS :** double-cliquez sur `Lancer-SeaMat.command`.
4. **Windows :** double-cliquez sur `Lancer-SeaMat-Windows.bat`.

Le premier lancement crée un environnement isolé et installe automatiquement les composants. Le navigateur s'ouvre ensuite sur [http://127.0.0.1:8088](http://127.0.0.1:8088). Les lancements suivants sont directs tant que les dépendances ne changent pas.

Avec Docker :

```sh
docker compose up --build
```

### Avec une URL commune pour toute la classe

Déployez une seule instance Docker sur un serveur : les étudiants n'installent alors ni Python ni Docker et utilisent SeaMat depuis leur navigateur, sur macOS, Windows, Linux, tablette ou Chromebook. La base et les comptes sont conservés dans le volume persistant du serveur.

GitHub Pages ne peut pas exécuter cette application Python. Pour obtenir cette URL commune, déployez l'image Docker derrière HTTPS et définissez les deux codes d'administration dans `.env`. Les instructions et les variables sont détaillées dans [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Parcours disponibles

- Accueil : aperçu pédagogique et accès aux fonctions.
- Matériaux : recherche dans un catalogue réel de 75 polymères et composites.
- Ajout manuel : description structurée du polymère, de la formulation et du procédé, classement des analogues publiés, seuil d’acceptation commun et refus explicite si la preuve est insuffisante.
- Catalogue réel : 21 profils de module initial pour 19 matériaux sont recoupés entre deux documents fabricant officiels. Grade, norme, conditionnement, procédé et plage restent visibles.
- Simuler : page d’orientation vers deux parcours : fiche matériau et mesures publiées.
- Fiche matériau : estimation centrale sur les 75 fiches à partir du module initial, de la température, de l'humidité, de l'épaisseur et du milieu. Un module fabricant recoupé est proposé lorsqu’il existe ; la cinétique reste explicitement séparée. Le rapport affiche le niveau de preuve, les facteurs, les limites, une table accessible et une empreinte reproductible.
- Mesures publiées : quatre formulations PP issues du tableau MDPI sont tracées avec leur écart-type. L’interpolation reste limitée à 0–120 jours et l’extrapolation est bloquée.
- Preuves MDPI : 12 valeurs exactes de module du PP, issues de quatre formulations suivies à 0, 30 et 120 jours, recalibrent la courbe extérieure et sa plage inter-formulations.
- Cas PP H301 : validation hors formulation sans mesure de vieillissement cible, huit prédictions masquées, erreur relative moyenne de 2,75 % et bande empirique interne de ±3,41 % entre 0 et 120 jours.
- Comparer : un à quatre matériaux ou simulations enregistrées ; axes communs.
- Mes projets : retrouver les résultats avec la version conservée, exporter un classeur Excel illustré ou un rapport étudiant lisible, archiver ou supprimer les projets.
- Mon compte : compte local étudiant ou enseignant, mot de passe haché, conservation des projets entre navigateurs et droits adaptés au profil.
- Espace classe : création de cours réservée aux enseignants, code d’accès, travaux, consignes, parcours demandé, remise d’une simulation, correction, note sur 20, retour étudiant et export Excel des notes.
- Comprendre : six fiches et un exercice interactif.
- Données et modèles : import CSV hygrothermique contrôlé, calcul de `E/E₀`, rattachement à un matériau et une URL source, revue scientifique traçable, entraînement limité au corpus accepté, comparaison Ridge/Random Forest/boosting par expérience, interprétabilité et recherche Crossref.
- Mes documents : import de PDF texte, lecture par page, recherche locale et notes avec références. PDF limités à 8 Mo et 100 pages. Les scans nécessitent un OCR externe ou une transcription ; aucun texte n’est inventé. Les nouveaux originaux sont stockés séparément de SQLite et protégés par session ; les anciens documents Base64 sont migrés automatiquement à l’ouverture de la bibliothèque.

## Premiers essais

1. Dans Simuler, ouvrir **Mesures publiées** et comparer les quatre formulations PP à 120 jours.
2. Vérifier que la fenêtre publiée et la zone extrapolée sont clairement séparées lorsque l’horizon dépasse 120 jours.
3. Ouvrir **Fiche matériau**, choisir un matériau et lire le niveau de preuve avant la courbe.
4. Déplier la méthode et vérifier les facteurs, avertissements et l’empreinte du calcul.
5. Comparer deux matériaux à conditions communes et exporter le classeur Excel.
6. Créer un compte, enregistrer le résultat, puis rejoindre un cours dans **Espace classe**.

## Tests

L'audit reproductible sur les observations publiées est documenté dans
[`docs/AUDIT_DONNEES_REELLES_V31.md`](docs/AUDIT_DONNEES_REELLES_V31.md). Une
installation en cours d'exécution expose aussi le rapport JSON par
`GET /api/v3/audit-donnees-reelles`.

```sh
.venv/bin/python -m pytest -q
```

Les tests couvrent aussi l'interpolation des observations, le refus d'extrapoler au-delà du dernier temps mesuré, les comptes locaux, les droits enseignants, la protection de la revue scientifique et le cycle cours–travail–remise. Ils ne prouvent pas la validité sur des polymères réels.

## Données et comptes

Les données sont dans `data/seamat.sqlite3`. Les visiteurs peuvent essayer le logiciel dans une session invitée. Lors de la création d’un compte ou de la première connexion, les projets de cette session sont rattachés au compte. Les mots de passe sont salés et dérivés avec scrypt ; ils ne sont jamais conservés en clair.

Les comptes enseignants nécessitent un code serveur. Au premier lancement local, SeaMat génère ce code dans `data/.teacher_token` avec des droits de lecture restreints. `SEAMAT_TEACHER_TOKEN` permet de fournir un secret géré par l’établissement et reste prioritaire. Cette identité locale rend le pilote de classe utilisable ; un déploiement à l’échelle de l’école doit la remplacer ou la relier au SSO.

Le secret local est généré au premier lancement dans `data/.secret`. Les sessions NiceGUI sont dans `.nicegui/`. Ces fichiers sont ignorés par Git. Pour une publication Internet, utiliser le déploiement Docker documenté, des codes d'administration longs, un volume persistant et un domaine HTTPS.

La file de validation scientifique est verrouillée par défaut. Son code local est généré dans `data/.review_token` ; `SEAMAT_REVIEW_TOKEN` permet de le remplacer. Il faut un compte enseignant ou administrateur et ce second code pour accepter ou rejeter une expérience.

## Sauvegarde vérifiable

Créer puis contrôler une archive comprenant la base et les PDF séparés :

```sh
.venv/bin/python -m seamat.maintenance backup data/backups/seamat.zip
.venv/bin/python -m seamat.maintenance verify data/backups/seamat.zip
```

Le manifeste conserve la version de schéma, la taille et l’empreinte SHA-256 de chaque fichier. La vérification contrôle aussi l’intégrité SQLite.

## Limites explicites

Pas encore implémentés : authentification institutionnelle, administration centralisée des comptes, réinitialisation de mot de passe, extraction IA/OCR des publications, assistant conversationnel, intervalle prédictif validé pour toutes les familles, historique environnemental variable et choix automatique d'expériences. Hors PP extérieur, le corpus reste trop petit pour calibrer une incertitude statistique par matériau. Un transfert par analogue ne constitue jamais une qualification du grade personnalisé ; il autorise uniquement une présélection lorsque les seuils et le domaine sont satisfaits. La courbe centrale générique reste explicitement séparée des modèles informés par des publications.

Les publications Crossref fournissent des références ; elles ne sont ni extraites ni validées automatiquement. Les mesures importées restent en attente de validation et ne modifient pas le catalogue.

Voir `docs/ARCHITECTURE.md`, `docs/DICTIONNAIRE.md`, `docs/VALIDATION.md` et `docs/EXPLOITATION.md` pour les détails et la suite du projet. Le cahier des charges original est conservé dans `docs/CAHIER_DES_CHARGES.txt`.
