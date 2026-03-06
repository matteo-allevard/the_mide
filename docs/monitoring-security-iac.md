\# 5. ⚙️ Monitoring, Security \& Infrastructure as Code (IaC)



\## 📈 Monitoring et Observabilité (CloudWatch)



\*   \*\*Logs Centralisés\*\* :

&nbsp;   \*   Toutes les fonctions Lambda envoient leurs logs structurés (JSON) à \*\*CloudWatch Logs\*\*.

&nbsp;   \*   Création de groupes de logs dédiés : `/aws/lambda/c3-discord-proxy`, `/aws/lambda/c3-worker-draw`, etc.

\*   \*\*Métriques Personnalisées\*\* :

&nbsp;   \*   Les Lambdas envoient des métriques à CloudWatch via `putMetricData` :

&nbsp;       \*   `PixelsDrawnPerSecond` (count)

&nbsp;       \*   `ActiveUsers` (count)

&nbsp;       \*   `DrawLatency` (millisecondes, du proxy à la fin du worker)

&nbsp;       \*   `QueueDepth` (profondeur de la file SQS/EventBridge)

&nbsp;       \*   `ChunkUpdateConflicts` (nombre de conflits CAS sur ElastiCache)

\*   \*\*Tableaux de Bord (Dashboards)\*\* :

&nbsp;   \*   Création d'un dashboard CloudWatch pour visualiser en temps réel l'état du système : métriques clés, logs d'erreur, etc.

\*   \*\*Alertes (Alarms)\*\* :

&nbsp;   \*   Alarme si `DrawLatency > 2 secondes` pendant 5 minutes.

&nbsp;   \*   Alarme si `Errors` (Lambda) > 0.

&nbsp;   \*   Alarme si la profondeur de la file d'attente est trop élevée (risque de backlog).

&nbsp;   \*   Notifications via \*\*Amazon SNS\*\* (email, SMS).



\## 🔒 Sécurité et IAM (Principe du Moindre Privilège)



\*   \*\*Rôles IAM dédiés\*\* pour chaque fonction Lambda, avec des politiques restrictives.

&nbsp;   \*   \*\*Rôle pour `DiscordProxy`\*\* :

&nbsp;       \*   `lambda:InvokeFunction` (non, il ne doit pas invoquer d'autres Lambdas directement)

&nbsp;       \*   `events:PutEvents` sur l'EventBridge spécifique.

&nbsp;       \*   `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`.

&nbsp;   \*   \*\*Rôle pour `Worker-DrawPixel`\*\* :

&nbsp;       \*   `dynamodb:GetItem`, `dynamodb:UpdateItem` sur la table `Users` (uniquement pour le rate limiting).

&nbsp;       \*   `dynamodb:PutItem` sur la table `PixelMetadata` (si utilisée).

&nbsp;       \*   `elasticache:Connect` et permissions pour les commandes Redis (`GET`, `SET`, `WATCH`, etc.) sur le cluster ElastiCache.

&nbsp;       \*   `events:PutEvents` (optionnel pour envoyer des événements de confirmation).

&nbsp;   \*   \*\*Rôle pour `Snapshot Generator`\*\* :

&nbsp;       \*   `elasticache:Connect` et permissions `GET` sur le cluster.

&nbsp;       \*   `s3:PutObject` sur le bucket de snapshots.

&nbsp;       \*   `dynamodb:UpdateItem` sur `CanvasMetadata`.

\*   \*\*API Gateway\*\* :

&nbsp;   \*   Activer \*\*AWS WAF\*\* (Web Application Firewall) pour se protéger des attaques courantes (SQL injection, XSS).

&nbsp;   \*   Utiliser une clé d'API ou un plan d'usage si nécessaire (peu pertinent ici avec JWT).

\*   \*\*Gestion des Secrets\*\* :

&nbsp;   \*   Utiliser \*\*AWS Secrets Manager\*\* ou \*\*Parameter Store\*\*.

&nbsp;   \*   Y stocker : `CLIENT\_SECRET` de l'application Discord, la clé publique du bot, la clé secrète pour signer les JWT, les URLs de connexion Redis.

&nbsp;   \*   Les fonctions Lambda récupèrent ces secrets au démarrage (ou via des variables d'environnement pour les moins sensibles).



\## 🧱 Infrastructure as Code (IaC) - Optionnel (Bonus)



L'utilisation d'IaC est fortement recommandée pour la reproductibilité et la clarté. Voici les options possibles :



\*   \*\*AWS CloudFormation\*\* : Le natif AWS, utilisant des templates YAML/JSON.

\*   \*\*AWS SAM (Serverless Application Model)\*\* : Une extension de CloudFormation spécialement conçue pour les applications serverless. C'est l'outil idéal pour ce projet.

\*   \*\*Terraform\*\* : Multi-cloud, très puissant.



\*\*Exemple de structure avec AWS SAM :\*\*



```yaml

\# template.yaml (extrait)

Resources:

&nbsp; DiscordProxyFunction:

&nbsp;   Type: AWS::Serverless::Function

&nbsp;   Properties:

&nbsp;     CodeUri: src/discord-proxy/

&nbsp;     Handler: app.lambda\_handler

&nbsp;     Runtime: python3.12

&nbsp;     Policies:

&nbsp;       - Statement:

&nbsp;         - Effect: Allow

&nbsp;           Action: 'events:PutEvents'

&nbsp;           Resource: !GetAtt DrawEventBus.Arn

&nbsp;     Environment:

&nbsp;       Variables:

&nbsp;         EVENT\_BUS\_NAME: !Ref DrawEventBus

&nbsp;         DISCORD\_PUBLIC\_KEY: '{{resolve:secretsmanager:MyDiscordSecret:SecretString:publicKey}}'



&nbsp; DrawEventBus:

&nbsp;   Type: AWS::Events::EventBus

&nbsp;   Properties:

&nbsp;     Name: c3-draw-events



&nbsp; DrawWorkerFunction:

&nbsp;   Type: AWS::Serverless::Function

&nbsp;   Properties:

&nbsp;     CodeUri: src/worker-draw/

&nbsp;     # ... (autres configs)

