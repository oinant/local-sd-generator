# Feature: Explain & Debug System

**Status:** future
**Priority:** 7
**Depends on:** All other templating features

## Description

Système d'explication et de debugging permettant de comprendre comment un prompt est construit, quelles variations sont utilisées, et pourquoi certains résultats sont obtenus. Inclut un LLM-friendly output pour poser des questions en langage naturel.

## Motivation

### Problème
Avec un système de templating complexe :
- Difficile de comprendre pourquoi un prompt final ressemble à ça
- Impossible de tracer d'où vient une valeur spécifique
- Debugging frustrant quand le résultat n'est pas attendu
- Pas de documentation auto-générée des configurations

### Avec explain system
```bash
sdgen explain portrait.prompt.yaml \
  "Pourquoi Emma a la peau rouge dans certaines images ?"
```

**Output :** Documentation complète + analyse LLM de la question + contexte pour résoudre le problème.

## Commande principale

### Syntaxe
```bash
sdgen explain <prompt_file> [question] [options]
```

**Arguments :**
- `prompt_file` : Fichier .prompt.yaml à expliquer
- `question` : (Optionnel) Question en langage naturel
- `options` :
  - `--output FILE` : Sauvegarder dans un fichier (défaut: stdout)
  - `--format yaml|json|markdown` : Format de sortie (défaut: yaml)
  - `--include-images` : Inclure les images générées si disponibles
  - `--variation-index N` : Expliquer la variation spécifique N

### Exemples d'usage

**Explication complète :**
```bash
sdgen explain portrait.prompt.yaml > debug.yaml
```

**Question spécifique :**
```bash
sdgen explain portrait.prompt.yaml \
  "Pourquoi la combinaison african + pale skin est possible ?"
```

**Variation spécifique :**
```bash
sdgen explain portrait.prompt.yaml \
  --variation-index 42 \
  "Pourquoi cette image a ces caractéristiques ?"
```

## Format de sortie

### Structure YAML complète
```yaml
# =====================================
# SDGEN EXPLAIN OUTPUT
# Generated: 2025-10-02 14:23:45
# =====================================

# Section 1: Métadonnées
metadata:
  prompt_file: prompts/portrait.prompt.yaml
  generated_at: "2025-10-02T14:23:45Z"
  sdgen_version: "2.0.0"
  question: "Pourquoi Emma a la peau rouge dans certaines images ?"

# Section 2: Configuration du prompt
prompt_config:
  name: "Emma Multi-ethnic Portrait"
  generation_mode: combinatorial
  seed_mode: progressive
  seed: 42
  total_variations: 15

# Section 3: Template du prompt
prompt_template: |
  {TECHNIQUE}
  BREAK
  {CHARACTER with ethnicity=ETHNICITIES[african,asian,latina]}
  BREAK
  {POSES[range:1-10,random:5]}, {EXPRESSIONS[happy,surprised]},
  {ENVIRONMENTS[outdoor]}
  BREAK
  cowboy shot, face focus

# Section 4: Imports utilisés
imports:
  TECHNIQUE:
    source: base/photorealistic_tech.txt
    type: fixed
    content: |
      Photorealistic, ultra realistic,
      (realistic eyes, detailed eyes, perfect eyes),
      ...

  CHARACTER:
    source: characters/athlete_portrait.char.yaml
    type: character
    implements: templates/portrait_subject.char.template.yaml
    base_values:
      eyes: "focused eyes, determined gaze"
      hair_style: "short athletic cut"
      height: "tall"
      body_type: "athletic, muscular"
      # ... autres champs
    overrides:
      - field: ethnicity
        source: ETHNICITIES[african,asian,latina]
        expanded_values:
          african:
            ethnicity: "(African:1.3)"
            skin_tone: "(black skin:1.3)"
            typical_features: "full lips, wide nose"
          asian:
            ethnicity: "(Asian:1.2)"
            skin_tone: "(pale skin)"
            typical_features: "almond eyes"
          latina:
            ethnicity: "(cuban venezuelan latina)"
            skin_tone: "(dark brown skin:1.3)"
            typical_features: "warm skin"

  ETHNICITIES:
    source: variations/ethnicities.yaml
    type: multi_field_variation
    selected_keys: [african, asian, latina]
    total_available: 10
    fields_affected: [ethnicity, skin_tone, typical_features]

  POSES:
    source: variations/poses.yaml
    type: variation
    selector: "[range:1-10,random:5]"
    selected_count: 15
    selected_variations:
      - standing
      - sitting
      - lying down
      # ... 12 more

  EXPRESSIONS:
    source: variations/expressions.yaml
    type: variation
    selector: "[happy,surprised]"
    selected_count: 2
    selected_variations:
      - key: happy
        value: "smiling, cheerful"
      - key: surprised
        value: "eyes wide, mouth open"

  ENVIRONMENTS:
    source: variations/environments.yaml
    type: variation
    selector: "[outdoor]"
    selected_count: 1
    selected_variations:
      - key: outdoor
        value: "outdoor setting, natural background"

# Section 5: Arbre de résolution
resolution_tree:
  TECHNIQUE:
    type: direct
    result: "Photorealistic, ultra realistic, ..."

  CHARACTER:
    type: character_with_override
    steps:
      1_load_base:
        source: characters/athlete_portrait.char.yaml
        template: templates/portrait_subject.char.template.yaml
        fields_loaded: 15

      2_apply_overrides:
        field: ethnicity
        source: ETHNICITIES[african,asian,latina]
        expansion_type: multi_field
        fields_affected:
          - ethnicity
          - skin_tone
          - typical_features
        variations_created: 3

      3_render:
        template_format: "{ethnicity}, {skin_tone}, ... 1girl, {age}, ..."
        rendered_variations:
          - variation_1:
              ethnicity: "(African:1.3)"
              skin_tone: "(black skin:1.3)"
              typical_features: "full lips, wide nose"
              eyes: "(blue eyes:0.3)"  # From base
              # ...
              final_prompt: "(African:1.3), (black skin:1.3), (blue eyes:0.3), ..."

          - variation_2:
              ethnicity: "(Asian:1.2)"
              skin_tone: "(pale skin)"
              # ...

          - variation_3:
              ethnicity: "(cuban venezuelan latina)"
              skin_tone: "(dark brown skin:1.3)"
              # ...

# Section 6: Toutes les variations générées
all_variations:
  - index: 0
    seed: 42
    character_variant: african
    pose: standing
    expression: happy
    environment: outdoor
    final_prompt: |
      Photorealistic, ultra realistic, ...
      BREAK
      (African:1.3), (black skin:1.3), (blue eyes:0.3), ...
      BREAK
      standing, smiling, cheerful, outdoor setting
      BREAK
      cowboy shot, face focus

  - index: 1
    seed: 43
    character_variant: african
    pose: standing
    expression: surprised
    # ...

  # ... 13 more variations

# Section 7: Fichiers sources complets
source_files:
  "characters/athlete_portrait.char.yaml":
    content: |
      version: "1.0"
      type: character
      name: "Professional Athlete"
      implements: templates/portrait_subject.char.template.yaml
      values:
        eyes: "focused eyes, determined gaze"
        # ... full content

  "variations/ethnicities.yaml":
    content: |
      version: "1.0"
      variations:
        - key: african
          ethnicity: "(African:1.3)"
          # ... full content

  # ... tous les autres fichiers

# Section 8: API Request (si généré)
api_request:
  endpoint: "http://127.0.0.1:7860/sdapi/v1/txt2img"
  method: POST
  payload_template:
    prompt: "{final_prompt}"
    negative_prompt: "low quality, blurry, deformed"
    width: 768
    height: 1024
    steps: 30
    cfg_scale: 7.5
    seed: "{seed}"
    sampler_name: "DPM++ 2M Karras"

# Section 9: LLM Context & Answer
llm_context:
  question: "Pourquoi Emma a la peau rouge dans certaines images ?"

  system_specification: |
    # SD Prompt Generator - System Specification

    ## Character Override System
    When using `{CHARACTER with field=SOURCE[selector]}`, the system:
    1. Loads the base character from the .char.yaml file
    2. Loads the variation source
    3. For multi-field variations, expands ALL fields defined
    4. Inline overrides take priority over expanded fields

    ## Priority Order
    1. Inline override in `with` clause (highest)
    2. Multi-field expansion from variation file
    3. Base character values
    4. Template defaults (lowest)

    ## Multi-field Expansion
    When a variation file defines multiple fields (e.g., ethnicity, skin_tone):
    - ALL fields are expanded together
    - To override specific fields, use inline syntax

    Example:
    ```yaml
    {CHARACTER with
      ethnicity=ETHNICITIES[african],
      skin_tone="(red skin:1.2)"  # Inline override
    }
    ```

    This will:
    - Use ethnicity from ETHNICITIES[african]
    - Override skin_tone with inline value
    - Use other fields (eyes, hair) from base character

  analysis: |
    Based on your question and the configuration analysis:

    **Why Emma might have red skin:**

    The configuration uses:
    ```yaml
    {CHARACTER with ethnicity=ETHNICITIES[african,asian,latina]}
    ```

    This expands the `ethnicity` field with variations from `ethnicities.yaml`.
    Each variation is a **multi-field expansion** that sets:
    - ethnicity
    - skin_tone
    - typical_features

    **However**, if you later override skin_tone inline or if there's a
    bug in the variation file, the skin_tone could become inconsistent.

    **Most likely cause:**
    Check your `ethnicities.yaml` file. If one of the variations has
    `skin_tone: "(red skin:1.2)"`, that would explain it.

    **To fix:**
    1. Review `variations/ethnicities.yaml` for incorrect skin_tone values
    2. OR, if you want to force a specific skin_tone:
       ```yaml
       {CHARACTER with
         ethnicity=ETHNICITIES[african],
         skin_tone="(black skin:1.3)"  # Force this
       }
       ```

    **Related variations:**
    - Index 0-4: african variations
    - Index 5-9: asian variations
    - Index 10-14: latina variations

    Check specific images to identify which variation has the issue.

  suggested_actions:
    - action: review_file
      file: variations/ethnicities.yaml
      reason: Check skin_tone values for each ethnicity

    - action: test_override
      command: |
        sdgen generate portrait.prompt.yaml \
          --override "CHARACTER.skin_tone=(black skin:1.3)" \
          --variation-index 2
      reason: Test if inline override fixes the issue

    - action: validate
      command: sdgen validate variations/ethnicities.yaml
      reason: Check for inconsistencies in variation file
```

## Use Cases

### UC1 : Debugging incohérences
**Problème :** "Emma asiatique a les yeux bleus et la peau noire"

**Commande :**
```bash
sdgen explain portrait.prompt.yaml \
  "Pourquoi Emma asiatique a les yeux bleus et la peau noire ?"
```

**Output :**
- Montre que `eyes: "(blue eyes:0.3)"` vient du base character
- Montre que `skin_tone: "(black skin:1.3)"` vient d'une mauvaise config
- Suggère de vérifier `ethnicities.yaml` ou d'override `eyes`

### UC2 : Comprendre la génération
**Question :** "Combien d'images seront générées ?"

**Commande :**
```bash
sdgen explain portrait.prompt.yaml "Combien d'images ?"
```

**Output :**
```yaml
llm_context:
  analysis: |
    Total variations: 45

    Calculation:
    - ETHNICITIES: 3 variations (african, asian, latina)
    - POSES: 15 variations (range:1-10 + random:5)
    - EXPRESSIONS: 2 variations (happy, surprised)
    - ENVIRONMENTS: 1 variation (outdoor)

    Total = 3 × 15 × 2 × 1 = 90 combinations

    BUT, generation.mode = "combinatorial" and no max_images set,
    so all 90 will be generated.

    With seed_mode = "progressive" and seed = 42:
    - Image 0: seed 42
    - Image 1: seed 43
    - ...
    - Image 89: seed 131
```

### UC3 : Tracer une valeur
**Question :** "D'où vient la valeur 'bob hair' dans le prompt ?"

**Commande :**
```bash
sdgen explain portrait.prompt.yaml \
  "D'où vient 'bob hair' ?"
```

**Output :**
```yaml
llm_context:
  analysis: |
    The value "bob hair" comes from:

    Source chain:
    1. Prompt uses: {CHARACTER}
    2. CHARACTER loads: characters/athlete_portrait.char.yaml
    3. athlete_portrait.char.yaml defines:
       values:
         hair_style: "short athletic cut"
    4. This value is used in the template at position:
       portrait_subject.char.template.yaml line 8: {hair_style}

    Full resolution:
    - File: characters/athlete_portrait.char.yaml
    - Field: hair_style
    - Value: "short athletic cut"
    - Rendered in: all variations (not overridden)
```

### UC4 : Partage de configuration
**Besoin :** Partager la config avec quelqu'un pour reproduction

**Commande :**
```bash
sdgen explain portrait.prompt.yaml --format yaml > shared_config.yaml
```

**Résultat :** Fichier auto-suffisant avec :
- Toute la configuration
- Tous les fichiers sources
- Instructions de reproduction

### UC5 : Documentation auto
**Besoin :** Générer de la doc pour une bibliothèque de variations

**Commande :**
```bash
sdgen explain --docs variations/ethnicities.yaml > ethnicities_docs.md
```

## Implémentation

### Architecture
```python
class ExplainSystem:
    def __init__(self, prompt_file: str):
        self.prompt_file = prompt_file
        self.config = load_prompt_config(prompt_file)
        self.resolution_tree = {}
        self.source_files = {}

    def explain(self, question: Optional[str] = None) -> dict:
        """Génère l'explication complète"""

        # 1. Parse et charge tout
        self.load_all_sources()

        # 2. Résout et trace
        self.build_resolution_tree()

        # 3. Génère toutes les variations
        self.generate_all_variations()

        # 4. Collecte les sources
        self.collect_source_files()

        # 5. Si question, interroge LLM
        llm_response = None
        if question:
            llm_response = self.ask_llm(question)

        # 6. Assemble l'output
        return self.build_output(llm_response)

    def build_resolution_tree(self):
        """Construit l'arbre de résolution"""
        for import_name, import_config in self.config.imports.items():
            self.resolution_tree[import_name] = self.trace_resolution(
                import_name,
                import_config
            )

    def trace_resolution(self, name, config, depth=0):
        """Trace récursivement la résolution"""
        trace = {
            "name": name,
            "type": config.type,
            "source": config.source,
            "depth": depth
        }

        if config.type == "character_with_override":
            trace["steps"] = {
                "1_load_base": self.trace_character_load(config),
                "2_apply_overrides": self.trace_overrides(config),
                "3_render": self.trace_render(config)
            }

        elif config.type == "nested_variation":
            trace["nested_resolutions"] = [
                self.trace_resolution(ref, ref_config, depth + 1)
                for ref, ref_config in config.references.items()
            ]

        return trace

    def ask_llm(self, question: str) -> dict:
        """Interroge un LLM avec le contexte complet"""

        context = self.build_llm_context()

        prompt = f"""
        You are analyzing a Stable Diffusion prompt generation configuration.

        # User Question
        {question}

        # System Specification
        {context['specification']}

        # Configuration
        {yaml.dump(context['config'])}

        # Resolution Tree
        {yaml.dump(context['resolution_tree'])}

        # Source Files
        {yaml.dump(context['source_files'])}

        Analyze the configuration and answer the user's question.
        Provide:
        1. Direct answer
        2. Explanation of relevant parts
        3. Suggested fixes if applicable
        4. Related variations to check
        """

        response = call_llm_api(prompt)
        return {
            "question": question,
            "analysis": response,
            "suggested_actions": parse_actions(response)
        }
```

### LLM Integration
```python
def call_llm_api(prompt: str) -> str:
    """Appel à un LLM (Claude, GPT, local, etc.)"""

    # Option 1: API Claude
    response = anthropic_client.messages.create(
        model="claude-3-sonnet",
        messages=[{"role": "user", "content": prompt}]
    )

    # Option 2: API OpenAI
    # response = openai.ChatCompletion.create(...)

    # Option 3: Local LLM
    # response = ollama.generate(...)

    return response.content
```

## Output Formats

### YAML (défaut)
Complet, structuré, facile à parser

### JSON
Pour intégration programmatique

### Markdown
Pour documentation humaine
```bash
sdgen explain portrait.prompt.yaml --format markdown > docs.md
```

**Output :**
```markdown
# Prompt Explanation: Emma Multi-ethnic Portrait

## Configuration
- **Generation mode:** combinatorial
- **Total variations:** 45
- **Seed:** 42 (progressive)

## Imports

### TECHNIQUE
**Source:** base/photorealistic_tech.txt
**Type:** Fixed

Content:
\`\`\`
Photorealistic, ultra realistic, ...
\`\`\`

### CHARACTER
**Source:** characters/athlete_portrait.char.yaml
**Type:** Character with overrides

Base values:
- eyes: focused eyes, determined gaze
- hair: short athletic cut
- body_type: athletic, muscular
...

Overrides:
- ethnicity → ETHNICITIES[african,asian,latina]
  - Affects: ethnicity, skin_tone, typical_features
  - Creates 3 variations

...
```

## Tests

### Test 1 : Explication basique
```python
def test_basic_explain():
    explainer = ExplainSystem("portrait.prompt.yaml")
    output = explainer.explain()

    assert "metadata" in output
    assert "imports" in output
    assert "resolution_tree" in output
```

### Test 2 : Question LLM
```python
def test_llm_question():
    explainer = ExplainSystem("portrait.prompt.yaml")
    output = explainer.explain("Why red skin?")

    assert "llm_context" in output
    assert output["llm_context"]["question"] == "Why red skin?"
    assert "analysis" in output["llm_context"]
```

### Test 3 : Trace de résolution
```python
def test_resolution_trace():
    explainer = ExplainSystem("portrait.prompt.yaml")
    tree = explainer.build_resolution_tree()

    assert "CHARACTER" in tree
    assert tree["CHARACTER"]["type"] == "character_with_override"
    assert "steps" in tree["CHARACTER"]
```

### Test 4 : Formats de sortie
```python
def test_output_formats():
    explainer = ExplainSystem("portrait.prompt.yaml")
    output = explainer.explain()

    yaml_str = explainer.format_as_yaml(output)
    json_str = explainer.format_as_json(output)
    md_str = explainer.format_as_markdown(output)

    assert yaml.safe_load(yaml_str) == output
    assert json.loads(json_str) == output
    assert "# Prompt Explanation" in md_str
```

## Performance

### Optimisations
- **Lazy LLM call** : Seulement si question fournie
- **Cache** : Réutilise les fichiers déjà chargés
- **Parallel** : Charge les sources en parallèle

### Benchmarks
- Explain sans LLM : < 100ms
- Explain avec LLM : < 5s (dépend de l'API)

## Documentation auto-générée

La commande `explain` génère aussi de la documentation :

```bash
# Doc d'un prompt
sdgen explain portrait.prompt.yaml --format markdown > docs/portrait.md

# Doc d'une variation
sdgen explain variations/ethnicities.yaml --format markdown > docs/ethnicities.md

# Doc d'un character
sdgen explain characters/athlete_portrait.char.yaml --format markdown > docs/athlete.md
```

## Success Criteria

- [ ] Commande `sdgen explain` fonctionnelle
- [ ] Génère output YAML complet
- [ ] Trace la résolution complète
- [ ] Collecte tous les fichiers sources
- [ ] Intégration LLM pour questions
- [ ] Support YAML, JSON, Markdown
- [ ] Documentation auto-générée
- [ ] Performance acceptable (< 5s total)
- [ ] Tests complets (>85% coverage)
- [ ] Documentation utilisateur complète
