\# 2. 🤖 Discord Bot Development



\## 🎯 Objectif



Développer un bot Discord serverless qui permet d'interagir avec le canevas via des commandes slash, en utilisant les Interactions Discord.



\## ⚙️ Configuration et Architecture



Le bot n'utilise \*\*pas\*\* de librairie comme `discord.js` en mode "self-hosted". Il est entièrement basé sur le système d'\*\*Interactions\*\* de Discord.



1\.  \*\*Portail Développeur Discord\*\* :

&nbsp;   \*   Créer une application et un bot.

&nbsp;   \*   Définir les commandes slash (`/draw`, `/canvas`, `/start`, `/pause`, `/reset`, `/snapshot`).

&nbsp;   \*   \*\*Configurer l'Endpoint URL\*\* : Mettre l'URL de votre API Gateway (ex: `https://api.votredomaine.com/discord/interactions`). Discord enverra toutes les interactions à cette URL.



2\.  \*\*AWS API Gateway\*\* :

&nbsp;   \*   Créez une route `POST /discord/interactions`.

&nbsp;   \*   Configurez la validation de requête pour vérifier la signature `X-Signature-Ed25519` et `X-Signature-Timestamp` de Discord (sécurité essentielle).

&nbsp;   \*   Intégrez cette route à une fonction \*\*Lambda "DiscordInteractionProxy"\*\*.



3\.  \*\*Lambda "DiscordInteractionProxy"\*\* :

&nbsp;   \*   \*\*Rôle\*\* : Point d'entrée unique pour Discord.

&nbsp;   \*   \*\*Actions\*\* :

&nbsp;       1.  Vérifier la signature de la requête (re-jouer la validation faite par API Gateway si nécessaire, ou s'assurer qu'elle est bien faite).

&nbsp;       2.  Pour les commandes, répondre immédiatement par un `response` de type `DEFERRED\_CHANNEL\_MESSAGE\_WITH\_SOURCE` (type 5). Cela indique à Discord que la requête est bien reçue et que le bot répondra plus tard (évite le timeout de 3 secondes).

&nbsp;       3.  Publier un événement détaillant la commande sur \*\*EventBridge\*\* (ou SQS).

&nbsp;       4.  Se terminer.



\## 📝 Commandes Implémentées



\*   `/draw <x> <y> <couleur\_hex>` : Place un pixel sur le canevas.

\*   `/canvas` : Retourne l'URL de la dernière snapshot du canevas (stockée sur S3).

\*   `/snapshot` (Admin) : Déclenche manuellement la génération d'une snapshot. La Lambda de snapshot enverra le résultat sur Discord via un webhook.

\*   `/start` / `/pause` / `/reset` (Admin) : Change l'état de la session (ouvert/fermé) dans DynamoDB. Les workers refuseront les dessins si la session est en pause.



\## 🔄 Flux de Traitement d'une Commande `/draw`



```mermaid

sequenceDiagram

&nbsp;   participant User as Utilisateur Discord

&nbsp;   participant Discord

&nbsp;   participant APIGW as API Gateway

&nbsp;   participant ProxyLambda as Lambda: Discord Proxy

&nbsp;   participant EventBridge as EventBridge

&nbsp;   participant WorkerLambda as Lambda: Worker Draw

&nbsp;   participant ElastiCache as ElastiCache (Valkey)



&nbsp;   User->>Discord: Tape /draw 5 5 #FF5733

&nbsp;   Discord->>APIGW: POST /interactions (avec signature)

&nbsp;   APIGW->>ProxyLambda: Invoque la fonction (validation incluse)

&nbsp;   ProxyLambda->>Discord: Réponse immédiate: DEFERRED (type 5)

&nbsp;   ProxyLambda->>EventBridge: Publie événement "DrawRequest"

&nbsp;   ProxyLambda-->>APIGW: Fin de l'invocation

&nbsp;   APIGW-->>Discord: 200 OK (pour la réponse deferred)

&nbsp;   Discord->>User: "Bot est en train de réfléchir..."



&nbsp;   EventBridge->>WorkerLambda: Déclenche la fonction

&nbsp;   WorkerLambda->>ElastiCache: Met à jour le pixel

&nbsp;   WorkerLambda-->>Discord: (Plus tard) Appelle Webhook pour dire "Pixel dessiné !"

&nbsp;   Discord->>User: Affiche le message de confirmation

