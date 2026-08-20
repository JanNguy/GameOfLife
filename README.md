# GameOfLife

Simulation multi-agents fondée sur des profils démographiques, un modèle de décision et des scénarios textuels. Pour chaque scénario, le système génère des questions binaires, évalue les décisions des agents puis produit une synthèse globale.

## Architecture

```text
data_part/ -> ml_part/ -> game/ -> serveur/ -> Client/
 données       modèle      agents    API SSE     terminal React
```

1. `data_part` transforme le jeu de données UCI Adult Income en profils démographiques.
2. `ml_part` entraîne les modèles de décision et écrit les artefacts dans `ml_part/out/models/`.
3. `game` génère une population d'agents et simule leurs décisions pour un scénario.
4. `serveur` expose la simulation via FastAPI, dont une sortie SSE pour le terminal web.
5. `Client` fournit l'interface terminal React/Vite.

## Prérequis

- Python 3.11
- Node.js et pnpm
- Le fichier `data_part/Data/train.csv` (déjà présent dans le projet)

Les dépendances Python utilisent un environnement virtuel unique à la racine : `.venv`.

## Démarrage rapide

Depuis la racine du dépôt :

```bash
# Installe les dépendances Python dans .venv
make setup

# Installe les dépendances du client React
make client-setup

# Lance FastAPI et Vite ensemble
make dev
```

Ouvrir ensuite `http://localhost:5173`. La cible `make dev` lance FastAPI sur `http://127.0.0.1:8000` et Vite configure le proxy `/exec` vers cette API.

Pour préparer les données, entraîner les modèles et exécuter une première simulation locale :

```bash
make all
```

## Simulation

La commande principale accepte le nombre d'agents, suivi du scénario libre :

```bash
.venv/bin/python game/game.py --n 10 --scenario "la planete ne tourne plus sur elle meme"
```

Elle effectue les opérations suivantes :

1. Échantillonne les agents depuis `data_part/out/out_profiles.csv`.
2. Propose des questions de décision binaires adaptées au scénario.
3. Évalue chaque question pour chaque agent avec le moteur de décision.
4. Déroule une histoire en trois actes et conserve une branche narrative par agent.
5. Classe les agents par survie, patrimoine final et stabilité.

Par exemple, pour un crash boursier, les agents perdent d'abord une part de leur patrimoine. Les agents qui investissent pendant la baisse et adaptent leur travail peuvent récupérer davantage à la reprise ; le classement final affiche alors les patrimoines restants et le statut de survie. Pour une apocalypse (`fin du monde`, `catastrophe nucléaire`, `météorite`, etc.), les ressources et la stabilité sont fortement diminuées : les agents sans abri, réserves ou activité résiliente peuvent disparaître. Le bilan final indique le nombre de survivants et de disparus.

Le fichier généré `game/agents.json` est un artefact local ignoré par Git.

## Interface terminal

Dans le navigateur, les commandes disponibles sont :

| Commande | Description |
|---|---|
| `run <nb_agents> <scenario>` | Génère les agents et exécute une simulation. Exemple : `run 10 plus d'eau sur terre`. |
| `setup` | Exécute le prétraitement des données. |
| `data` | Relance le prétraitement des données. |
| `model` | Liste les modèles entraînés ; `model <nom.keras>` sélectionne un modèle. |
| `clean` | Supprime les caches Python du module de jeu. |
| `fclean` | Nettoie les artefacts du projet. |
| `clear` | Efface le terminal. |
| `help` | Affiche l'aide intégrée. |

La commande `run` est transmise en SSE à `GET /exec/run/<nb_agents>/<scenario>`. L'API relaie au navigateur la sortie de la simulation au fil de son exécution.

## API FastAPI

| Endpoint | Description |
|---|---|
| `GET /exec/{command}` | Exécute une commande du terminal et diffuse la sortie au format SSE. |
| `GET /scenario/questions?context=...` | Retourne les questions binaires d'un contexte. |
| `POST /scenario/questions` | Génère les questions pour `{ "context": "...", "max_questions": 5 }`. |
| `POST /scenario/run` | Simule les décisions pour un tableau `agents` et un `scenario`. |

L'API peut aussi être lancée seule :

```bash
make serveur
```

Le client peut être lancé seul lorsque l'API est déjà active :

```bash
make client
```

## Génération des questions avec Ollama

Par défaut, le projet utilise une banque locale de questions binaires. Pour demander à Ollama Cloud de proposer des questions contextualisées :

```bash
cp serveur/.env.example serveur/.env
```

Renseigner ensuite `OLLAMA_KEY` dans `serveur/.env`. Les variables optionnelles sont :

```dotenv
OLLAMA_KEY=
OLLAMA_BASE_URL=https://api.ollama.com/v1
OLLAMA_MODEL=deepseek-v4-flash:cloud
```

Le fichier `serveur/.env` est ignoré par Git. Ne le versionnez jamais. En l'absence de clé ou si l'appel distant échoue, le système revient automatiquement au générateur local.

## Commandes Make

| Commande | Description |
|---|---|
| `make setup` | Crée ou actualise l'environnement Python et les dépendances. |
| `make data` | Transforme les données source. |
| `make ml` | Entraîne les modèles de décision. |
| `make game` | Génère les agents et lance le scénario par défaut. |
| `make all` | Exécute `data`, `ml` et `game`. |
| `make dev` | Lance FastAPI et Vite ensemble. |
| `make clean` | Supprime les artefacts temporaires. |
| `make fclean` | Supprime aussi les sorties, `.venv` et les dépendances client. |

## Vérification

```bash
# Tests du générateur de questions
.venv/bin/python -m unittest game.test_scenario_orchestrator

# Build du client
cd Client && pnpm build
```

## Stack

| Couche | Technologies |
|---|---|
| Données | Python, pandas |
| Modélisation | TensorFlow/Keras, scikit-learn |
| Simulation | Python, moteur de décisions binaires |
| API | FastAPI, Uvicorn, SSE |
| Client | React 19, TypeScript, Vite |
