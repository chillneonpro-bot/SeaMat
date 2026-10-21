# SeaMat 3.1.2 — applications de bureau

Cette version corrige les téléchargements et les imports et ajoute une navigation de retour. Python n’a pas besoin d’être installé.

## Corrections 3.1.2

- Téléchargements activés dans les fenêtres natives Windows et macOS (modèles Excel et exports).
- Boutons Retour et Accueil disponibles sur chaque page.
- CSV français : séparateur point-virgule, virgules décimales et espaces d’en-têtes acceptés.
- Lecture de l’onglet Mesures même si le classeur s’ouvre sur le mode d’emploi.
- Modèle Excel synthétique cohérent pour tester l’import puis l’ajustement ; remplacer ses valeurs par les mesures réelles.
- Message d’import persistant et erreurs de saisie plus explicites.

Fermez l’ancienne application et remplacez-la par la nouvelle. Les données restent dans le même dossier utilisateur.

## Télécharger

- **Windows 10/11, 64 bits** : `SeaMat-Windows-x64.exe`
- **Mac Apple Silicon (M1, M2, M3, M4…)** : `SeaMat-macOS-Apple-Silicon.zip`
- **Mac Intel** : `SeaMat-macOS-Intel.zip`

## Premier lancement

### Windows

Téléchargez le fichier `.exe`, puis double-cliquez dessus. Si Windows SmartScreen s’affiche, choisissez **Informations complémentaires**, puis **Exécuter quand même**. Le premier démarrage peut durer quelques dizaines de secondes.

### macOS

Décompressez le fichier ZIP, puis déplacez **SeaMat.app** dans Applications. Au premier lancement, faites un clic droit sur l’application, choisissez **Ouvrir**, puis confirmez. Téléchargez la version correspondant au processeur indiqué dans ** → À propos de ce Mac**.

## Données locales

Les comptes, simulations, documents et sauvegardes restent sur l’ordinateur :

- Windows : `%LOCALAPPDATA%\SeaMat`
- macOS : `~/Library/Application Support/SeaMat`

Les applications sont compilées automatiquement par GitHub Actions, testées par une ouverture réelle et contrôlées via les points de santé et de référence scientifique. Elles ne sont pas signées avec un certificat commercial Apple ou Microsoft ; l’avertissement du premier lancement est donc normal.
