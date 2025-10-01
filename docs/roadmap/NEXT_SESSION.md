# Next Session: Placeholder Enhancements & New Features

**Date:** TBD
**Status:** Préparé

## Session Goals

Implémenter les améliorations du système de placeholders et corriger les bugs identifiés.

## Priority Order

### 1. Bugs (À corriger en premier)

**[BUG] Priority 1: Random mode no randomness** (`next/bug-random-mode-no-randomness.md`)
- Le mode random ne génère plus de vraies combinaisons aléatoires
- Cause: lazy generation prend les N premières séquentiellement
- Fix: Implémenter `generate_random_combinations_lazy()` avec sampling aléatoire

**[BUG] Priority 2: Output dir not used** (`next/bug-output-dir-not-used.md`)
- Le paramètre `output_dir` du `.sdgen_config.json` n'est pas utilisé
- Sortie toujours dans `apioutput/` au lieu du dossier configuré
- Fix: Lire config globale et passer output_dir au générateur

### 2. Features (Après les bugs)

**[FEATURE] Priority 3: Negative prompt placeholders** (`next/feature-negative-prompt-placeholders.md`)
- Permettre placeholders dans le negative prompt
- Use case: Varier entre neg prompts SDXL/Illustrious/Pony
- Exemple: `{NegStyle}` avec fichier de variations

**[FEATURE] Priority 4: Numeric slider placeholders** (`next/feature-numeric-slider-placeholders.md`)
- Nouveau type de placeholder pour valeurs numériques discrètes
- Syntaxe: `{Name:Unit:-1:3}`, `{Name:Decimal:-2.5:2.5}`, `{Name:Centimal:-1.26:3.57}`
- Use case: Tester valeurs de LoRA sliders

## Approach Suggérée

### Phase 1: Bug Fixes (1-2h)
1. Fix random mode avec lazy sampling
2. Fix output_dir configuration

### Phase 2: Negative Prompt Placeholders (1-2h)
1. Modifier extraction de placeholders pour inclure negative
2. Modifier application des variations pour negative
3. Tests

### Phase 3: Numeric Sliders (2-3h)
1. Parser syntax `Type:Min:Max`
2. Générer variations numériques
3. Intégrer avec système existant
4. Tests

## Testing Strategy

Pour chaque feature/fix:
- Tests unitaires dans `tests/`
- Test d'intégration avec config JSON complète
- Vérifier que les anciens tests passent toujours

## Documentation Updates

- Mettre à jour `docs/cli/technical/placeholder-system.md` avec nouvelles features
- Créer exemples d'usage dans `docs/cli/usage/`
- Déplacer specs de `next/` vers `wip/` pendant le travail
- Déplacer vers `done/` une fois terminé avec hash de commit

## Notes Importantes

### Random Mode Fix

L'ancien code (`private_generators/facial_expression_generator.py`) faisait:
```python
all_combinations = generate_all_combinations(variations_dict)
random.shuffle(all_combinations)
selected = all_combinations[:n]
```

Mais ne fonctionne pas avec 60T+ combinaisons. Solution:
- Option A: Random sampling avec indices uniques
- Option B: Génération directe de combinaisons aléatoires avec vérification unicité

### Numeric Sliders

Génération discrète de TOUTES les valeurs dans l'intervalle:
- `Unit:-1:3` → 5 valeurs [-1, 0, 1, 2, 3]
- `Decimal:-2.5:2.5` → 6 valeurs [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
- `Centimal:-1.26:3.57` → 49 valeurs (pas de 0.1)

Format dans prompt: `<lora:DetailSlider:{DetailLevel:Unit:-2:2}>`

### Negative Prompt

Même système que prompt principal:
- Support tous les sélecteurs (#|, :N, $X)
- Peut partager fichiers de variations avec prompt
- Exemple: `{Style}` dans prompt et negative → même valeur utilisée

## État du Projet

**Commits récents:**
- `33997e2`: perf: Lazy combinatorial generation

**Fonctionnalités actuelles:**
- ✓ Phase 1: Core Generator (SF-4, SF-5)
- ✓ Phase 2: Global Config & Validation (SF-7, SF-1)
- ✓ Phase 3: JSON Config Execution (SF-2, SF-3)
- ✓ Lazy generation pour grandes combinaisons
- ✓ Placeholders avec sélecteurs (#|, :N, $X)
- ✓ Modes: combinatorial/random, fixed/progressive/random seeds

**À faire:**
- ⚠ Fix random mode
- ⚠ Fix output_dir
- ⏳ Negative prompt placeholders
- ⏳ Numeric slider placeholders

## Quick Start Next Session

```bash
# 1. Lire les specs dans docs/roadmap/next/
# 2. Commencer par bug-random-mode-no-randomness.md (Priority 1)
# 3. Déplacer dans wip/ quand on commence
# 4. Commit quand terminé + déplacer dans done/
# 5. Puis bug-output-dir-not-used.md
# 6. Puis features dans l'ordre de priorité
```
