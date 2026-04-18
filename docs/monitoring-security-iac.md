# 5. Monitoring, Security & Infrastructure as Code (IaC)

## Monitoring et Observabilité (CloudWatch)

- **Logs Centralisés** :
  - Toutes les fonctions Lambda envoient leurs logs structurés (JSON) à **CloudWatch Logs**.
  - Création de groupes de logs dédiés : `/aws/lambda/c3-discord-proxy`, `/aws/lambda/c3-worker`, etc.
- **Métriques Personnalisées** :
  - Les Lambdas envoient des métriques à CloudWatch via `putMetricData` :
    - `PixelsDrawnPerSecond` (count)
    - `ActiveUsers` (count)
    - `DrawLatency` (millisecondes, du proxy à la fin du worker)
    - `QueueDepth` (profondeur de la file SQS/EventBridge)
    - `DynamoDBWriteConflicts` (nombre d'écritures conditionnelles en échec)
- **Tableaux de Bord (Dashboards)** :
  - Création d'un dashboard CloudWatch pour visualiser en temps réel l'état du système : métriques clés, logs d'erreur, etc.
- **Alertes (Alarms)** :
  - Alarme si `DrawLatency > 2 secondes` pendant 5 minutes.
  - Alarme si `Errors` (Lambda) > 0.
  - Alarme si la profondeur de la file d'attente est trop élevée (risque de backlog).
  - Notifications via **Amazon SNS** (email, SMS).

## Sécurité et IAM (Principe du Moindre Privilège)

- **Rôles IAM dédiés** pour chaque fonction Lambda, avec des politiques restrictives.
  - **Rôle pour `DiscordProxy`** :
    - `events:PutEvents` sur l'EventBridge spécifique.
    - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`.
  - **Rôle pour `Worker`** :
    - `dynamodb:GetItem`, `dynamodb:UpdateItem` sur la table `Users` (rate limiting).
    - `dynamodb:PutItem`, `dynamodb:UpdateItem` sur la table `CanvasMetadata`.
    - `dynamodb:PutItem` sur la table `PixelMetadata` (si utilisée).
    - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`.
  - **Rôle pour `AuthHandler`** :
    - `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem` sur la table `Users`.
    - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`.
- **API Gateway** :
  - Activer **AWS WAF** (Web Application Firewall) pour se protéger des attaques courantes (SQL injection, XSS).
  - Utiliser un plan d'usage avec throttling pour limiter les abus.
- **Gestion des Secrets** :
  - Utiliser **AWS Secrets Manager** ou **Parameter Store**.
  - Y stocker : `CLIENT_SECRET` de l'application Discord, la clé publique du bot, la clé secrète pour signer les JWT.
  - Les fonctions Lambda récupèrent ces secrets au démarrage (ou via des variables d'environnement pour les moins sensibles).

## Infrastructure as Code (IaC) - Optionnel (Bonus)

L'utilisation d'IaC est fortement recommandée pour la reproductibilité et la clarté. Voici les options possibles :

- **AWS CloudFormation** : Le natif AWS, utilisant des templates YAML/JSON.
- **AWS SAM (Serverless Application Model)** : Une extension de CloudFormation spécialement conçue pour les applications serverless. C'est l'outil idéal pour ce projet.
- **Terraform** : Multi-cloud, très puissant.

**Exemple de structure avec AWS SAM :**

```yaml
# template.yaml (extrait)
Resources:
  DiscordProxyFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/discord-proxy/
      Handler: app.lambda_handler
      Runtime: python3.12
      Policies:
        - Statement:
          - Effect: Allow
            Action: 'events:PutEvents'
            Resource: !GetAtt DrawEventBus.Arn
      Environment:
        Variables:
          EVENT_BUS_NAME: !Ref DrawEventBus
          DISCORD_PUBLIC_KEY: '{{resolve:secretsmanager:MyDiscordSecret:SecretString:publicKey}}'

  DrawEventBus:
    Type: AWS::Events::EventBus
    Properties:
      Name: c3-draw-events

  DrawWorkerFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/worker/
      # ... (autres configs)
```
