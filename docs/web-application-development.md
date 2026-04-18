# 4. Web Application Development

## Objectif

Développer une interface web serverless permettant aux utilisateurs de visualiser et de dessiner sur le canevas en temps réel, avec une authentification Discord.

## Architecture Frontend & Backend

### 1. Frontend (Statique)

- **Hébergement** : **Amazon S3** + **CloudFront**.
- **Technologies** : HTML, CSS, JavaScript (Vanilla ou framework léger comme React/Vue.js compilé en statique).
- **Fonctionnalités** :
  - Affichage du canevas par tuilage (chargement des chunks depuis le backend).
  - Palette de couleurs.
  - Sélection d'un pixel pour afficher l'auteur et la date (via une requête API sur `PixelMetadata`).
  - Bouton de connexion Discord (OAuth2).
  - Interface admin (si l'utilisateur a les droits).

### 2. Backend pour le Web (Serverless)

- **API Gateway REST ou WebSocket** :
  - **REST** : Plus simple pour les requêtes classiques (GET, POST). Idéal pour l'affichage et le dessin si on accepte un léger délai. Utilisation de `POST /draw` et `GET /canvas/state?chunkX=...&chunkY=...`.
  - **WebSocket** : Pour une expérience "quasi temps réel", on peut ouvrir une connexion WebSocket via API Gateway. Les mises à jour de pixels (via le worker) peuvent être poussées à tous les clients connectés. C'est un **bonus** avancé.
- **Fonctions Lambda** :
  - `AuthHandler` : Gère le flux OAuth2 avec Discord, valide les tokens JWT, et crée une session.
  - `GetCanvasChunk` : Lit un chunk spécifique depuis DynamoDB et le retourne au frontend.
  - `WebProxy` (Draw) : Fonction proxy qui reçoit la requête de dessin, valide l'authentification (via le token JWT) et publie l'événement sur EventBridge, similaire au bot Discord.

## Authentification avec Discord OAuth2

1. L'utilisateur clique sur "Se connecter avec Discord".
2. Il est redirigé vers l'URL d'autorisation Discord.
3. Discord le redirige vers une route API Gateway (ex: `/auth/discord/callback`).
4. La Lambda `AuthHandler` échange le `code` contre un `access_token` et récupère les informations de l'utilisateur (ID, username).
5. La Lambda crée ou met à jour l'utilisateur dans la table DynamoDB `Users`.
6. La Lambda génère un **token JWT** signé et le retourne au frontend (soit dans un cookie sécurisé, soit dans la réponse pour stockage en mémoire).
7. Pour toutes les requêtes API ultérieures (`/draw`, etc.), le frontend inclut ce JWT dans le header `Authorization`. L'API Gateway (ou une Lambda d'autorisation personnalisée) valide le JWT avant d'invoquer le proxy.

## Affichage du Canevas (Tuilage)

- Le frontend connaît les dimensions d'un chunk (ex: 64x64) et la taille totale du canevas.
- Lors du chargement ou du défilement (pan/zoom), le frontend calcule les chunks nécessaires à l'affichage.
- Pour chaque chunk requis, il fait une requête parallèle à `GET /canvas/chunk?x=<chunk_x>&y=<chunk_y>`.
- La réponse contient les données du chunk lues depuis DynamoDB. Le frontend les décode et les dessine sur un élément `<canvas>` HTML.
- (Bonus WebSocket) : Le serveur peut pousser un événement `pixel_updated` avec les coordonnées et la nouvelle couleur. Le frontend met à jour le pixel concerné sans recharger tout le chunk.
