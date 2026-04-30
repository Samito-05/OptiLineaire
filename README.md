# OptiLinéaire

Application web pour la résolution de problèmes de programmation linéaire par la **méthode du Simplexe**.

## 📋 Description

OptiLinéaire est une application Django interactive qui permet de résoudre des problèmes de programmation linéaire sous forme standard :

- **max/min Z = c^T · x**
- **s.c. Ax ≤ b, x ≥ 0**

L'application implémente la méthode du Simplexe et affiche de manière pédagogique toutes les étapes du calcul, avec :
- Tableaux détaillés du simplexe à chaque itération
- Identification des variables entrantes et sortantes
- Explication pas-à-pas du pivotage
- Visualisation des ratios pour la sélection du pivot

## ✨ Fonctionnalités

- 📊 Saisie interactive du problème (objective et contraintes)
- 🎲 Remplissage aléatoire pour tester rapidement
- 📈 Résolution par la méthode du Simplexe
- 🔍 Visualisation détaillée de chaque itération
- ⚠️ Détection des cas particuliers (problème non borné, non admissible)
- 📱 Interface responsive (Bootstrap)
- 🌓 Support du mode clair/sombre

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Étapes

1. **Cloner ou télécharger le projet**
   ```bash
   cd OptiLineaire
   ```

2. **Créer un environnement virtuel** (optionnel mais recommandé)
   ```bash
   python -m venv myenv
   # Activation
   # Windows:
   myenv\Scripts\activate
   # Linux/Mac:
   source myenv/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

5. **Lancer le serveur**
   ```bash
   python manage.py runserver
   ```

6. **Accéder à l'application**
   ```
   http://127.0.0.1:8000/
   ```

## 📖 Utilisation

### Étape 1 : Saisir le problème
- Choisir le nombre de variables et de contraintes
- Sélectionner si vous voulez maximiser ou minimiser
- Entrer les coefficients de la fonction objectif
- Entrer les coefficients des contraintes

### Étape 2 : Résoudre
Cliquer sur "Résoudre" pour lancer le simplexe.

### Étape 3 : Consulter les résultats
- **Tableau initial** : État de départ du problème
- **Itérations** : Chaque étape du simplexe avec :
  - Identification du pivot
  - Tableau après pivotage
  - Détails des opérations élémentaires
- **Solution optimale** : Valeur de Z et valeurs des variables

## 📁 Structure du projet

```
OptiLineaire/
├── manage.py                 # Gestion Django
├── requirements.txt          # Dépendances
├── db.sqlite3               # Base de données
│
├── OptiLineaire/            # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── pb_lineaire/             # Application principale
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── simplex.py           # Implémentation du simplexe
│   ├── apps.py
│   │
│   ├── static/
│   │   └── pb_lineaire/
│   │       └── global.css
│   │
│   ├── templates/
│   │   └── pb_lineaire/
│   │       ├── base.html         # Template de base
│   │       ├── index.html        # Formulaire de saisie
│   │       ├── result.html       # Résultats
│   │       └── _iterations.html  # Détail des itérations
│   │
│   ├── templatetags/
│   │   └── math_notation.py     # Filtres pour notation mathématique
│   │
│   └── migrations/
│
└── myenv/                   # Environnement virtuel (si créé)
```

## 🔧 Dépendances principales

- **Django 6.0.4** : Framework web
- **asgiref** : Support ASGI
- **sqlparse** : Parsing SQL
- **tzdata** : Données de fuseaux horaires

Voir `requirements.txt` pour la liste complète.

## 🧮 Algorithme du Simplexe

L'implémentation suit la méthode du Simplexe standard :

1. Déterminer la variable entrante (coefficient LF le plus positif)
2. Déterminer la variable sortante (ratio minimum)
3. Effectuer le pivotage
4. Répéter jusqu'à l'optimalité ou détection d'unboundedness

### Fichier clé
- **`pb_lineaire/simplex.py`** : Implémentation complète de l'algorithme

## 📝 Exemple d'utilisation

**Problème :**
```
max Z = 3·x₁ + 2·x₂
s.c.
  2·x₁ + x₂ ≤ 100
  x₁ + x₂ ≤ 80
  x₁, x₂ ≥ 0
```

**Procédure :**
1. Aller à http://127.0.0.1:8000/
2. Choisir 2 variables, 2 contraintes
3. Sélectionner "Maximisation"
4. Entrer les coefficients
5. Cliquer "Résoudre"

## 🎨 Personnalisation

### Thème
Le CSS est géré dans `pb_lineaire/static/pb_lineaire/global.css` avec variables CSS pour le mode clair/sombre.

### Filtres mathématiques
Les filtres Django personnalisés se trouvent dans `pb_lineaire/templatetags/math_notation.py`.

## 🐛 Dépannage

### Port déjà utilisé
```bash
python manage.py runserver 8001
```

### Erreur de migration
```bash
python manage.py migrate --fake-initial
```

### Réinitialiser la base
```bash
rm db.sqlite3
python manage.py migrate
```

## 📄 Licence

Ce projet est fourni à titre éducatif dans le cadre d'une SAE (Situation d'Apprentissage et d'Évaluation).

## 👤 Auteur

Développé pour l'apprentissage de la programmation linéaire et du développement web avec Django.

---

**Dernière mise à jour:** Avril 2026
