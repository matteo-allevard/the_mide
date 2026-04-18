# 3. Data Storage

## Objectif

Définir un modèle de données efficace, scalable et serverless pour stocker l'état du canevas, les métadonnées et les informations utilisateur.

## Modèle de Données

### 1. DynamoDB - Tables Principales

- **Table: `Users`**
  - `userId` (String, **Partition Key**) : Identifiant unique de l'utilisateur (Discord ID ou ID interne).
  - `discordUsername` (String) : Nom d'utilisateur Discord.
  - `lastDrawTimestamp` (Number) : Timestamp du dernier pixel posé (pour le rate limiting).
  - `drawCountMinute` (Number) : Compteur de pixels pour la minute courante.
  - `createdAt` (Number) : Date de première interaction.

- **Table: `CanvasMetadata`**
  - `canvasId` (String, **Partition Key**) : `'current'` pour le canevas actif.
  - `status` (String) : `'open'`, `'paused'`, `'closed'`.
  - `totalPixels` (Number) : Nombre total de pixels dessinés.
  - `lastSnapshotUrl` (String) : URL S3 de la dernière snapshot.
  - `lastSnapshotTime` (Number) : Timestamp de la dernière snapshot.
  - `dimensions` (Map) : `{ "width": 1000, "height": 1000 }`.

- **Table: `PixelMetadata`** (Optionnel, pour traçabilité)
  - `pixelId` (String, **Partition Key**) : `x:y` (ex: `"150:250"`).
  - `lastUpdatedBy` (String) : `userId` du dernier auteur.
  - `lastUpdatedAt` (Number) : Timestamp de la dernière mise à jour.
  - `color` (String) : Dernière couleur posée.

### 2. Amazon S3 - Stockage des Snapshots et du Site Web

- **Bucket: `c3-canvas-snapshots`**
  - Dossier : `snapshots/`
  - Nom du fichier : `canvas_<timestamp>.png` (ex: `canvas_1678886400.png`).
  - Règle de cycle de vie : Supprimer ou archiver les snapshots de plus de X jours (optionnel).

- **Bucket: `c3-web-app`**
  - Contient les fichiers statiques : `index.html`, `script.js`, `style.css`.
  - Configuré pour l'hébergement de site web statique.
  - Accès restreint via CloudFront et OAC (Origin Access Control).

## Gestion de la Consistance et Concurrence

- **Écritures Concurrentes** : Le worker Lambda utilise les **écritures conditionnelles** de DynamoDB (`ConditionExpression`) pour éviter les conflits lors de mises à jour simultanées sur un même pixel. En cas d'échec de condition, il réessaie.
- **Rate Limiting** : Implémenté dans le worker Lambda avant toute écriture. Il vérifie et incrémente le compteur dans la table `Users` de DynamoDB de manière atomique via `UpdateItem` avec une expression conditionnelle.
