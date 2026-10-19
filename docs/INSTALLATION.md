# Installer et distribuer SeaMat

## Applications prêtes à ouvrir — méthode recommandée

Depuis [l’accueil du dépôt](../README.md), téléchargez le fichier pour votre ordinateur. Python est inclus dans les applications distribuées.

- **Windows** : ouvrir `SeaMat-Windows-x64.exe`.
- **Mac Apple Silicon** : décompresser `SeaMat-macOS-Apple-Silicon.zip` et déplacer `SeaMat.app` dans Applications.
- **Mac Intel** : décompresser `SeaMat-macOS-Intel.zip` et déplacer `SeaMat.app` dans Applications.

Les applications ne disposent pas de certificat commercial Apple/Microsoft. Windows peut afficher SmartScreen ; pour le fichier provenant de ce dépôt, les options **Informations complémentaires → Exécuter quand même** peuvent être proposées. Sur macOS, si l’application est bloquée, consultez **Réglages Système → Confidentialité et sécurité** et l’option **Ouvrir quand même** pour SeaMat lorsqu’elle est proposée. Les règles d’un ordinateur géré par une école peuvent nécessiter l’intervention du service informatique.

Les données des applications sont stockées dans `%LOCALAPPDATA%\SeaMat` sous Windows et `~/Library/Application Support/SeaMat` sous macOS. Voir le [mode d’emploi du dépôt](UTILISER_CE_DEPOT.md) pour les documents et les mises à jour.

Les sections suivantes concernent l’installation depuis le code source.

## Installation depuis le code sur macOS

1. Installer Python 3.11, 3.12 ou 3.13 depuis `python.org`.
2. Télécharger puis décompresser l'archive GitHub de SeaMat.
3. Double-cliquer sur `Lancer-SeaMat.command`.
4. Si macOS bloque le premier lancement, effectuer un clic droit sur le fichier, choisir **Ouvrir**, puis confirmer l'ouverture.

Le lanceur crée `.venv`, installe les versions figées et ouvre le navigateur. Il ne modifie pas l'installation Python du système.

## Installation depuis le code sur Windows

1. Installer Python 3.11, 3.12 ou 3.13 depuis `python.org`. Le lanceur Python `py` est installé par défaut.
2. Extraire entièrement le ZIP ; ne pas lancer SeaMat depuis l'aperçu de l'archive.
3. Double-cliquer sur `Lancer-SeaMat-Windows.bat`.
4. Autoriser Python sur le réseau privé seulement si Windows le demande et si l'accès depuis d'autres postes du réseau est souhaité.

`uvloop` est exclu automatiquement sous Windows. Les chemins de l'environnement virtuel sont choisis selon le système.

## Utilisation manuelle sur Linux

```sh
python3.13 launcher.py
```

Pour un serveur sans navigateur :

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
SEAMAT_HOST=0.0.0.0 SEAMAT_PORT=8088 .venv/bin/python main.py
```

## Docker

```sh
cp .env.example .env
docker compose up --build -d
```

Le volume `seamat-data` conserve la base SQLite, les documents, les secrets et les sauvegardes lors du remplacement du conteneur. Sauvegarder ce volume avant une mise à jour.

Contrôler l'instance :

```sh
curl http://127.0.0.1:8088/health
docker compose logs --tail=100 seamat
```

## Publication depuis GitHub

Le workflow `container.yml` construit une image Linux `amd64` et `arm64` dans GitHub Container Registry lorsqu'un tag `v*` est publié. Le workflow `ci.yml` teste chaque modification sous Windows, macOS et Linux et contrôle le démarrage de l'image Docker.

GitHub Pages héberge uniquement des fichiers statiques et ne peut pas faire fonctionner NiceGUI, Python ou SQLite. Pour une URL publique, utiliser l'image Docker sur un serveur ou une plateforme acceptant les conteneurs, monter un volume persistant sur `/app/data`, puis placer l'application derrière un domaine HTTPS.

Dans ce mode, tous les étudiants ouvrent la même adresse dans un navigateur. Ils n'ont rien à installer sur leur Mac ou leur PC ; seul le serveur exécute Python et conserve les comptes, projets et documents.

Variables de serveur :

| Variable | Usage |
|---|---|
| `SEAMAT_HOST` | `127.0.0.1` en local, `0.0.0.0` dans Docker |
| `SEAMAT_PORT` | Port HTTP, `8088` par défaut |
| `SEAMAT_EXTERNAL_URL` | Adresse HTTPS publique utilisée par l'audit de déploiement |
| `SEAMAT_TEACHER_TOKEN` | Code enseignant long et unique |
| `SEAMAT_REVIEW_TOKEN` | Code indépendant pour la revue scientifique |
| `SEAMAT_DB` | Emplacement alternatif de la base SQLite |
| `SEAMAT_DOCUMENTS_DIR` | Emplacement alternatif des PDF importés |

## Données exclues de GitHub

La base SQLite, les comptes, les PDF, les sessions, les sauvegardes et les secrets sont ignorés. Seules les données scientifiques explicitement versionnées sous `data/evidence/` appartiennent au dépôt.

Avant chaque publication :

```sh
git status --short
python -m pytest -q
```

Vérifier qu'aucun fichier de `data/`, `.nicegui/`, `.env`, `output/` ou `tmp/` n'apparaît dans la liste.
