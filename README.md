# OptiLinéaire

Application web pour la résolution de problèmes de **programmation linéaire** via la méthode du Simplexe et la méthode des deux phases.

---

## 📋 Description

**OptiLinéaire** est une application Django interactive qui permet de :

- Résoudre des problèmes de la forme :  
  `max/min Z = c^T · x   s.c.   Ax ≤ b,  x ≥ 0`
- Choisir la méthode de résolution : Simplexe standard ou méthode des deux phases
- Visualiser chaque étape du calcul (tableaux, pivot, opérations élémentaires)
- Détecter automatiquement les cas dégénérés (problème non borné, infaisable)

---

## ✨ Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| 📊 Saisie interactive | Nombre de variables et de contraintes personnalisable |
| ➕ Types de contraintes | ≤, ≥ et = supportés |
| 🎯 Objectif | Maximisation ou minimisation |
| 🎲 Remplissage aléatoire | Génère un exemple instantanément pour tester |
| ⚙️ Choix de méthode | Simplexe standard, méthode des deux phases, ou automatique |
| 🔍 Visualisation pas-à-pas | Chaque itération avec pivot mis en évidence et opérations élémentaires |
| ⚠️ Cas particuliers | Détection : non borné, infaisable, origine non admissible |
| 📱 Interface responsive | Design Bootstrap, compatible mobile |
| 🌓 Mode clair/sombre | Thème commutable côté client |

---

## 🚀 Installation et lancement

### Prérequis

- **Python 3.8+**
- **pip**

---

### Méthode 1 — Téléchargement ZIP (sans Git)

1. Sur la page GitHub du projet, cliquez sur **Code → Download ZIP**
2. Décompressez l'archive et ouvrez un terminal dans le dossier extrait :
   ```bash
   cd OptiLineaire-main
   ```
3. Créez et activez un environnement virtuel :
   ```bash
   python -m venv myenv

   # Windows
   myenv\Scripts\activate

   # Linux / macOS
   source myenv/bin/activate
   ```
4. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
5. Appliquez les migrations :
   ```bash
   python manage.py migrate
   ```
6. Lancez le serveur :
   ```bash
   python manage.py runserver
   ```
7. Ouvrez votre navigateur à l'adresse : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

### Méthode 2 — Git clone (recommandée)

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/Samito-05/OptiLineaire.git
   cd OptiLineaire
   ```
2. Créez et activez un environnement virtuel :
   ```bash
   python -m venv myenv

   # Windows
   myenv\Scripts\activate

   # Linux / macOS
   source myenv/bin/activate
   ```
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Appliquez les migrations :
   ```bash
   python manage.py migrate
   ```
5. Lancez le serveur :
   ```bash
   python manage.py runserver
   ```
6. Ouvrez : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

### Méthode 3 — GitHub CLI (`gh`)

Si vous avez l'outil [GitHub CLI](https://cli.github.com/) installé :

```bash
gh repo clone Samito-05/OptiLineaire
cd OptiLineaire
python -m venv myenv && source myenv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

### Méthode 4 — pip + venv en une seule ligne (Linux/macOS)

Pour les utilisateurs avancés, voici une commande combinée :

```bash
git clone https://github.com/Samito-05/OptiLineaire.git && cd OptiLineaire && python -m venv myenv && source myenv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py runserver
```

---

## 📖 Utilisation

### Étape 1 — Configurer le problème

- Choisir le **nombre de variables** (`n`) et le **nombre de contraintes** (`m`)
- Sélectionner le **type d'objectif** : Maximisation ou Minimisation
- Choisir la **méthode** :
  - `Simplexe` : méthode standard (nécessite b ≥ 0)
  - `Deux phases` : force la méthode des deux phases
  - `Automatique` : détecte automatiquement et bascule vers les deux phases si nécessaire
- Saisir les **coefficients** de la fonction objectif `c`
- Saisir les coefficients des contraintes `A`, les **opérateurs** (≤, ≥, =) et les membres droits `b`

> 💡 Utilisez le bouton **"Remplissage aléatoire"** pour générer un exemple automatiquement.

### Étape 2 — Résoudre

Cliquez sur **"Résoudre"** pour lancer l'algorithme.

### Étape 3 — Lire les résultats

La page de résultats affiche :

- **Formulation du problème** : rappel de l'objectif et des contraintes saisies
- **Tableau initial** : tableau du simplexe avant toute itération
- **Itérations détaillées** :
  - Variable entrante et variable sortante identifiées
  - Tableau après pivotage (pivot mis en évidence en couleur)
  - Ratios calculés pour chaque ligne
  - Opérations élémentaires ligne par ligne (normalisation + éliminations)
- **Solution optimale** : valeur de Z* et valeurs de chaque variable `xᵢ`

Pour la **méthode des deux phases**, les résultats de Phase 1 et Phase 2 sont affichés séparément.

---

## 📁 Structure du projet

```
OptiLineaire/
├── manage.py                        # Point d'entrée Django
├── requirements.txt                 # Dépendances Python
├── db.sqlite3                       # Base de données SQLite (créée après migrate)
│
├── OptiLineaire/                    # Configuration du projet Django
│   ├── settings.py                  # Paramètres Django (DEBUG, INSTALLED_APPS, etc.)
│   ├── urls.py                      # Routes racines
│   ├── wsgi.py                      # Interface WSGI (déploiement)
│   └── asgi.py                      # Interface ASGI (async)
│
└── pb_lineaire/                     # Application principale
    ├── apps.py                      # Configuration de l'app
    ├── models.py                    # Modèles Django (vide — pas de BDD métier)
    ├── admin.py                     # Interface d'administration Django
    ├── views.py                     # Contrôleurs HTTP (logique de la vue)
    ├── urls.py                      # Routes de l'application
    ├── simplex.py                   # Algorithme du Simplexe standard
    ├── simplex_two_phase.py         # Algorithme des deux phases
    │
    ├── templatetags/
    │   ├── __init__.py
    │   └── math_notation.py         # Filtres Django pour la notation mathématique
    │
    ├── templates/pb_lineaire/
    │   ├── base.html                # Template de base (navbar, thème)
    │   ├── index.html               # Formulaire de saisie
    │   ├── result.html              # Résultats Simplexe standard
    │   ├── result_two_phase.html    # Résultats méthode des deux phases
    │   └── _iterations.html        # Sous-template : tableau des itérations
    │
    ├── static/pb_lineaire/
    │   └── global.css               # Styles (variables CSS, mode clair/sombre)
    │
    └── migrations/                  # Migrations Django
```

---

## 🔧 Dépendances

| Package | Version | Rôle |
|---|---|---|
| `Django` | 5.2.6 | Framework web Python |

> Aucune dépendance externe supplémentaire — tout le calcul (Simplexe, deux phases) est implémenté en pur Python avec le module standard `fractions`.

---

## 🧮 Algorithmes

### Simplexe standard — `simplex.py`

**Fonction publique : `run_simplex(c, A, b)`**

| Paramètre | Type | Description |
|---|---|---|
| `c` | `list[Fraction]` | Coefficients de la fonction objectif (maximisation) |
| `A` | `list[list[Fraction]]` | Matrice des contraintes |
| `b` | `list[Fraction]` | Membres droits (doit être ≥ 0) |

**Retourne** un dictionnaire avec :
- `status` : `"optimal"`, `"unbounded"`, ou `"non_admissible"`
- `optimal_value` : valeur de Z* (en chaîne fractionnaire)
- `solution` : dictionnaire `{xᵢ: valeur}`
- `iterations` : liste des snapshots de tableaux

**Fonctions internes :**

| Fonction | Rôle |
|---|---|
| `_simplex_core(tableau, basis, ...)` | Moteur du simplexe réutilisable par les deux phases |
| `_snapshot(tableau, basis, ...)` | Construit la représentation d'un tableau pour le template |
| `_compute_pivot_steps(...)` | Calcule les opérations élémentaires de pivotage |
| `fmt(f)` | Formate une `Fraction` en chaîne lisible (`"3"` ou `"5/2"`) |

**Déroulement de l'algorithme :**

1. Ajout des variables d'écart `y₁, …, yₘ` (base initiale)
2. À chaque itération :
   - Sélection de la **variable entrante** : colonne avec le plus grand coefficient positif dans la ligne objectif (LF)
   - Sélection de la **variable sortante** : ligne avec le ratio minimum `b[i] / A[i][col]`
   - **Pivotage** : normalisation de la ligne pivot + éliminations dans toutes les autres lignes
3. Critère d'arrêt : tous les coefficients LF ≤ 0 (optimalité)

---

### Méthode des deux phases — `simplex_two_phase.py`

**Fonction publique : `run_two_phase(c, A, b)`**

Même signature que `run_simplex`. Utilisée quand certains `bᵢ < 0` (l'origine n'est pas admissible).

**Phase 1 :**
- Pour chaque contrainte avec `bᵢ < 0`, la ligne est multipliée par −1 et une **variable artificielle** `aⱼ` est ajoutée
- On résout `min Σ aⱼ` (équivalent à `max −Σ aⱼ`) via `_simplex_core`
- Si la somme minimale > 0 → le problème est **infaisable**

**Phase 2 :**
- Les colonnes artificielles sont supprimées du tableau
- La fonction objectif originale est restaurée
- On relance `_simplex_core` depuis la base admissible trouvée en Phase 1

**Retourne** un dictionnaire enrichi avec les clés `phase1` et `phase2`, chacune contenant ses propres itérations.

---

### Filtres de notation mathématique — `templatetags/math_notation.py`

| Filtre | Exemple d'usage | Résultat |
|---|---|---|
| `math_var` | `{{ "x1" \| math_var }}` | `$x_{1}$` (LaTeX pour MathJax) |
| `math_text` | `{{ "L(y1) ← L(y1) ÷ 6" \| math_text }}` | Texte avec variables remplacées par LaTeX |
| `math_index` | `{{ 3 \| math_index:"x" }}` | `$x_{3}$` |

---

### Vues — `views.py`

| Fonction | Route | Description |
|---|---|---|
| `index(request)` | `GET /` | Affiche le formulaire de saisie |
| `solve(request)` | `POST /solve/` | Parse les données du formulaire, choisit la méthode et retourne les résultats |
| `_solve_two_phase(...)` | (interne) | Délègue à `run_two_phase` et construit le contexte |
| `_build_context(...)` | (interne) | Construit le dictionnaire de contexte commun pour les templates |

La vue `solve` gère automatiquement :
- La conversion des contraintes `≥` en `≤` (multiplication par −1)
- La conversion minimisation → maximisation (négation des coefficients `c`)
- Le routage vers `run_two_phase` si `method == "auto"` et que des `bᵢ < 0` sont détectés

---

## 📝 Exemple

**Problème :**
```
max Z = 3·x₁ + 2·x₂
s.c.
  2·x₁ +  x₂ ≤ 100
   x₁ +  x₂ ≤  80
  x₁, x₂ ≥ 0
```

**Procédure :**
1. Aller sur [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
2. Choisir **2 variables**, **2 contraintes**
3. Sélectionner **Maximisation** et méthode **Simplexe**
4. Entrer `c = [3, 2]`, puis les lignes de `A` et `b`
5. Cliquer **"Résoudre"**

**Résultat attendu :** Z* = 220, x₁ = 20, x₂ = 60

---

## 🐛 Dépannage

| Problème | Solution |
|---|---|
| Port déjà utilisé | `python manage.py runserver 8001` |
| Erreur de migration | `python manage.py migrate --fake-initial` |
| Réinitialiser la base de données | `rm db.sqlite3 && python manage.py migrate` |
| Module introuvable | Vérifiez que votre environnement virtuel est activé |

---

## 📄 Licence

Ce projet est fourni à titre éducatif dans le cadre d'une SAE (Situation d'Apprentissage et d'Évaluation).

## 👤 Auteur

Développé pour l'apprentissage de la programmation linéaire et du développement web avec Django.

---

**Dernière mise à jour :** Avril 2026
