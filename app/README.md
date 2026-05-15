# Coursify Backend

API REST pour la plateforme de gestion de cours en ligne Coursify.

## Technologies

- **Python 3.11**
- **FastAPI** — Framework web moderne et performant
- **SQLAlchemy** — ORM pour la base de données
- **PostgreSQL** — Base de données en production
- **SQLite** — Base de données en développement
- **JWT** — Authentification par token
- **nbconvert** — Conversion des notebooks Jupyter en HTML

## Prérequis

- Python 3.11+
- pip

## Installation

```bash
# Cloner le projet
git clone https://github.com/TON_USERNAME/coursify-backend.git
cd coursify-backend

# Créer et activer l'environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Copier le fichier d'environnement
cp .env.example .env
# Modifier .env avec vos valeurs
```

## Lancement

```bash
uvicorn app.main:app --reload
```

L'API est accessible sur `http://127.0.0.1:8000`
La documentation Swagger est disponible sur `http://127.0.0.1:8000/docs`

## Compte admin par défaut

Au premier démarrage, un compte administrateur est créé automatiquement avec les identifiants définis dans `.env` :

```
Email    : admin@coursify.bj
Password : Admin2026
```

## Structure du projet

```
coursify-backend/
├── app/
│   ├── main.py          # Point d'entrée, configuration CORS, seed admin
│   ├── database.py      # Configuration base de données
│   ├── models/          # Modèles SQLAlchemy
│   │   ├── user.py      # Modèle utilisateur
│   │   └── course.py    # Modèle cours
│   ├── schemas/         # Schémas Pydantic
│   │   ├── user.py
│   │   └── course.py
│   ├── routers/         # Routes API
│   │   ├── auth.py      # Authentification
│   │   ├── users.py     # Gestion utilisateurs
│   │   └── courses.py   # Gestion cours
│   ├── services/        # Logique métier
│   │   ├── auth.py
│   │   └── course.py
│   └── core/            # Configuration centrale
│       ├── config.py    # Variables d'environnement
│       ├── security.py  # JWT, hachage mots de passe
│       └── deps.py      # Dépendances FastAPI
├── uploads/             # Fichiers uploadés
├── .env.example         # Template variables d'environnement
├── requirements.txt     # Dépendances Python
└── README.md
```

## Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/login` | Connexion |
| GET | `/api/auth/me` | Utilisateur connecté |
| GET | `/api/courses/` | Liste des cours publics |
| GET | `/api/courses/popular` | Cours populaires |
| GET | `/api/courses/my-courses` | Cours de l'enseignant |
| GET | `/api/courses/{slug}` | Détail d'un cours |
| POST | `/api/courses/` | Créer un cours |
| PUT | `/api/courses/{id}/full` | Modifier un cours |
| DELETE | `/api/courses/{id}` | Supprimer un cours |
| POST | `/api/courses/{id}/duplicate` | Dupliquer un cours |
| GET | `/api/users/` | Liste utilisateurs (admin) |
| POST | `/api/users/` | Créer un utilisateur (admin) |
| GET | `/api/users/stats` | Statistiques plateforme (admin) |

## Déploiement

Le projet est configuré pour Railway. Voir la section déploiement dans la documentation.