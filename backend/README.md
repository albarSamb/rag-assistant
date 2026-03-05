# DocuBot Backend

Backend API pour DocuBot - Assistant de documentation technique avec RAG.

## Installation

1. Créer un environnement virtuel Python :
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Installer les dépendances :
```bash
cd backend
pip install -r requirements.txt
```

3. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

## Test du Pipeline RAG

Avant de lancer l'API, vous pouvez tester le pipeline RAG complet :

### Test automatique avec document de test
```bash
python test_rag_pipeline.py
```

Ce script va :
- Créer un document de test
- Le traiter (parsing → chunking → embedding → stockage)
- Effectuer des requêtes de test
- Afficher les résultats avec scores de similarité

### Test avec votre propre document
```bash
python quick_test.py path/to/your/document.pdf
```

Formats supportés : PDF, Markdown (.md), TXT, DOCX

Exemple :
```bash
# Créer un fichier test
echo "# Test\n\nCeci est un test." > test.md

# Tester
python quick_test.py test.md
```

## Lancer l'API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

L'API sera disponible sur http://localhost:8000

Documentation interactive : http://localhost:8000/docs

## Tests Unitaires

```bash
pytest
```

Avec coverage :
```bash
pytest --cov=app --cov-report=html
```

## Structure du Projet

```
backend/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration
│   ├── rag/                 # Pipeline RAG
│   │   ├── parser.py        # Extraction texte (PDF/MD/TXT)
│   │   ├── chunker.py       # Découpage intelligent
│   │   ├── embedder.py      # Vectorisation
│   │   ├── retriever.py     # ChromaDB
│   │   └── pipeline.py      # Pipeline complet
│   ├── models/              # SQLAlchemy models (à venir)
│   ├── schemas/             # Pydantic schemas (à venir)
│   ├── services/            # Business logic (à venir)
│   └── routers/             # API endpoints (à venir)
├── tests/
│   └── test_chunker.py
├── test_rag_pipeline.py     # Test end-to-end
└── requirements.txt
```

## Pipeline RAG

### 1. Parser
Extrait le texte depuis différents formats :
- PDF (PyPDF2 + pdfplumber fallback)
- Markdown
- TXT
- DOCX

### 2. Chunker
Découpe le texte en chunks avec overlap :
- Taille par défaut : 512 caractères
- Overlap : 50 caractères
- Stratégie récursive (paragraphes → lignes → phrases → mots)

### 3. Embedder
Vectorise le texte avec `sentence-transformers` :
- Modèle : `all-MiniLM-L6-v2`
- Dimension : 384
- Rapide et performant

### 4. Retriever
Stocke et recherche avec ChromaDB :
- Distance cosinus
- Collections par utilisateur
- Persistance locale

## Prochaines Étapes

- [ ] Modèles de base de données (PostgreSQL)
- [ ] Système d'authentification (JWT)
- [ ] API endpoints (upload, chat, etc.)
- [ ] Intégration Claude API pour génération
- [ ] Streaming SSE pour le chat

## Technologies

- FastAPI
- ChromaDB
- sentence-transformers (all-MiniLM-L6-v2)
- PyPDF2 + pdfplumber
- SQLAlchemy (async)
- PostgreSQL
