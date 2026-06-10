# Méthode du Simplexe

## Vue d'ensemble
La méthode du Simplexe résout des problèmes de programmation linéaire en forme standard :

max Z = c^T x  s.t.  A x ≤ b,  x ≥ 0

Elle est adaptée quand l'origine est admissible (tous les b_i ≥ 0) ou lorsqu'une solution de base initiale admissible est disponible.

## Principe
- Construire le tableau (tableau de Simplexe) avec variables d'écart (`y`) en base.
- À chaque itération :
  - Choisir la variable entrante : coefficient le plus négatif (ou le plus positif selon convention) de la ligne objectif (coûts réduits).
  - Choisir la variable sortante : test du ratio minimum `b_i / a_ij` pour `a_ij > 0`.
  - Effectuer un pivot (opérations élémentaires) pour mettre la variable entrante en base.
- Répéter jusqu'à optimalité (tous les coûts réduits indiquant optimalité) ou jusqu'à détection d'un cas particulier.

## Structure de données recommandée
- Représenter le tableau par une liste de listes (matrice) d'objets rationnels (`fractions.Fraction`) pour éviter les erreurs numériques.
- Maintenir une structure `basis` : dictionnaire {row_index: var_name}.
- Enregistrer par itération un snapshot contenant : tableau, base, variable entrante/sortante, pivot, opérations.

## Conditions d'arrêt et cas d'échec
- Optimalité : tous les coûts réduits satisfont la condition d'optimalité (selon la convention choisie).
- Non borné (unbounded) : si la colonne entrante a `a_ij ≤ 0` pour toutes les lignes → aucun ratio possible → problème non borné.
- Dégénérescence / cycling : lorsque le ratio minimum est 0 ou plusieurs ratios identiques → risque de boucle infinie. Mitigation : appliquer la règle de Bland (choisir la plus petite variable indexée) ou perturbation lexicographique.
- Base non admissible initiale : si certains `b_i < 0` → on ne peut pas démarrer le Simplexe primal directement (utiliser Two-Phase ou Dual Simplex).
- Problèmes numériques : arrondis flottants peuvent induire mauvais choix de pivot; préférer `fractions.Fraction` ou arithmétique rationnelle.

## Bonnes pratiques
- Utiliser arithmétique exacte (`fractions.Fraction`) pour l'affichage et la validation.
- Sauvegarder les itérations complètes pour traçabilité et pour l'interface pas-à-pas.
- Prévoir un critère d'arrêt par nombre d'itérations et un timeout pour éviter blocages en pratique.

## Sources
- `doc/DEUX_PHASES.md` (présentation complémentaire)
- `doc/OptiLin_Info_1 (1).pdf`, `doc/OptiLin_Info_1bis.pdf`, `doc/OptiLin_Info_2 (1).pdf`, `doc/OptiLin_Info_3 (2).pdf`, `doc/OptiLin_Info_3bis (1).pdf` (fichiers présents dans `doc/`)
