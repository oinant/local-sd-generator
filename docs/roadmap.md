# Roadmap - Upcoming Features

Liste des fonctionnalités à venir, organisées par priorité et cible.

---

## Haute priorité (P1)

### CLI: Format JSON pour session_config
Transformer le fichier session_config.txt en JSON structuré pour améliorer la lisibilité et le parsing.
📄 [Spécification détaillée](roadmap/json-session-config.md)

### CLI: Métadonnées des choix interactifs
Sauvegarder les choix du menu interactif (mode génération, seed mode, etc.) dans session_config.
📄 [Spécification détaillée](roadmap/interactive-metadata.md)

### WebApp: Architecture simplifiée
Source unique de vérité avec CLI/apioutput, suppression de la duplication de dossiers.
📄 [Spécification détaillée](roadmap/webapp-architecture.md)

### All: Génération automatique de thumbnails WebP
Créer automatiquement des thumbnails WebP optimisés lors de la génération d'images.
📄 [Spécification détaillée](roadmap/webp-thumbnails.md)

---

## Priorité moyenne (P2)

### CLI: Lancement depuis fichier de configuration
Permettre de lancer une génération directement avec un fichier config JSON.
📄 [Spécification détaillée](roadmap/config-file-launch.md)

### WebApp: Base de données SQLite centralisée
Centraliser les métadonnées de sessions et images dans une base SQLite.
📄 [Spécification détaillée](roadmap/sqlite-database.md)

### CLI: Exclusion d'index de variations
Syntaxe pour exclure certains index : `{Hair:!|4|8}` au lieu de tout lister.

---

## Basse priorité (P3)

### Tool: Prévisualisation des variations
Interface CLI/webapp pour voir toutes les variations avant génération.

### CLI: Variations conditionnelles
Certaines variations ne s'appliquent que si d'autres sont présentes.

### CLI: Poids de variations en mode random
Certaines variations apparaissent plus souvent que d'autres.

### WebApp: Historique et favoris
Marquer des images favorites et générer des variations similaires.

### Tool: Templates de configuration réutilisables
Bibliothèque de configurations prêtes à l'emploi (portrait, character sheet, etc.).

---

## Légende

**Cibles :**
- **CLI** : Fonctionnalité pour les scripts de génération
- **WebApp** : Fonctionnalité pour l'interface web
- **Tool** : Fonctionnalité transverse ou outil annexe
- **All** : Impacte CLI et WebApp

**Priorités :**
- **P1** : Haute priorité (fondations, performance)
- **P2** : Priorité moyenne (enrichissement)
- **P3** : Basse priorité (exploration)

---

**Dernière mise à jour** : 2025-10-01
