# Comment utiliser le dépôt SeaMat

[← Accueil et téléchargements](../README.md)

## Un seul lien à partager

Transmettez **https://github.com/chillneonpro-bot/SeaMat**. Cette page donne accès au logiciel, au guide illustré, au rapport scientifique, aux méthodes et au code source. Les applications sont rangées dans **Releases**, à l’intérieur du même dépôt GitHub.

## Je veux seulement utiliser le logiciel

1. Sur l’accueil, choisissez le téléchargement Windows, Mac Apple Silicon ou Mac Intel.
2. Sous Windows, ouvrez le `.exe`. Sous macOS, décompressez le ZIP et placez `SeaMat.app` dans Applications.
3. Consultez le [guide d’installation](INSTALLATION.md) si le système demande une confirmation au premier lancement.
4. Ouvrez le [guide utilisateur PDF](livrables/01_Guide_utilisation/SeaMat_Guide_utilisation_complet.pdf) pour la saisie et l’interprétation des résultats.

Vous n’avez pas besoin de télécharger le code source ni d’installer Python pour ces applications. Un compte GitHub n’est pas nécessaire pour télécharger les fichiers d’un dépôt public.

## Je veux lire ou récupérer le rendu

Le dossier [livrables](livrables/README.md) comporte deux sous-dossiers :

- **01_Guide_utilisation** : guide illustré en PDF et version Word modifiable.
- **02_Rapport_scientifique** : rapport scientifique en PDF et version Word modifiable.

Cliquez sur un document pour l’ouvrir. Utilisez ensuite **Download raw file / Télécharger le fichier brut** pour l’enregistrer. Le PDF conserve la mise en page ; le Word permet les annotations et modifications. Si l’aperçu GitHub ne s’affiche pas, téléchargez le fichier et ouvrez-le localement.

## Je veux tout le dossier source et les documents

Depuis l’accueil du dépôt, cliquez sur **Code → Download ZIP**, puis extrayez l’archive. Elle contient les documents et le code. **Les applications compilées doivent être téléchargées séparément via les liens Windows/Mac** : elles sont distribuées dans Releases et ne sont pas incluses dans le ZIP du code source.

## Organisation

| Emplacement | Contenu | Public principal |
|---|---|---|
| [Accueil](../README.md) | Téléchargements et parcours rapide | Tous |
| [Releases](https://github.com/chillneonpro-bot/SeaMat/releases/latest) | Applications Windows/Mac et empreintes de contrôle | Utilisateurs |
| [Livrables](livrables/README.md) | Guide et rapport, PDF et Word | Étudiants, enseignants, évaluateurs |
| [Documentation](README.md) | Méthodes, validation, audits et installation | Utilisateurs avancés, évaluateurs |
| `seamat/` et `main.py` | Application et moteur scientifique | Développeurs |
| `data/evidence/` | Éléments scientifiques versionnés | Évaluateurs, développeurs |
| `tests/` | Vérifications automatiques | Développeurs |
| `examples/` | Exemple de mesures synthétiques | Démonstration uniquement |
| `.github/workflows/` et `packaging/` | Construction, tests et publication des applications | Maintenance |

Les documents nommés `MISE_A_JOUR_*` décrivent l’historique de développement. Pour commencer, utilisez le guide et le rapport du dossier des livrables.

## Mettre à jour le logiciel

Fermez SeaMat, sauvegardez vos données, puis récupérez le fichier correspondant à votre ordinateur depuis [la dernière version](https://github.com/chillneonpro-bot/SeaMat/releases/latest). Remplacez l’application par cette version. Vos données personnelles sont enregistrées séparément :

- Windows : `%LOCALAPPDATA%\SeaMat`.
- macOS : `~/Library/Application Support/SeaMat`.

Le numéro d’une version publiée correspond à un état précis du logiciel. Le code et la documentation de la branche `main` peuvent évoluer après cette publication.

## Comprendre les contrôles

Le fichier `SHA256SUMS.txt` de Releases contient les empreintes des applications. Celui du [dossier des livrables](livrables/SHA256SUMS.txt) concerne les documents. Ils permettent de vérifier l’intégrité des fichiers téléchargés.

La rubrique **Actions** contient les tests de fonctionnement informatique et de construction des applications. Pour évaluer la qualité scientifique d’une estimation, consultez le niveau de preuve dans SeaMat et les [études de validation](README.md#vérifier-la-validité).

## Signaler un problème

Ouvrez une [Issue](https://github.com/chillneonpro-bot/SeaMat/issues) en précisant le système, la version de SeaMat, les étapes suivies et le message d’erreur. Ajoutez une capture sans données personnelles. Ne publiez pas de mots de passe, de clés d’accès ou de base personnelle.
