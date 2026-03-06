# C3: Cloud-Native & Serverless - Collaborative Pixel Canvas (r/place Clone)



## Présentation du Projet



Bienvenue dans la documentation officielle du projet **C3**. Ce projet a pour objectif de concevoir et d'implémenter un prototype fonctionnel d'une plateforme de dessin collaboratif multijoueur, entièrement serverless et inspirée de Reddit's r/place.



Les utilisateurs peuvent dessiner des pixels sur un canevas partagé via :

*   Un bot Discord (commandes slash).

*   Une interface web interactive.



Ce document décrit l'architecture, les choix techniques, la configuration et le déploiement de la solution sur **Amazon Web Services (AWS)**.



## Architecture Générale (Vue d'ensemble)



Le système est conçu selon des principes **serverless**, **event-driven** et **asynchrones**. Toutes les interactions passent par une couche d'API Gateway, puis sont traitées de manière découplée via des files d'attente et des fonctions Lambda.



```mermaid
graph TD
    subgraph Clients
        A[Utilisateur Discord] --> B[Interaction Discord]
        C[Utilisateur Web] --> D[App Web S3/CloudFront]
    end

    subgraph "Couche d'Entree & Auth"
        B --> E[API Gateway REST]
        D --> F[API Gateway REST]
        F --> G[Lambda: Auth Handler]
        G --> H[(DynamoDB Users)]
    end

    subgraph "Traitement Asynchrone"
        E --> I[Lambda: Discord Proxy]
        F --> J[Lambda: Web Proxy]
        I --> K[EventBridge/SQS]
        J --> K
        K --> L[Lambda: Worker Draw]
        L --> M[(ElastiCache Valkey)]
        L --> N[(DynamoDB Metadata)]
    end

    subgraph "Stockage & Services"
        M
        N
        O[(S3 Snapshots)]
        P[CloudWatch]
    end

    subgraph "Taches Planifiees"
        Q[EventBridge Scheduler] --> R[Lambda: Snapshot]
        R --> O
    end

    L --> P
    R --> P
    G --> P
    I --> P

    style A fill:#c9f,stroke:#333
    style C fill:#c9f,stroke:#333
    style E fill:#f9f,stroke:#333
    style F fill:#f9f,stroke:#333
    style K fill:#ff9,stroke:#333
    style L fill:#9cf,stroke:#333
    style M fill:#d95,stroke:#333
    style N fill:#d95,stroke:#333
    style O fill:#d95,stroke:#333
```
