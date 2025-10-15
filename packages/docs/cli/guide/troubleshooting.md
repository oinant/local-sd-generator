# Troubleshooting

**Solutions aux problèmes courants et FAQ.**

📚 **Pour toutes questions sur l'utilisation du CLI.**

⏱️ **Durée de lecture** : 10 minutes

---

## Problèmes de génération

### ❌ Une seule image générée au lieu de plusieurs

**Symptôme** : Vous attendiez 50 images mais une seule est générée.

**Cause probable** : Placeholder utilisé sans variations définies.

**Solution** :

1. **Vérifier les statistiques affichées** avant génération :
   ```
   ╭─────────────────── Detected Variations ──────────────────╮
   │   Expression: 5 variations                                │
   │   Outfit: 0 variations  ← PROBLÈME ICI                    │
   │   Total combinations: 0                                   │
   ╰───────────────────────────────────────────────────────────╯
   ```

2. **Ajouter l'import manquant** :
   ```yaml
   imports:
     Expression: ../variations/expressions.yaml
     Outfit: ../variations/outfits.yaml  # ← Ajouter ceci
   ```

3. **Régénérer** :
   ```bash
   sdgen generate -t votre_template.prompt.yaml
   ```

---

### ❌ Trop d'images générées (explosion combinatoire)

**Symptôme** : Le CLI annonce 30,000 combinaisons alors que vous vouliez ~100 images.

**Cause** : Trop de variations sans sélecteurs.

**Exemple problématique** :
```yaml
imports:
  Expression: ../variations/expressions.yaml  # 50 variations
  Outfit: ../variations/outfits.yaml         # 30 variations
  Angle: ../variations/angles.yaml            # 20 variations

# 50 × 30 × 20 = 30,000 images !
```

**Solutions** :

**Option 1 : Utiliser des sélecteurs**
```yaml
template: |
  portrait, {Expression[5]}, {Outfit[3]}, {Angle[4]}

# 5 × 3 × 4 = 60 images
```

**Option 2 : Mode random**
```yaml
generation:
  mode: random
  max_images: 100  # Tire 100 combinaisons aléatoires
```

**Option 3 : Limiter max_images**
```yaml
generation:
  mode: combinatorial
  max_images: 100  # S'arrête après 100 images
```

---

### ❌ Pas assez de variété dans les résultats

**Symptôme** : Toutes les images se ressemblent trop.

**Cause** : Seed mode `fixed` (même seed pour toutes les images).

**Solution** : Changer le seed mode

```yaml
generation:
  # ❌ Mauvais (toutes les images identiques en style)
  seed_mode: fixed
  seed: 1000

  # ✅ Bon (seeds différentes)
  seed_mode: progressive  # Recommandé
  seed: 1000

  # ✅ Bon aussi (maximum de variété)
  seed_mode: random
```

---

### ❌ Génération très lente

**Symptôme** : La génération prend plusieurs heures.

**Causes possibles** :

1. **Trop d'images** : Réduire `max_images`
2. **Hires fix activé** : Double le temps de génération
3. **Résolution trop haute** : Réduire width/height
4. **Steps trop élevés** : Réduire steps

**Solutions** :

```yaml
# Version test (rapide)
generation:
  max_images: 10  # Test avec peu d'images

parameters:
  width: 512      # Résolution standard
  height: 768
  steps: 15       # Steps réduits
  enable_hr: false  # Désactiver hires fix

# Version production (après validation)
generation:
  max_images: 500

parameters:
  steps: 25
  enable_hr: true
```

---

## Erreurs de validation

### ❌ Unresolved placeholders

**Erreur** :
```
ValueError: Unresolved placeholders in template: Outfit
These placeholders are used in the prompt/template but have no
corresponding variations defined in 'imports:' section.
Available variations: Expression, Background
```

**Cause** : Placeholder `{Outfit}` utilisé mais pas d'import correspondant.

**Solution** :
```yaml
imports:
  Expression: ../variations/expressions.yaml
  Background: ../variations/backgrounds.yaml
  Outfit: ../variations/outfits.yaml  # ← Ajouter ceci
```

---

### ❌ File not found

**Erreur** :
```
FileNotFoundError: ../variations/expressions.yaml
```

**Causes possibles** :

1. **Chemin incorrect** : Vérifier le chemin relatif
2. **Fichier n'existe pas** : Créer le fichier manquant

**Solution 1 : Vérifier le chemin relatif**

```yaml
# Si votre structure est :
# project/
#   ├── prompts/
#   │   └── portrait.prompt.yaml
#   └── variations/
#       └── expressions.yaml

# Dans prompts/portrait.prompt.yaml :
imports:
  Expression: ../variations/expressions.yaml  # ✅ Correct (remonte d'un niveau)

# ❌ Incorrect :
imports:
  Expression: variations/expressions.yaml  # Ne remonte pas
```

**Solution 2 : Créer le fichier manquant**

```bash
# Créer le dossier
mkdir -p variations

# Créer le fichier
cat > variations/expressions.yaml << 'EOF'
happy: smiling, cheerful expression
sad: crying, melancholic look
neutral: calm, neutral expression
EOF
```

---

### ❌ Invalid field 'variations'

**Erreur** :
```
ValueError: Invalid field in my_prompt.prompt.yaml:
V2.0 Template System uses 'imports:' field, not 'variations:'.
Please rename 'variations:' to 'imports:' in your YAML file.
```

**Cause** : Utilisation de l'ancienne syntaxe V1.

**Solution** : Remplacer `variations:` par `imports:`

```yaml
# ❌ Ancien (V1)
variations:
  Expression: ../variations/expressions.yaml

# ✅ Nouveau (V2.0)
imports:
  Expression: ../variations/expressions.yaml
```

---

### ❌ YAML syntax error

**Erreur** :
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Cause** : Erreur de syntaxe YAML (indentation, format).

**Exemples d'erreurs courantes** :

**Problème 1 : Indentation incorrecte**
```yaml
# ❌ Incorrect
imports:
Expression: ../variations/expressions.yaml  # Manque 2 espaces

# ✅ Correct
imports:
  Expression: ../variations/expressions.yaml
```

**Problème 2 : Template sans pipe `|`**
```yaml
# ❌ Incorrect
template:
  masterpiece, portrait, detailed

# ✅ Correct
template: |
  masterpiece, portrait, detailed
```

**Problème 3 : Mélange tabs/espaces**
```yaml
# ❌ Incorrect (mélange tabs et espaces)
imports:
→ Expression: file.yaml  # Tab
  Outfit: file2.yaml     # 2 espaces

# ✅ Correct (toujours 2 espaces)
imports:
  Expression: file.yaml
  Outfit: file2.yaml
```

---

## Problèmes de configuration

### ❌ Config file not found

**Erreur** :
```
FileNotFoundError: ~/.sdgen_config.json not found
```

**Solution** : Initialiser la configuration

```bash
sdgen init
```

Puis éditer `~/.sdgen_config.json` :
```json
{
  "configs_dir": "/path/to/your/templates",
  "output_dir": "/path/to/output",
  "api_url": "http://127.0.0.1:7860"
}
```

---

### ❌ Connection refused (API)

**Erreur** :
```
requests.exceptions.ConnectionError: Connection refused
```

**Cause** : Stable Diffusion WebUI n'est pas lancé.

**Solution** :

1. **Lancer SD WebUI**
   ```bash
   cd /path/to/stable-diffusion-webui
   ./webui.sh  # ou webui.bat sur Windows
   ```

2. **Vérifier l'URL** dans `~/.sdgen_config.json`
   ```json
   {
     "api_url": "http://127.0.0.1:7860"
   }
   ```

3. **Tester l'API**
   ```bash
   sdgen api samplers
   ```

---

## Problèmes de templates

### ❌ Template trop répétitif

**Symptôme** : Vous avez 10 fichiers prompts quasi-identiques.

**Mauvaise approche** :
```
prompts/
├── portrait_happy.prompt.yaml       # Duplication
├── portrait_sad.prompt.yaml         # Duplication
├── portrait_action.prompt.yaml      # Duplication
...
```

**Solution : Utiliser l'héritage**

**Créer un template de base** :
```yaml
# templates/base_portrait.template.yaml
version: '2.0'
name: 'Base Portrait'

parameters:
  width: 512
  height: 768
  steps: 20
  cfg_scale: 7
  sampler: DPM++ 2M Karras

template: |
  masterpiece, portrait, {prompt}, detailed
```

**Utiliser implements** :
```yaml
# prompts/portrait_happy.prompt.yaml
version: '2.0'
name: 'Portrait Happy'
implements: ../templates/base_portrait.template.yaml

template: |
  smiling, happy, cheerful

generation:
  mode: random
  seed: 1000
  seed_mode: progressive
  max_images: 50
```

---

### ❌ Sélecteur ne fonctionne pas

**Symptôme** : `{Expression[5]}` génère toujours toutes les variations.

**Cause** : Erreur de syntaxe du sélecteur.

**Syntaxes valides** :
```yaml
{Expression[5]}              # ✅ 5 variations aléatoires
{Expression[#0,2,4]}         # ✅ Indices 0, 2, 4
{Expression[happy,sad]}      # ✅ Clés nommées
{Expression[#0-10]}          # ✅ Range d'indices
```

**Syntaxes invalides** :
```yaml
{Expression[random:5]}       # ❌ Ancienne syntaxe
{Expression(5)}              # ❌ Mauvais délimiteurs
{Expression:5}               # ❌ Mauvais séparateur
```

---

## FAQ

### Q : Puis-je utiliser plusieurs fichiers pour un même placeholder ?

**Oui !** Utilisez une liste d'imports :

```yaml
imports:
  HairColor:
    - ../variations/haircolors.realistic.yaml
    - ../variations/haircolors.fantasy.yaml
    - ../variations/haircolors.gradient.yaml
```

Les fichiers sont automatiquement mergés.

---

### Q : Comment régénérer exactement la même image ?

**Utilisez la seed du manifest.json** :

1. Ouvrir `results/session_name/manifest.json`
2. Trouver l'image désirée et noter sa seed
3. Créer un nouveau prompt avec cette seed en mode `fixed`

```yaml
generation:
  seed_mode: fixed
  seed: 42  # Seed de l'image originale
  max_images: 1
```

---

### Q : Combien d'images puis-je générer en une session ?

**Limite théorique** : Aucune (dépend de votre espace disque).

**Recommandations** :
- Tests : 5-20 images
- Production normale : 50-500 images
- Datasets LoRA : 500-2000 images

**Note** : Sessions très longues (>1000 images) peuvent prendre plusieurs heures.

---

### Q : Puis-je annuler une génération en cours ?

**Oui**, avec `Ctrl+C` dans le terminal.

**Les images déjà générées** sont sauvegardées dans `results/`.

---

### Q : Comment voir tous les samplers disponibles ?

```bash
sdgen api samplers
```

**Autres commandes utiles** :
```bash
sdgen api models      # Modèles disponibles
sdgen api schedulers  # Schedulers disponibles
sdgen api upscalers   # Upscalers disponibles
```

---

### Q : Les placeholders sont-ils case-sensitive ?

**Oui !** `{Expression}` ≠ `{expression}`

**Recommandation** : Utiliser PascalCase pour les placeholders
```yaml
{Expression}   # ✅ Bon
{HairColor}    # ✅ Bon
{expression}   # ⚠️ Fonctionne mais moins lisible
```

---

### Q : Puis-je utiliser des espaces dans les placeholders ?

**Non**, les espaces ne sont pas supportés.

```yaml
{Hair Color}   # ❌ Invalide
{HairColor}    # ✅ Valide
```

---

### Q : Comment débugger un template complexe ?

**Méthode 1 : Dry-run**
```bash
sdgen generate -t template.yaml --dry-run
```

Sauvegarde les payloads API en JSON sans générer.

**Méthode 2 : Limite à 1 image**
```yaml
generation:
  max_images: 1
```

Génère une seule image pour tester rapidement.

**Méthode 3 : Validation**
```bash
sdgen validate template.yaml
```

Vérifie la structure sans générer.

---

## Récapitulatif

✅ Vous savez maintenant comment :
- Diagnostiquer les problèmes de génération
- Corriger les erreurs de validation
- Résoudre les problèmes de configuration
- Optimiser les templates répétitifs
- Utiliser les commandes de debug

### Ressources supplémentaires

- [Getting Started](./getting-started.md) - Guide d'installation
- [Templates Basics](./3-templates-basics.md) - Concepts fondamentaux
- [Templates Advanced](./4-templates-advanced.md) - Features avancées
- [Examples](./examples.md) - Cas d'usage réels

---

**Dernière mise à jour** : 2025-10-14
**Durée de lecture** : ~10 minutes
**Version du système** : V2.0
