\# C3: Cloud-Native \& Serverless - Collaborative Pixel Canvas (r/place Clone)



\## 🎨 Présentation du Projet



Bienvenue dans la documentation officielle du projet \*\*C3\*\*. Ce projet a pour objectif de concevoir et d'implémenter un prototype fonctionnel d'une plateforme de dessin collaboratif multijoueur, entièrement serverless et inspirée de Reddit's r/place.



Les utilisateurs peuvent dessiner des pixels sur un canevas partagé via :

\*   Un bot Discord (commandes slash).

\*   Une interface web interactive.



Ce document décrit l'architecture, les choix techniques, la configuration et le déploiement de la solution sur \*\*Amazon Web Services (AWS)\*\*.



\## 🏗️ Architecture Générale (Vue d'ensemble)



Le système est conçu selon des principes \*\*serverless\*\*, \*\*event-driven\*\* et \*\*asynchrones\*\*. Toutes les interactions passent par une couche d'API Gateway, puis sont traitées de manière découplée via des files d'attente et des fonctions Lambda.



```mermaid

graph TD

&nbsp;   subgraph "Clients"

&nbsp;       A\[Utilisateur Discord] --> B\[Interaction Discord (Slash Commands)]

&nbsp;       C\[Utilisateur Web] --> D\[Application Web Statique S3/CloudFront]

&nbsp;   end



&nbsp;   subgraph "Couche d'Entrée \& Authentification"

&nbsp;       B --> E\[AWS API Gateway REST]

&nbsp;       D -- "Requêtes API (AJAX/Fetch)" --> F\[AWS API Gateway REST / WebSocket?]

&nbsp;       F -- "Authentification OAuth2" --> G\[Lambda: Auth Handler]

&nbsp;       G --> H\[(DynamoDB - Users)]

&nbsp;   end



&nbsp;   subgraph "Traitement Asynchrone (Pipeline Cœur)"

&nbsp;       E --> I\[Lambda: Discord Proxy]

&nbsp;       F --> J\[Lambda: Web Proxy]

&nbsp;       I --> K\[Amazon EventBridge / SQS]

&nbsp;       J --> K

&nbsp;       K --> L\[Lambda: Worker - Draw Pixel]

&nbsp;       L --> M\[(ElastiCache Valkey - Canvas Chunks)]

&nbsp;       L --> N\[(DynamoDB - Canvas Metadata/Users)]

&nbsp;   end



&nbsp;   subgraph "Stockage \& Services Supports"

&nbsp;       M

&nbsp;       N

&nbsp;       O\[(S3 - Snapshots)]

&nbsp;       P\[CloudWatch Logs / Metrics]

&nbsp;   end



&nbsp;   subgraph "Tâches Planifiées"

&nbsp;       Q\[EventBridge Scheduler] --> R\[Lambda: Snapshot Generator]

&nbsp;       R --> O

&nbsp;   end



&nbsp;   L -- "Logs \& Traces" --> P

&nbsp;   R -- "Logs \& Traces" --> P

&nbsp;   G -- "Logs \& Traces" --> P

&nbsp;   I -- "Logs \& Traces" --> P



&nbsp;   style A fill:#c9f,stroke:#333,stroke-width:2px

&nbsp;   style C fill:#c9f,stroke:#333,stroke-width:2px

&nbsp;   style E fill:#f9f,stroke:#333,stroke-width:2px

&nbsp;   style F fill:#f9f,stroke:#333,stroke-width:2px

&nbsp;   style K fill:#ff9,stroke:#333,stroke-width:2px

&nbsp;   style L fill:#9cf,stroke:#333,stroke-width:2px

&nbsp;   style M fill:#d95,stroke:#333,stroke-width:2px

&nbsp;   style N fill:#d95,stroke:#333,stroke-width:2px

&nbsp;   style O fill:#d95,stroke:#333,stroke-width:2px

