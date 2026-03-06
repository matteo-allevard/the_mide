\# 1. Architecture Design - AWS



\## 🎯 Objectif



Définir une architecture cloud native qui respecte les contraintes serverless, la scalabilité et la maintenabilité.



\## 📦 Services AWS Utilisés



| Service | Rôle | Justification Serverless |

| :--- | :--- | :--- |

| \*\*AWS Lambda\*\* | Cœur du traitement métier (proxy, worker, auth, snapshots). | Compute serverless, scaling automatique, facturation à l'usage. |

| \*\*API Gateway\*\* | Point d'entrée unique et sécurisé pour toutes les requêtes HTTP (Discord, Web). | Gestion des API, authentification, throttling, intégration native avec Lambda. |

| \*\*DynamoDB\*\* | Stockage persistant des métadonnées (utilisateurs, canvas, infos snapshots). | Base de données NoSQL serverless, scalabilité horizontale, performances prévisibles. |

| \*\*ElastiCache (Valkey)\*\* | Stockage en mémoire du canevas actif (chunks). | Cache distribué ultra-rapide pour les lectures/écritures fréquentes. Mode serverless disponible. |

| \*\*EventBridge / SQS\*\* | Bus d'événements et file d'attente pour découpler les composants. | Service d'event bus serverless, permet un traitement asynchrone et fiable. |

| \*\*S3\*\* | Hébergement du site web statique et stockage des snapshots (images). | Stockage objet serverless, haute durabilité, facile à servir via CloudFront. |

| \*\*CloudFront\*\* | CDN pour sécuriser et accélérer la distribution du site web statique. | Réseau de diffusion de contenu global, sécurisation (HTTPS), intégration avec S3. |

| \*\*CloudWatch\*\* | Centralisation des logs, métriques et alarmes. | Observabilité native, sans serveur à gérer. |

| \*\*IAM\*\* | Gestion fine des permissions entre les services. | Sécurité et principe du moindre privilège. |



\## 🔁 Flux de Données Détaillé



\### 1. Interaction Utilisateur (Discord)

1\.  Un utilisateur tape `/draw 10 20 FF0000` sur Discord.

2\.  Discord appelle l'\*\*Endpoint URL\*\* configuré, qui pointe vers \*\*API Gateway\*\*.

3\.  \*\*API Gateway\*\* valide la requête (signature Discord) et l'envoie à une \*\*Lambda "Discord-Proxy"\*\*.

4\.  La \*\*Lambda Proxy\*\* accuse immédiatement réception à Discord (pour éviter un timeout), publie un événement "PixelDrawRequest" sur un bus \*\*EventBridge\*\* (ou une queue SQS) et se termine.

5\.  Une \*\*Lambda "Worker-DrawPixel"\*\* est déclenchée par l'événement.

&nbsp;   \*   Elle vérifie le taux limite de l'utilisateur dans \*\*DynamoDB\*\*.

&nbsp;   \*   Elle valide les coordonnées et la couleur.

&nbsp;   \*   Elle met à jour le chunk de canevas correspondant dans le cluster \*\*ElastiCache (Valkey)\*\*.

&nbsp;   \*   Elle enregistre la métadonnée du pixel (auteur, timestamp) dans \*\*DynamoDB\*\*.

&nbsp;   \*   Elle envoie un message de confirmation (optionnel) à Discord via un webhook.



\### 2. Interaction Utilisateur (Web)

1\.  L'utilisateur charge l'application web statique depuis \*\*S3/CloudFront\*\*.

2\.  Il se connecte via Discord OAuth2. La lambda `Auth Handler` valide le token et crée une session.

3\.  Pour dessiner, le frontend fait une requête `POST /draw` à \*\*API Gateway\*\* (REST ou WebSocket) avec les coordonnées, la couleur et le token d'authentification.

4\.  Le processus est identique à celui de Discord à partir de l'API Gateway (proxy -> EventBridge -> worker).



\### 3. Génération de Snapshot (Tâche Planifiée)

1\.  Un \*\*EventBridge Scheduler\*\* déclenche une \*\*Lambda "Snapshot Generator"\*\* toutes les X minutes.

2\.  La Lambda lit l'état complet du canevas depuis \*\*ElastiCache\*\* (en agrégeant les chunks).

3\.  Elle génère une image (PNG/JPEG) et la stocke dans un bucket \*\*S3\*\* dédié.

4\.  Elle enregistre les métadonnées du snapshot (URL, timestamp) dans \*\*DynamoDB\*\*.

5\.  (Optionnel) Elle publie un événement pour notifier Discord.

