# OptiLinéaire

Application web pour la résolution de problèmes de **programmation linéaire et entière** : méthode du Simplexe, méthode des deux phases, coupes de Gomory et Branch-and-Bound.

---

## 📋 Description

**OptiLinéaire** est une application Django interactive qui permet de :

- Résoudre des problèmes de la forme :
  `max/min Z = c^T · x   s.c.   Ax ≤ b,  x ≥ 0`  (avec option `x ∈ ℤ`)
- **Choisir la méthode automatiquement** selon la structure du problème
  (Simplexe si l'origine est admissible, deux phases sinon)
- Résoudre les problèmes en **variables entières** par **coupes de Gomory** ou **Branch-and-Bound**
- Visualiser **chaque étape du calcul** : tableaux, pivots, opérations élémentaires,
  dérivation des coupes, arbre d'exploration
- Détecter les cas particuliers (non borné, infaisable, origine non admissible)

Tout le calcul est effectué en **arithmétique rationnelle exacte** (`fractions.Fraction`) — aucun flottant.

---

## ✨ Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| 📊 Saisie interactive | De 1 à 30 variables et contraintes ; entiers, décimaux (`2.5` ou `2,5`) et fractions (`1/3`) |
| 💾 Saisie conservée | Les valeurs restent quand on change la taille du problème, après une erreur, et via « Modifier le problème » |
| ➕ Types de contraintes | ≤, ≥ et = supportés ; la **forme standard résolue** (max, ≤) est affichée quand elle diffère de la saisie |
| 🎯 Objectif | Maximisation ou minimisation |
| 🔢 Variables entières | Interrupteur dédié + choix entre coupes de Gomory et Branch-and-Bound |
| ⚙️ Sélection automatique | Simplexe si tous les `bᵢ ≥ 0`, deux phases sinon — expliqué par un bandeau « Choix de méthode » |
| 🎲 Remplissage aléatoire | Génère un exemple instantanément pour tester |
| 🔍 Visualisation pas-à-pas | Itérations avec pivot mis en évidence, opérations ligne par ligne, étapes de coupe numérotées, arbre B&B |
| ⚠️ Cas particuliers | Détection : non borné, infaisable ; anti-cyclage (règle de Bland sur sommet dégénéré) ; bascule automatique Gomory → Branch-and-Bound |
| 📴 Hors ligne | Bootstrap, MathJax et polices servis localement — aucun CDN |
| 📱 Interface responsive | Design Bootstrap, compatible mobile |
| 🌓 Mode clair/sombre | Thème commutable côté client |

---

## 🚀 Installation et lancement

### Prérequis

- **Python 3.9+**
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
5. Lancez le serveur :
   ```bash
   python manage.py runserver
   ```
6. Ouvrez votre navigateur à l'adresse : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

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
4. Lancez le serveur :
   ```bash
   python manage.py runserver
   ```
5. Ouvrez : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

### Méthode 3 — Scripts de lancement

```bash
# Windows
.\run.ps1

# Linux / macOS
./run.sh
```

---

> L'application ne stocke rien : pas de base de données, donc pas de migration.

### Configuration (optionnelle)

Par défaut, les réglages conviennent au développement local. Pour un déploiement :

| Variable | Rôle |
|---|---|
| `DJANGO_DEBUG=0` | Désactive le mode debug |
| `DJANGO_SECRET_KEY` | Clé secrète — obligatoire quand `DJANGO_DEBUG=0` |
| `DJANGO_ALLOWED_HOSTS` | Hôtes autorisés, séparés par des virgules (défaut : `localhost,127.0.0.1,[::1]`) |

Avec `DJANGO_DEBUG=0`, `runserver` ne sert plus les fichiers statiques : lancez
`python manage.py collectstatic` et servez `staticfiles/` par le serveur web.

---

## 📖 Utilisation

### Étape 1 — Configurer le problème

- Choisir le **nombre de variables** (`n`) et le **nombre de contraintes** (`m`)
- Sélectionner le **type d'objectif** : Maximisation ou Minimisation
- (Optionnel) Activer **Variables entières** (`xⱼ ∈ ℤ`), puis choisir la méthode :
  - **Coupes de Gomory** : relaxation LP + coupes successives dérivées du tableau optimal
  - **Branch-and-Bound** : arbre d'exploration avec bornes et élagage
- Saisir les **coefficients** de la fonction objectif `c` — entiers, décimaux ou fractions (`1/3`)
- Saisir les coefficients des contraintes `A`, les **opérateurs** (≤, ≥, =) et les membres droits `b`

> 💡 La méthode continue (Simplexe ou deux phases) est **choisie automatiquement** :
> il n'y a pas de sélecteur à régler. Utilisez **« Remplissage aléatoire »** pour générer un exemple.

### Étape 2 — Résoudre

Cliquez sur **« Résoudre »**.

### Étape 3 — Lire les résultats

Chaque page de résultats commence par un bandeau **« Choix de méthode »** qui justifie
la méthode retenue (par exemple : `b₁ = −2 < 0` → deux phases), suivi du rappel du problème
et, si le problème a été transformé (min, ≥, =), de la **forme standard résolue**.
« Modifier le problème » revient au formulaire avec la saisie ; « Nouveau problème » repart de zéro.

**Simplexe / Deux phases :**
- Tableau initial, puis chaque itération : variable entrante (coefficient LF le plus positif),
  variable sortante (ratio minimum), pivot en évidence, opérations élémentaires détaillées
- Pour les deux phases : Phase 1 (problème auxiliaire avec l'artificielle unique **δ**)
  puis Phase 2 (objectif original), affichées séparément

**Coupes de Gomory :**
- Pour chaque coupe, les étapes du cours numérotées : solution de la relaxation, test
  d'intégrité, ligne source du tableau, **parties fractionnaires** `{aᵢⱼ}` en table,
  coupe `Σ{aᵢⱼ}·tⱼ ≥ {bᵢ}`, substitution des écarts, mise à l'échelle entière
  (arrondi de Chvátal–Gomory) et contrainte ajoutée
- Itérations de chaque relaxation consultables en repli
- Si les coupes n'aboutissent pas (15 coupes), **bascule automatique vers le Branch-and-Bound**,
  affiché à la suite

**Branch-and-Bound :**
- **Arbre d'exploration** dessiné (nœuds branché / solution entière ★ / élagué / infaisable)
- Détail de chaque nœud dans l'ordre d'exploration best-bound : contrainte de branchement,
  borne `Z_LP`, raison de l'élagage, relaxation LP en repli

---

## 📁 Structure du projet

```
OptiLineaire/
├── manage.py                        # Point d'entrée Django
├── requirements.txt                 # Dépendances Python
├── run.ps1 / run.sh                 # Scripts de lancement
│
├── OptiLineaire/                    # Configuration du projet Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
│
└── pb_lineaire/                     # Application principale
    ├── views.py                     # Parsing, normalisation ≤, sélection automatique
    ├── urls.py                      # Routes de l'application
    │
    ├── simplex.py                   # Moteur du Simplexe (tableaux, pivots, snapshots)
    ├── simplex_two_phase.py         # Méthode des deux phases (artificielle unique δ)
    ├── lp_relax.py                  # Relaxation LP automatique (Simplexe ou deux phases)
    ├── gomory.py                    # Coupes de Gomory (programmation entière)
    ├── branch_bound.py              # Branch-and-Bound (programmation entière)
    ├── tests.py                     # 44 tests unitaires
    │
    ├── templatetags/
    │   └── math_notation.py         # Filtres Django pour la notation mathématique (MathJax)
    │
    ├── templates/pb_lineaire/
    │   ├── base.html                # Template de base (navbar, thème)
    │   ├── index.html               # Formulaire de saisie
    │   ├── result.html              # Résultats Simplexe
    │   ├── result_two_phase.html    # Résultats deux phases
    │   ├── result_gomory.html       # Résultats coupes de Gomory
    │   ├── result_branch_bound.html # Résultats Branch-and-Bound (arbre + nœuds)
    │   ├── _iterations.html         # Sous-template : tableaux d'itérations
    │   ├── _lp_block.html           # Sous-template : une relaxation LP (simplexe ou 2 phases)
    │   ├── _problem.html            # Sous-template : bandeau méthode, rappel du problème, forme standard
    │   ├── _actions.html            # Sous-template : boutons Modifier / Nouveau problème
    │   ├── _bb_summary.html         # Sous-template : résultat global du B&B
    │   ├── _bb_body.html            # Sous-template : arbre + détail des nœuds B&B
    │   ├── _legend.html             # Sous-template : légende des couleurs
    │   └── _bb_node.html            # Sous-template récursif : nœud de l'arbre B&B
    │
    └── static/pb_lineaire/
        ├── global.css               # Styles (variables CSS, mode clair/sombre)
        └── vendor/                  # Bootstrap 5.3.3, MathJax 3.2.2 (SVG), polices — servis localement
```

---

## 🔧 Dépendances

| Package | Version | Rôle |
|---|---|---|
| `Django` | 5.2.6 | Framework web Python |

> Aucune dépendance externe supplémentaire — tout le calcul (Simplexe, deux phases,
> Gomory, Branch-and-Bound) est implémenté en pur Python avec le module standard `fractions`.
>
> Côté navigateur, `static/pb_lineaire/vendor/` embarque Bootstrap 5.3.3 (MIT),
> MathJax 3.2.2 (Apache 2.0) et les polices Bricolage Grotesque, Archivo et Space Mono (SIL OFL) :
> l'application fonctionne sans connexion Internet.

---

## 🧮 Algorithmes

### Convention de tableau (commune à toutes les méthodes)

- La ligne objectif (**LF**) contient les coûts réduits ; valeur de l'objectif = **−(coin bas-droit)**
- **Variable entrante** : coefficient **le plus positif** de la ligne LF
- **Variable sortante** : ratio minimum `bᵢ / aᵢⱼ` avec `aᵢⱼ > 0`
- **Anti-cyclage** : après un pivot dégénéré (ratio minimum nul), règle de **Bland**
  (plus petit indice) jusqu'au prochain pivot non dégénéré — signalée dans l'itération
- **Optimalité** : tous les coefficients LF ≤ 0
- Variables d'écart nommées `y₁, …, yₘ` ; minimisation résolue en interne comme `max(−c)`

### Simplexe — `simplex.py`

`run_simplex(c, A, b)` : résout `max c^T x, Ax ≤ b, x ≥ 0` quand tous les `bᵢ ≥ 0`.
Statuts : `optimal`, `unbounded`, `non_admissible`, `max_iter` (garde à 500 itérations).
Le moteur `_simplex_core` est réutilisé par toutes les autres méthodes.

`DetailBudget` borne le volume de détails enregistrés pour l'affichage (étapes de pivot,
puis tableaux) : une page de résultats reste de taille raisonnable même à 30 × 30.
Le calcul n'est jamais tronqué ; la page signale un « affichage allégé ».

### Deux phases — `simplex_two_phase.py`

`run_two_phase(c, A, b)` : utilisée quand certains `bᵢ < 0` (origine non admissible).

- **Phase 1** : une **seule variable artificielle δ** (colonne de −1 sur chaque ligne),
  objectif auxiliaire `max(−δ)`. δ est forcée en base par **un seul pivot** sur la ligne
  au RHS le plus négatif — tous les RHS deviennent ≥ 0 d'un coup.
  À l'optimum : `δ = 0` → admissible (passage en Phase 2) ; `δ > 0` → **infaisable**.
- **Phase 2** : suppression de la colonne δ, réexpression de l'objectif original,
  Simplexe standard depuis la base admissible.

### Coupes de Gomory — `gomory.py`

`run_gomory(c, A, b, minimize=False, max_cuts=15)` : programmation entière par plans coupants.

1. Résoudre la **relaxation LP** (Simplexe ou deux phases, choisi automatiquement)
2. Solution entière → terminé
3. Sinon : ligne source = variable de base la plus fractionnaire ;
   coupe `Σ{aᵢⱼ}·tⱼ ≥ {bᵢ}` à partir des **parties fractionnaires** de sa ligne
4. Réexpression en variables originales (substitution des écarts), puis
   **mise à l'échelle entière + arrondi de Chvátal–Gomory** `⌈D·g₀⌉` —
   indispensable pour que les écarts des coupes restent entiers et que les
   coupes suivantes soient valides
5. Ajout de la coupe au modèle et retour en 1

Au-delà de `max_cuts` coupes (ou si aucune coupe utile ne peut être dérivée), la vue
bascule automatiquement vers le Branch-and-Bound et affiche les deux.

### Branch-and-Bound — `branch_bound.py`

`run_branch_and_bound(c, A, b, minimize=False, max_nodes=100, time_limit=8.0)` : énumération arborescente.

- Sélection de nœud **best-bound**, branchement sur la **variable la plus fractionnaire** :
  fils `xⱼ ≤ ⌊v⌋` et `xⱼ ≥ ⌈v⌉`
- Élagage par : relaxation infaisable, borne ≤ incumbent, solution entière
  (mise à jour de l'incumbent + élagage des nœuds en attente dominés)
- Relaxation de chaque nœud résolue automatiquement (Simplexe ou deux phases)
- Résultat : arbre complet + détail des nœuds dans l'ordre d'exploration
- Limite de nœuds ou de temps atteinte → incumbent partiel affiché

### Sélection automatique — `views.py` + `lp_relax.py`

| Situation | Méthode choisie |
|---|---|
| Continu, tous les `bᵢ ≥ 0` (forme ≤) | Simplexe |
| Continu, un `bᵢ < 0` | Deux phases |
| Variables entières | Coupes de Gomory **ou** Branch-and-Bound (choix utilisateur) |

### Filtres de notation mathématique — `templatetags/math_notation.py`

| Filtre | Exemple d'usage | Résultat |
|---|---|---|
| `math_var` | `{{ "x1" \| math_var }}` | `$x_{1}$` (LaTeX pour MathJax) |
| `math_text` | `{{ "L(y1) ← L(y1) ÷ 6" \| math_text }}` | Texte avec variables remplacées par LaTeX |
| `math_index` | `{{ 3 \| math_index:"x" }}` | `$x_{3}$` |

---

## 🧪 Tests

```bash
python manage.py test pb_lineaire
```

**44 tests** couvrant les quatre méthodes (optimal, non borné, infaisable, minimisation,
données fractionnaires, coefficients de coupe entiers, anti-cyclage, budget d'affichage)
et les vues (routage, validation de la saisie, limites de taille, bascule Gomory → B&B).
Les méthodes entières ont en outre été validées par comparaison avec une énumération
exhaustive sur 190 instances aléatoires.

---

## 📝 Exemple

**Problème entier :**
```
max Z = 5·x₁ + 4·x₂
s.c.
  6·x₁ + 4·x₂ ≤ 24
   x₁ + 2·x₂ ≤  6
  x₁, x₂ ≥ 0,  x₁, x₂ ∈ ℤ
```

**Procédure :**
1. Aller sur [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
2. Choisir **2 variables**, **2 contraintes**, **Maximisation**
3. Activer **Variables entières** et choisir une méthode (Gomory ou Branch-and-Bound)
4. Entrer `c = [5, 4]`, puis les lignes de `A` et `b`
5. Cliquer **« Résoudre »**

**Résultat attendu :** relaxation LP `Z = 21` en `(3, 3/2)` (fractionnaire),
puis optimum entier **Z\* = 20 en (4, 0)**.

---

## 🐛 Dépannage

| Problème | Solution |
|---|---|
| Port déjà utilisé | `python manage.py runserver 8001` |
| « Affichage allégé » sur la page de résultats | Problème volumineux : le détail de certains pivots est masqué, le résultat reste exact |
| Module introuvable | Vérifiez que votre environnement virtuel est activé |

---

## 📄 Licence

Ce projet est fourni à titre éducatif dans le cadre d'une SAE (Situation d'Apprentissage et d'Évaluation).

## 👤 Auteur

Développé pour l'apprentissage de la programmation linéaire et du développement web avec Django.

---

**Dernière mise à jour :** Juin 2026
