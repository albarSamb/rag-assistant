# Guide de Démarrage Rapide - DocuBot Backend

## Installation

### 1. Créer et activer l'environnement virtuel

```powershell
cd C:\Users\Dell\Documents\rag-assistant\backend
python -m venv venv
.\venv\Scripts\activate
```

Vous devriez voir `(venv)` apparaître dans votre terminal.

### 2. Installer les dépendances

```powershell
pip install -r requirements_simple.txt
```

Cette installation prendra quelques minutes (téléchargement de PyTorch, sentence-transformers, etc.)

## Tests

### Test 1 : Pipeline RAG automatique

```powershell
python test_rag_pipeline.py
```

**Ce que vous devriez voir** :
```
======================================================================
RAG PIPELINE END-TO-END TEST
======================================================================

Creating test document...
Created: tmp...md

Initializing RAG pipeline...
Pipeline ready

[*] Processing document...
[OK] Document processed successfully!
  - Chunks created: 8
  - Embedding dimension: 384

[*] Collection stats:
  - Total chunks: 8

======================================================================
TESTING QUERIES
======================================================================

Question 1: How do I create an authentication middleware with FastAPI?
...
[+] Found 3 relevant chunks:
  1. [Similarity: 0.xxx]
  ...

[SUCCESS] TEST COMPLETED SUCCESSFULLY!
```

### Test 2 : Votre propre document

Créez un fichier texte ou Markdown :

```powershell
# Créer un fichier test
@"
# Mon Document Test

## Introduction
Ceci est un document de test pour le système RAG.

## Contenu
Le système peut extraire des informations de ce document.
"@ | Out-File -FilePath test.md -Encoding UTF8
```

Testez-le :

```powershell
python quick_test.py test.md
```

Le script vous demandera une question, par exemple :
- "De quoi parle ce document ?"
- "Qu'est-ce qu'un système RAG ?"

### Test 3 : Tests unitaires

```powershell
pytest tests/test_chunker.py -v
```

Vous devriez voir tous les tests passer (✓).

### Test 4 : API FastAPI

Lancer le serveur :

```powershell
uvicorn app.main:app --reload
```

Ouvrir dans le navigateur :
- http://localhost:8000 → Message de bienvenue
- http://localhost:8000/health → Status de l'API
- http://localhost:8000/docs → Documentation interactive Swagger

## Vérification de l'Installation

Pour vérifier que tout fonctionne :

```powershell
python -c "import fastapi; import chromadb; import sentence_transformers; print('[OK] All packages imported')"
```

Si aucune erreur → tout est bon !

## Dossiers Créés

Après le premier test, vous verrez :
- `chroma_data/` → Base de données vectorielle ChromaDB
- `uploads/` → Stockage des fichiers uploadés (vide pour l'instant)

Ces dossiers sont ignorés par git (.gitignore).

## Troubleshooting

### Erreur "ModuleNotFoundError"
→ L'environnement virtuel n'est pas activé ou les dépendances ne sont pas installées
```powershell
.\venv\Scripts\activate
pip install -r requirements_simple.txt
```

### Erreur "UnicodeEncodeError"
→ Problème d'encodage Windows, déjà corrigé dans le code

### ChromaDB ne démarre pas
→ Vérifier que le dossier `chroma_data/` est accessible en écriture

### Le modèle d'embedding se télécharge
→ Normal au premier lancement (all-MiniLM-L6-v2, ~90MB)
→ Il sera mis en cache pour les prochains tests

## Prochaines Étapes

Une fois que tous les tests passent, on peut continuer avec :
- Modèles PostgreSQL (users, documents, conversations)
- Authentification JWT
- API endpoints (upload, chat, etc.)
- Frontend Vue.js

## Désactiver l'environnement virtuel

Quand vous avez fini :
```powershell
deactivate
```
