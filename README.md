# C3: Cloud-Native & Serverless - Collaborative Pixel Canvas (r/place Clone)

## Présentation du Projet

Bienvenue dans la documentation officielle du projet **C3**. Ce projet a pour objectif de concevoir et d'implémenter un prototype fonctionnel d'une plateforme de dessin collaboratif multijoueur, entièrement serverless et inspirée de Reddit's r/place.

Les utilisateurs peuvent dessiner des pixels sur un canevas partagé via :

- Un bot Discord (commandes slash).
- Une interface web interactive.

Ce document décrit l'architecture, les choix techniques, la configuration et le déploiement de la solution sur **Amazon Web Services (AWS)**.

## Architecture Générale (Vue d'ensemble)

Le système est conçu selon des principes **serverless**, **event-driven** et **asynchrones**. Toutes les interactions passent par une couche d'API Gateway, puis sont traitées de manière découplée via des files d'attente SQS et des fonctions Lambda.

```mermaid
graph TD
    subgraph "Clients"
        A[Utilisateur Discord] --> B[Interaction Discord - Slash Commands]
        C[Utilisateur Web] --> D[Application Web Statique S3/CloudFront]
    end

    subgraph "Couche d'Entrée & Authentification"
        B --> E[AWS API Gateway REST]
        D -- "Requêtes API (AJAX/Fetch)" --> F[AWS API Gateway REST / WebSocket]
        F -- "Authentification OAuth2" --> G[Lambda: Auth Handler]
        G --> H[(DynamoDB - Users)]
    end

    subgraph "Traitement Asynchrone (Pipeline Coeur)"
        E --> I[Lambda: Discord Proxy]
        F --> J[Lambda: Web Proxy]
        I --> K[Amazon EventBridge / SQS]
        J --> K
        K --> L[Lambda: Worker]
        L --> N[(DynamoDB - Canvas Metadata/Users)]
    end

    subgraph "Stockage & Services Supports"
        N
        O[(S3 - Snapshots)]
        P[CloudWatch Logs / Metrics]
    end

    L -- "Logs & Traces" --> P
    G -- "Logs & Traces" --> P
    I -- "Logs & Traces" --> P

    style A fill:#c9f,stroke:#333,stroke-width:2px
    style C fill:#c9f,stroke:#333,stroke-width:2px
    style E fill:#f9f,stroke:#333,stroke-width:2px
    style F fill:#f9f,stroke:#333,stroke-width:2px
    style K fill:#ff9,stroke:#333,stroke-width:2px
    style L fill:#9cf,stroke:#333,stroke-width:2px
    style N fill:#d95,stroke:#333,stroke-width:2px
    style O fill:#d95,stroke:#333,stroke-width:2px
```
