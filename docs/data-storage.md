

---



\### Fichier : `docs/03-data-storage.md`



```markdown

\# 3. 🗄️ Data Storage



\## 🎯 Objectif



Définir un modèle de données efficace, scalable et serverless pour stocker l'état du canevas, les métadonnées et les informations utilisateur.



\## 📊 Modèle de Données



\### 1. \*\*DynamoDB - Tables Principales\*\*



\*   \*\*Table: `Users`\*\*

&nbsp;   \*   `userId` (String, \*\*Partition Key\*\*) : Identifiant unique de l'utilisateur (Discord ID ou ID interne).

&nbsp;   \*   `discordUsername` (String) : Nom d'utilisateur Discord.

&nbsp;   \*   `lastDrawTimestamp` (Number) : Timestamp du dernier pixel posé (pour le rate limiting).

&nbsp;   \*   `drawCountMinute` (Number) : Compteur de pixels pour la minute courante.

&nbsp;   \*   `createdAt` (Number) : Date de première interaction.



\*   \*\*Table: `CanvasMetadata`\*\*

&nbsp;   \*   `canvasId` (String, \*\*Partition Key\*\*) : 'current' pour le canevas actif.

&nbsp;   \*   `status` (String) : 'open', 'paused', 'closed'.

&nbsp;   \*   `totalPixels` (Number) : Nombre total de pixels dessinés.

&nbsp;   \*   `lastSnapshotUrl` (String) : URL S3 de la dernière snapshot.

&nbsp;   \*   `lastSnapshotTime` (Number) : Timestamp de la dernière snapshot.

&nbsp;   \*   `dimensions` (Map) : `{ "width": 1000, "height": 1000 }` (ou infini, géré par les chunks).



\*   \*\*Table: `PixelMetadata`\*\* (Optionnel, pour traçabilité sans surcharger le cache)

&nbsp;   \*   `pixelId` (String, \*\*Partition Key\*\*) : `x:y` (ex: "150:250").

&nbsp;   \*   `lastUpdatedBy` (String) : `userId` du dernier auteur.

&nbsp;   \*   `lastUpdatedAt` (Number) : Timestamp de la dernière mise à jour.

&nbsp;   \*   `color` (String) : Dernière couleur (peut être déduite du cache, mais utile pour l'historique).



\### 2. \*\*ElastiCache pour Valkey - Stockage du Canevas Actif\*\*



\*   \*\*Stratégie de Chunking\*\* : Pour gérer un canevas "infini", on le divise en chunks de taille fixe (ex: 64x64 pixels).

\*   \*\*Clé\*\* : `chunk:<chunk\_x>:<chunk\_y>` (ex: `chunk:2:5`).

\*   \*\*Valeur\*\* : Une structure de données optimisée. Plusieurs options :

&nbsp;   1.  \*\*String (Recommandé)\*\* : Un bitmap ou une chaîne encodée. Par exemple, une chaîne hexadécimale de `64\*64\*3` caractères (si RGB). C'est très compact et rapide à lire/écrire avec `GET`/`SET`.

&nbsp;   2.  \*\*Hash\*\* : `HSET chunk:2:5 pixel:10:20 "#FF5733"`. Plus simple à manipuler mais moins performant pour des mises à jour fréquentes sur un même chunk.

&nbsp;   3.  \*\*RedisJSON (si module activé)\*\* : Permet de manipuler un objet JSON représentant la matrice du chunk.

\*   \*\*Choix de conception\*\* : On utilisera l'option \*\*String\*\* avec un encodage binaire personnalisé pour les performances maximales.



\### 3. \*\*Amazon S3 - Stockage des Snapshots et du Site Web\*\*



\*   \*\*Bucket: `c3-canvas-snapshots`\*\*

&nbsp;   \*   Dossier : `snapshots/`

&nbsp;   \*   Nom du fichier : `canvas\_<timestamp>.png` (ex: `canvas\_1678886400.png`).

&nbsp;   \*   Règle de cycle de vie : Supprimer ou archiver les snapshots de plus de X jours (optionnel).



\*   \*\*Bucket: `c3-web-app`\*\*

&nbsp;   \*   Contient les fichiers statiques : `index.html`, `script.js`, `style.css`.

&nbsp;   \*   Configuré pour l'hébergement de site web statique.

&nbsp;   \*   Accès restreint via CloudFront et OAC (Origin Access Control).



\## 🔄 Gestion de la Consistance et Concurrence



\*   \*\*Écritures Concurrentes\*\* : Le worker Lambda, avant de mettre à jour un chunk dans ElastiCache, doit s'assurer qu'il ne crée pas de conflit. On utilisera le \*\*versioning optimiste\*\* via le champ `CAS` (Check-And-Set) de Redis/Valkey. Le worker lit le chunk avec son `version\_token`, applique la modification, et le réécrit uniquement si le `version\_token` n'a pas changé. En cas d'échec, il réessaie.

\*   \*\*Rate Limiting\*\* : Implémenté dans le worker Lambda avant toute écriture. Il vérifie le compteur dans la table `Users` de DynamoDB et incrémente de manière atomique.

