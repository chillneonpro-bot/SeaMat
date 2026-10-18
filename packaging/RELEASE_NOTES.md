# SeaMat 3.1.1 — applications de bureau

Cette version ajoute des applications autonomes : Python n’a pas besoin d’être installé.

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
