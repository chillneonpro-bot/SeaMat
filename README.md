# SeaMat — logiciel et dossier de rendu

**Tout SeaMat au même endroit : applications Windows et Mac, guide illustré, rapport scientifique et code source.**

**Lien unique à transmettre : https://github.com/chillneonpro-bot/SeaMat**

## 1. Ouvrir le logiciel

Téléchargez uniquement le fichier correspondant à votre ordinateur. **Python n’est pas nécessaire pour ces applications.**

| Votre ordinateur | Télécharger | Ensuite |
|---|---|---|
| Windows 10/11 — 64 bits | [**SeaMat pour Windows (.exe)**](https://github.com/chillneonpro-bot/SeaMat/releases/latest/download/SeaMat-Windows-x64.exe) | Double-cliquer sur le fichier |
| Mac avec puce Apple — M1, M2, M3, M4… | [**SeaMat pour Mac Apple Silicon (.zip)**](https://github.com/chillneonpro-bot/SeaMat/releases/latest/download/SeaMat-macOS-Apple-Silicon.zip) | Décompresser, puis déplacer **SeaMat.app** dans Applications |
| Mac avec processeur Intel | [**SeaMat pour Mac Intel (.zip)**](https://github.com/chillneonpro-bot/SeaMat/releases/latest/download/SeaMat-macOS-Intel.zip) | Décompresser, puis déplacer **SeaMat.app** dans Applications |

Sur Mac, ** → À propos de ce Mac** indique le processeur. Le premier lancement peut prendre quelques dizaines de secondes. Les applications ne disposent pas de certificat commercial Apple/Microsoft : une confirmation du système peut être nécessaire. Voir les [instructions d’installation](docs/INSTALLATION.md).

[Voir la version publiée et ses fichiers de contrôle](https://github.com/chillneonpro-bot/SeaMat/releases/latest). Les téléchargements sont hébergés dans la rubrique **Releases de ce même dépôt**.

## 2. Lire les documents

| Document | Lire ou imprimer | Modifier |
|---|---|---|
| **Guide d’utilisation complet** — captures annotées, paramètres, lecture des courbes, comparaison et exports | [**Guide PDF**](docs/livrables/01_Guide_utilisation/SeaMat_Guide_utilisation_complet.pdf) | [Guide Word](docs/livrables/01_Guide_utilisation/SeaMat_Guide_utilisation_complet.docx) |
| **Rapport scientifique** — démarche, calculs, précision, validation et limites | [**Rapport PDF**](docs/livrables/02_Rapport_scientifique/SeaMat_Rapport_scientifique.pdf) | [Rapport Word](docs/livrables/02_Rapport_scientifique/SeaMat_Rapport_scientifique.docx) |

Pour enregistrer un document, ouvrez son lien puis utilisez **Download raw file / Télécharger le fichier brut**. Le guide et le rapport documentent SeaMat 3.1 ; les applications de bureau sont publiées en version 3.1.1.

## 3. Faire une première simulation

1. Choisir un matériau dans **Matériaux**, ou créer une fiche personnalisée.
2. Ouvrir **Simuler** et renseigner le module initial, les conditions de service et la durée.
3. Cliquer sur **Calculer**, puis consulter la courbe et le niveau de preuve associé.
4. Utiliser **Comparer** pour confronter plusieurs scénarios dans les mêmes conditions.
5. Exporter les résultats en **Excel ou PDF** pour conserver les paramètres et les conclusions.

La courbe est une estimation. Sa portée dépend des données disponibles et du domaine de validation affiché ; les tests informatiques ne garantissent pas une précision expérimentale universelle.

![Aperçu de SeaMat](docs/assets/apercu-seamat.png)

## 4. Se repérer dans le dépôt

| Vous cherchez… | Ouvrir |
|---|---|
| Comment utiliser GitHub, télécharger les fichiers et mettre à jour SeaMat | [**Mode d’emploi du dépôt**](docs/UTILISER_CE_DEPOT.md) |
| Les documents du rendu, bien classés | [**Dossier des livrables**](docs/livrables/README.md) |
| Les méthodes, sources, audits et études de validation | [**Sommaire de la documentation**](docs/README.md) |
| Les fonctions et le moteur en détail | [Présentation détaillée](docs/PRESENTATION_DETAILLEE.md) |
| Installer depuis le code ou déployer dans une école | [Installation](docs/INSTALLATION.md) · [Déploiement institutionnel](docs/DEPLOIEMENT_INSTITUTIONNEL.md) |
| Signaler un problème | [Issues du dépôt](https://github.com/chillneonpro-bot/SeaMat/issues) |

Le code se trouve dans `seamat/`, les tests dans `tests/` et les données scientifiques versionnées dans `data/evidence/`. Les comptes, simulations et documents personnels restent sur votre ordinateur.
