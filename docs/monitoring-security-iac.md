# 5. Monitoring, Security & Infrastructure as Code (IaC)

## Monitoring et Observabilité (CloudWatch)

### Logs Centralisés
- Toutes les fonctions Lambda envoient leurs logs structurés (JSON) à **CloudWatch Logs**.
- Création de groupes de logs dédiés :
  - `/aws/lambda/c3-discord-proxy`
  - `/aws/lambda/c3-worker-draw`
  - `/aws/lambda/c3-web-proxy`
  - `/aws/lambda/c3-auth-handler`
  - `/aws/lambda/c3-snapshot-generator`

### Métriques Personnalisées
Les Lambdas envoient des métriques à CloudWatch via `putMetricData` :

| Métrique | Description | Unité |
|:---------|:------------|:------|
| `PixelsDrawnPerSecond` | Taux de dessin par seconde | Count |
| `ActiveUsers` | Nombre d'utilisateurs actifs | Count |
| `DrawLatency` | Temps entre la requête et la confirmation | Millisecondes |
| `QueueDepth` | Profondeur de la file SQS/EventBridge | Count |
| `ChunkUpdateConflicts` | Nombre de conflits CAS sur ElastiCache | Count |
| `RateLimitExceeded` | Nombre de tentatives de dessin rejetées | Count |
| `WorkerExecutionTime` | Temps d'exécution du worker | Millisecondes |

### Tableaux de Bord (Dashboards)
Création d'un dashboard CloudWatch pour visualiser en temps réel l'état du système :
- **Vue d'ensemble** : Métriques clés (pixels/sec, utilisateurs actifs)
- **Performance** : Latences des différentes fonctions
- **Erreurs** : Taux d'erreur par fonction
- **Infrastructure** : État des queues et de la base de données

### Alertes (Alarms)
Configuration d'alarmes CloudWatch avec notifications via **Amazon SNS** :

| Alarme | Seuil | Action |
|:-------|:------|:-------|
| `HighDrawLatency` | `DrawLatency > 2s` pendant 5 minutes | Notification email |
| `FunctionErrors` | `Errors > 0` sur 5 minutes | Notification email + investigation |
| `HighQueueDepth` | `QueueDepth > 1000` pendant 2 minutes | Scaling check |
| `HighConflictRate` | `ChunkUpdateConflicts > 100`/min | Review CAS strategy |
| `LowSuccessRate` | `SuccessRate < 95%` sur 5 minutes | Alerte critique |

## Sécurité et IAM (Principe du Moindre Privilège)

### Rôles IAM Dédiés

#### Rôle pour `DiscordProxy`
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "events:PutEvents",
            "Resource": "arn:aws:events:region:account:event-bus/c3-draw-events"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
