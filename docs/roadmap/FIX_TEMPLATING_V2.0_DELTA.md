# Migration V2.0 Original → V2.0 Corrigée - Delta d'implémentation

**Date:** 2025-10-10
**Status:** 🔧 Guide de migration

---

## Vue d'ensemble des changements

### Changements conceptuels majeurs

| Aspect | V2.0 Original | V2.0 Corrigée |
|--------|---------------|---------------|
| **Sémantique template** | REPLACE (enfant écrase parent) | **INJECTION** (Template Method Pattern) |
| **Champ prompt.yaml** | `template:` | **`prompt:`** |
| **Placeholder {prompt}** | Optionnel | **OBLIGATOIRE** dans templates |
| **Merge strategy** | Child remplace parent | Child **injecté dans** parent |
| **Chunks inheritance** | Multi-niveaux possible | **1 niveau max** (definition → impl) |

---

## 1. Changements dans les Data Models

### 1.1 `PromptConfig` - Renommage du champ

**Fichier:** `CLI/src/templating/models/config_models.py`

```diff
  @dataclass
  class PromptConfig:
      version: str
      name: str
      generation: GenerationConfig
-     template: str
+     prompt: str  # RENOMMÉ
      source_file: Path
      implements: Optional[str] = None
      imports: Dict[str, Any] = field(default_factory=dict)
      parameters: Dict[str, Any] = field(default_factory=dict)
      negative_prompt: Optional[str] = None
```

**Impact:** Tous les endroits qui accèdent à `config.template` pour un PromptConfig doivent maintenant accéder à `config.prompt`.

### 1.2 Pas de changement pour `TemplateConfig` et `ChunkConfig`

Les modèles `TemplateConfig` et `ChunkConfig` gardent leur champ `template:` (pas de renommage).

---

## 2. Changements dans le Parser

### 2.1 `parse_prompt()` - Nouveau champ + validation

**Fichier:** `CLI/src/templating/loaders/parser.py`

```diff
  def parse_prompt(self, data: Dict[str, Any], source_file: Path) -> PromptConfig:
      """
      Parse a .prompt.yaml file.
      """
+     # Validation: prompt.yaml files use 'prompt:' not 'template:'
+     if 'template' in data:
+         raise ValueError(
+             f"Invalid field in {source_file.name}: "
+             f"Prompt files must use 'prompt:' field, not 'template:'. "
+             f"Please rename 'template:' to 'prompt:' in your file."
+         )
+
+     # Validate prompt field type
+     prompt = data['prompt']
+     if not isinstance(prompt, str):
+         raise ValueError(
+             f"Invalid 'prompt' field in {source_file.name}: "
+             f"Expected string, got {type(prompt).__name__}.\n"
+             f"Hint: If you're using placeholders like {{Angle}}, you need to quote them:\n"
+             f"  ✗ Wrong:   prompt: {{Angle}}\n"
+             f"  ✓ Correct: prompt: \"{{Angle}}\"\n"
+             f"  ✓ Or use:  prompt: |\n"
+             f"               {{Angle}}"
+         )

      # Parse generation config
      gen_data = data['generation']
      generation = GenerationConfig(
          mode=gen_data['mode'],
          seed=gen_data['seed'],
          seed_mode=gen_data['seed_mode'],
          max_images=gen_data['max_images']
      )

      return PromptConfig(
          version=data.get('version', '1.0.0'),
          name=data['name'],
          generation=generation,
-         template=data['template'],
+         prompt=prompt,
          source_file=source_file,
          implements=data.get('implements'),
          imports=data.get('imports') or {},
          parameters=data.get('parameters') or {},
          negative_prompt=data.get('negative_prompt')
      )
```

### 2.2 `parse_template()` - Validation du {prompt} obligatoire

**Fichier:** `CLI/src/templating/loaders/parser.py`

```diff
  def parse_template(self, data: Dict[str, Any], source_file: Path) -> TemplateConfig:
      """
      Parse a .template.yaml file.
      """
      # Validate template field type
      template = data['template']
      if not isinstance(template, str):
          raise ValueError(
              f"Invalid 'template' field in {source_file.name}: "
              f"Expected string, got {type(template).__name__}.\n"
              f"Hint: If you're using placeholders like {{prompt}}, you need to quote them:\n"
              f"  ✗ Wrong:   template: {{prompt}}\n"
              f"  ✓ Correct: template: \"{{prompt}}\"\n"
              f"  ✓ Or use:  template: |\n"
              f"               {{prompt}}"
          )

+     # Validate {prompt} placeholder is present
+     if '{prompt}' not in template:
+         raise ValueError(
+             f"Invalid template in {source_file.name}: "
+             f"Template files must contain {{prompt}} placeholder. "
+             f"This is the injection point for child content (Template Method Pattern).\n"
+             f"Example:\n"
+             f"  template: |\n"
+             f"    masterpiece, {{prompt}}, detailed"
+         )

      return TemplateConfig(
          version=data.get('version', '1.0.0'),
          name=data['name'],
          template=template,
          source_file=source_file,
          implements=data.get('implements'),
          parameters=data.get('parameters') or {},
          imports=data.get('imports') or {},
          negative_prompt=data.get('negative_prompt') or ''
      )
```

### 2.3 `parse_chunk()` - Validation des placeholders interdits

**Fichier:** `CLI/src/templating/loaders/parser.py`

```diff
  def parse_chunk(self, data: Dict[str, Any], source_file: Path) -> ChunkConfig:
      """
      Parse a .chunk.yaml file.
      """
      # Validate template field type
      template = data['template']
      if not isinstance(template, str):
          raise ValueError(
              f"Invalid 'template' field in {source_file.name}: "
              f"Expected string, got {type(template).__name__}.\n"
              f"Hint: If you're using placeholders like {{Expression}}, you need to quote them:\n"
              f"  ✗ Wrong:   template: {{Expression}}\n"
              f"  ✓ Correct: template: \"{{Expression}}\"\n"
              f"  ✓ Or use:  template: |\n"
              f"               {{Expression}}"
          )

+     # Validate reserved placeholders are NOT used in chunks
+     reserved_placeholders = ['{prompt}', '{negprompt}', '{loras}']
+     found_reserved = [p for p in reserved_placeholders if p in template]
+     if found_reserved:
+         raise ValueError(
+             f"Invalid template in {source_file.name}: "
+             f"Chunks cannot use reserved placeholders: {', '.join(found_reserved)}. "
+             f"Reserved placeholders are only allowed in template files.\n"
+             f"Chunks are reusable blocks composed into templates, not templates themselves."
+         )

      return ChunkConfig(
          version=data.get('version', '1.0.0'),
          type=data['type'],
          template=template,
          source_file=source_file,
          implements=data.get('implements'),
          imports=data.get('imports') or {},
          defaults=data.get('defaults') or {},
          chunks=data.get('chunks') or {}
      )
```

---

## 3. Changements dans l'Inheritance Resolver

### 3.1 Nouvelle logique de merge - Template Method Pattern

**Fichier:** `CLI/src/templating/resolvers/inheritance_resolver.py`

**Changement majeur:** La méthode `_merge_configs()` doit implémenter l'injection au lieu du remplacement.

```diff
  def _merge_configs(
      self,
      parent: ConfigType,
      child: ConfigType
  ) -> ConfigType:
      """
      Merge parent and child configs according to V2.0 merge rules.
      """
      # Create a deep copy of child to avoid mutations
      merged = deepcopy(child)

      # --- MERGE RULES ---

      # 1. parameters: MERGE (TemplateConfig and PromptConfig)
      if isinstance(child, TemplateConfig) and isinstance(parent, TemplateConfig):
          merged.parameters = {**parent.parameters, **child.parameters}
      elif isinstance(child, PromptConfig) and isinstance(parent, (TemplateConfig, PromptConfig)):
          merged.parameters = {**parent.parameters, **child.parameters}

      # 2. imports: MERGE (all config types)
      merged.imports = {**parent.imports, **child.imports}

      # 3. chunks and defaults: MERGE (ChunkConfig only)
      if isinstance(child, ChunkConfig) and isinstance(parent, ChunkConfig):
          merged.chunks = {**parent.chunks, **child.chunks}
          merged.defaults = {**parent.defaults, **child.defaults}

-     # 4. template: REPLACE with WARNING
-     # Note: child.template always replaces parent.template
-     # We log a warning only if parent had a non-empty template
-     if parent.template and parent.template.strip():
-         if child.template != parent.template:
-             logger.warning(
-                 f"Overriding parent template in {child.source_file.name}. "
-                 f"Consider creating a new base config instead of overriding."
-             )
+     # 4. template: INJECTION (Template Method Pattern)
+     # If parent has {prompt} placeholder → inject child content
+     # Otherwise → replace with warning
+     if isinstance(child, PromptConfig):
+         # PromptConfig has 'prompt' field, not 'template'
+         # Inject child.prompt into parent.template's {prompt}
+         if parent.template and '{prompt}' in parent.template:
+             merged.template = parent.template.replace('{prompt}', child.prompt)
+             logger.debug(
+                 f"Injected prompt from {child.source_file.name} into "
+                 f"{parent.source_file.name}'s {{prompt}} placeholder"
+             )
+         else:
+             # Parent has no {prompt} - this should not happen if validation worked
+             logger.error(
+                 f"Parent template {parent.source_file.name} does not contain {{prompt}} placeholder. "
+                 f"Cannot inject child prompt."
+             )
+             # Keep parent template as-is (validation should have caught this)
+             merged.template = parent.template
+
+     elif isinstance(child, TemplateConfig) and isinstance(parent, TemplateConfig):
+         # Both are templates: inject child.template into parent.template's {prompt}
+         if '{prompt}' in parent.template:
+             merged.template = parent.template.replace('{prompt}', child.template)
+             logger.debug(
+                 f"Injected template from {child.source_file.name} into "
+                 f"{parent.source_file.name}'s {{prompt}} placeholder"
+             )
+         else:
+             # Parent has no {prompt} → REPLACE with warning
+             logger.warning(
+                 f"Parent {parent.source_file.name} has no {{prompt}} placeholder. "
+                 f"Template from {child.source_file.name} will replace parent template completely. "
+                 f"Consider adding {{prompt}} placeholder to parent template."
+             )
+             merged.template = child.template
+
+     elif isinstance(child, ChunkConfig) and isinstance(parent, ChunkConfig):
+         # Chunks: inject if parent has {prompt} (rare), otherwise replace
+         if '{prompt}' in parent.template:
+             merged.template = parent.template.replace('{prompt}', child.template)
+         else:
+             # No {prompt} → standard replace
+             if parent.template and parent.template.strip():
+                 if child.template != parent.template:
+                     logger.warning(
+                         f"Overriding parent template in {child.source_file.name}. "
+                         f"Consider creating a new base chunk instead."
+                     )
+             merged.template = child.template

-     # 5. negative_prompt: REPLACE (TemplateConfig and PromptConfig)
-     # Child's negative_prompt is already set, but we inherit if child didn't specify
-     if hasattr(parent, 'negative_prompt') and hasattr(child, 'negative_prompt'):
-         # If child explicitly provided negative_prompt, use it (already in child)
-         # If child didn't provide (empty or None), inherit from parent
-         if not child.negative_prompt:
-             merged.negative_prompt = parent.negative_prompt
+     # 5. negative_prompt: INJECTION (if {negprompt} present)
+     if hasattr(parent, 'negative_prompt') and hasattr(child, 'negative_prompt'):
+         if parent.negative_prompt and '{negprompt}' in parent.negative_prompt:
+             # Inject child negative_prompt into {negprompt}
+             child_neg = child.negative_prompt if child.negative_prompt else ''
+             merged.negative_prompt = parent.negative_prompt.replace('{negprompt}', child_neg)
+             logger.debug(
+                 f"Injected negative_prompt from {child.source_file.name} into "
+                 f"{{negprompt}} placeholder"
+             )
+         elif child.negative_prompt:
+             # No {negprompt} in parent → child overrides
+             merged.negative_prompt = child.negative_prompt
+         else:
+             # Child has no negative_prompt → inherit from parent
+             merged.negative_prompt = parent.negative_prompt

      return merged
```

### 3.2 Validation de l'héritage des chunks - 1 niveau max

**Fichier:** `CLI/src/templating/resolvers/inheritance_resolver.py`

```diff
  def _validate_chunk_types(
      self,
      child: ChunkConfig,
      parent: ConfigType
  ) -> None:
      """
      Validate type compatibility for chunk inheritance.
      """
      # Parent must be a chunk too
      if not isinstance(parent, ChunkConfig):
          raise ValueError(
              f"Chunk {child.source_file.name} cannot implement "
              f"non-chunk {parent.source_file.name}"
          )

+     # NEW: Validate max 1 level of inheritance
+     # If parent has implements, child cannot implement parent (max 1 level)
+     if parent.implements:
+         raise ValueError(
+             f"Chunk inheritance limited to 1 level: "
+             f"{child.source_file.name} cannot implement {parent.source_file.name} "
+             f"(which already implements {parent.implements}). "
+             f"Chunks can only have definition → implementation (1 level)."
+         )

      # Check type compatibility
      if parent.type != child.type:
          if not parent.type:
              logger.warning(
                  f"Parent {parent.source_file.name} has no type, "
                  f"assuming '{child.type}' from child {child.source_file.name}"
              )
          else:
              raise ValueError(
                  f"Type mismatch: {child.source_file.name} (type='{child.type}') "
                  f"cannot implement {parent.source_file.name} (type='{parent.type}')"
              )
```

---

## 4. Changements dans le Template Resolver

### 4.1 Accès au champ `prompt` pour PromptConfig

**Fichier:** `CLI/src/templating/resolvers/template_resolver.py` (et tous les endroits qui résolvent des templates)

```diff
  def resolve_template(self, config: Union[TemplateConfig, PromptConfig], context: ResolvedContext) -> str:
      """Resolve template with placeholders."""
-     template = config.template
+     # Get the template string based on config type
+     if isinstance(config, PromptConfig):
+         template = config.template  # Already merged with injection by inheritance_resolver
+     else:
+         template = config.template

      # Continue with resolution...
      return resolved_template
```

**Note:** En fait, après l'héritage, le `PromptConfig.template` contient déjà le résultat de l'injection. Le reste du code peut continuer à accéder à `config.template`.

---

## 5. Changements dans les Tests

### 5.1 Tests du Parser

**Fichier:** `CLI/tests/v2/unit/test_parser.py`

```diff
+ class TestPromptConfigValidation:
+     """Tests for prompt.yaml specific validations."""
+
+     def test_parse_prompt_rejects_template_field(self):
+         """Test that 'template:' field is rejected in prompt files."""
+         parser = ConfigParser()
+         data = {
+             'version': '2.0',
+             'name': 'TestPrompt',
+             'generation': {
+                 'mode': 'random',
+                 'seed': 42,
+                 'seed_mode': 'progressive',
+                 'max_images': 10
+             },
+             'template': 'should be prompt'  # Wrong field
+         }
+         source_file = Path('/test/prompt.yaml')
+
+         with pytest.raises(ValueError) as exc_info:
+             parser.parse_prompt(data, source_file)
+
+         assert "must use 'prompt:' field, not 'template:'" in str(exc_info.value)
+
+     def test_parse_prompt_with_prompt_field(self):
+         """Test parsing with correct 'prompt:' field."""
+         parser = ConfigParser()
+         data = {
+             'version': '2.0',
+             'name': 'TestPrompt',
+             'generation': {
+                 'mode': 'random',
+                 'seed': 42,
+                 'seed_mode': 'progressive',
+                 'max_images': 10
+             },
+             'prompt': '1girl, beautiful'  # Correct field
+         }
+         source_file = Path('/test/prompt.yaml')
+
+         config = parser.parse_prompt(data, source_file)
+
+         assert config.prompt == '1girl, beautiful'
+
+ class TestTemplateValidation:
+     """Tests for template.yaml specific validations."""
+
+     def test_parse_template_requires_prompt_placeholder(self):
+         """Test that templates must contain {prompt} placeholder."""
+         parser = ConfigParser()
+         data = {
+             'version': '2.0',
+             'name': 'BadTemplate',
+             'template': 'masterpiece, detailed'  # Missing {prompt}
+         }
+         source_file = Path('/test/template.yaml')
+
+         with pytest.raises(ValueError) as exc_info:
+             parser.parse_template(data, source_file)
+
+         assert 'must contain {prompt} placeholder' in str(exc_info.value)
+
+     def test_parse_template_with_prompt_placeholder(self):
+         """Test parsing template with {prompt} placeholder."""
+         parser = ConfigParser()
+         data = {
+             'version': '2.0',
+             'name': 'GoodTemplate',
+             'template': 'masterpiece, {prompt}, detailed'
+         }
+         source_file = Path('/test/template.yaml')
+
+         config = parser.parse_template(data, source_file)
+
+         assert config.template == 'masterpiece, {prompt}, detailed'
+
+ class TestChunkValidation:
+     """Tests for chunk.yaml specific validations."""
+
+     def test_parse_chunk_rejects_reserved_placeholders(self):
+         """Test that chunks cannot use reserved placeholders."""
+         parser = ConfigParser()
+         data = {
+             'version': '2.0',
+             'type': 'character',
+             'template': '1girl, {prompt}, beautiful'  # Reserved placeholder
+         }
+         source_file = Path('/test/chunk.yaml')
+
+         with pytest.raises(ValueError) as exc_info:
+             parser.parse_chunk(data, source_file)
+
+         assert 'cannot use reserved placeholders' in str(exc_info.value)
+         assert '{prompt}' in str(exc_info.value)
```

### 5.2 Tests de l'Inheritance Resolver

**Fichier:** `CLI/tests/v2/unit/test_inheritance_resolver.py`

```diff
+ class TestTemplateMethodInjection:
+     """Tests for Template Method Pattern injection."""
+
+     def test_inject_prompt_into_template(self):
+         """Test injection of prompt into template's {prompt} placeholder."""
+         # Setup: parent template with {prompt}
+         parent = TemplateConfig(
+             version='2.0',
+             name='Parent',
+             template='masterpiece, {prompt}, detailed',
+             source_file=Path('/test/parent.yaml')
+         )
+
+         # Child prompt
+         child = PromptConfig(
+             version='2.0',
+             name='Child',
+             prompt='1girl, beautiful',
+             generation=GenerationConfig(mode='random', seed=42, seed_mode='progressive', max_images=10),
+             source_file=Path('/test/child.yaml')
+         )
+
+         resolver = InheritanceResolver(YamlLoader(), ConfigParser())
+         merged = resolver._merge_configs(parent, child)
+
+         assert merged.template == 'masterpiece, 1girl, beautiful, detailed'
+
+     def test_inject_negative_prompt(self):
+         """Test injection of negative_prompt into {negprompt} placeholder."""
+         parent = TemplateConfig(
+             version='2.0',
+             name='Parent',
+             template='masterpiece, {prompt}, detailed',
+             negative_prompt='low quality, {negprompt}',
+             source_file=Path('/test/parent.yaml')
+         )
+
+         child = PromptConfig(
+             version='2.0',
+             name='Child',
+             prompt='1girl',
+             negative_prompt='bad anatomy',
+             generation=GenerationConfig(mode='random', seed=42, seed_mode='progressive', max_images=10),
+             source_file=Path('/test/child.yaml')
+         )
+
+         resolver = InheritanceResolver(YamlLoader(), ConfigParser())
+         merged = resolver._merge_configs(parent, child)
+
+         assert merged.negative_prompt == 'low quality, bad anatomy'
+
+     def test_empty_negprompt_placeholder(self):
+         """Test {negprompt} becomes empty if child has no negative_prompt."""
+         parent = TemplateConfig(
+             version='2.0',
+             name='Parent',
+             template='masterpiece, {prompt}, detailed',
+             negative_prompt='low quality, {negprompt}',
+             source_file=Path('/test/parent.yaml')
+         )
+
+         child = PromptConfig(
+             version='2.0',
+             name='Child',
+             prompt='1girl',
+             generation=GenerationConfig(mode='random', seed=42, seed_mode='progressive', max_images=10),
+             source_file=Path('/test/child.yaml')
+         )
+
+         resolver = InheritanceResolver(YamlLoader(), ConfigParser())
+         merged = resolver._merge_configs(parent, child)
+
+         assert merged.negative_prompt == 'low quality, '
+
+ class TestChunkInheritanceLimits:
+     """Tests for chunk inheritance limits."""
+
+     def test_chunk_max_one_level_inheritance(self):
+         """Test that chunks cannot have more than 1 level of inheritance."""
+         # Grandparent chunk
+         grandparent = ChunkConfig(
+             version='2.0',
+             type='character',
+             template='1girl',
+             source_file=Path('/test/grandparent.chunk.yaml')
+         )
+
+         # Parent chunk (implements grandparent)
+         parent = ChunkConfig(
+             version='2.0',
+             type='character',
+             template='1girl, beautiful',
+             implements='grandparent.chunk.yaml',
+             source_file=Path('/test/parent.chunk.yaml')
+         )
+
+         # Child chunk (tries to implement parent)
+         child = ChunkConfig(
+             version='2.0',
+             type='character',
+             template='1girl, beautiful, detailed',
+             implements='parent.chunk.yaml',
+             source_file=Path('/test/child.chunk.yaml')
+         )
+
+         resolver = InheritanceResolver(YamlLoader(), ConfigParser())
+
+         with pytest.raises(ValueError) as exc_info:
+             resolver._validate_chunk_types(child, parent)
+
+         assert 'limited to 1 level' in str(exc_info.value)
```

---

## 6. Checklist d'implémentation

### Phase 1 : Data Models
- [ ] Renommer `PromptConfig.template` → `PromptConfig.prompt`
- [ ] Vérifier tous les accès à `config.template` pour PromptConfig

### Phase 2 : Parser
- [ ] Ajouter validation `{prompt}` obligatoire dans `parse_template()`
- [ ] Ajouter validation placeholders interdits dans `parse_chunk()`
- [ ] Modifier `parse_prompt()` pour utiliser `prompt:` au lieu de `template:`
- [ ] Ajouter validation rejet de `template:` dans `parse_prompt()`

### Phase 3 : Inheritance Resolver
- [ ] Réécrire `_merge_configs()` avec logique d'injection (Template Method)
- [ ] Implémenter injection de `{prompt}` placeholder
- [ ] Implémenter injection de `{negprompt}` placeholder
- [ ] Ajouter validation 1 niveau max pour chunks dans `_validate_chunk_types()`

### Phase 4 : Tests
- [ ] Ajouter tests validation `{prompt}` obligatoire (templates)
- [ ] Ajouter tests validation placeholders interdits (chunks)
- [ ] Ajouter tests rejet `template:` dans prompts
- [ ] Ajouter tests injection `{prompt}` et `{negprompt}`
- [ ] Ajouter tests limite 1 niveau chunks
- [ ] Mettre à jour tous les tests existants utilisant `template:` dans prompts

### Phase 5 : Documentation
- [ ] Remplacer `template-system-v2-spec.md` par la version corrigée
- [ ] Créer guide de migration pour les utilisateurs
- [ ] Mettre à jour exemples dans `/docs/cli/usage/`

### Phase 6 : Fichiers utilisateur
- [ ] Renommer `template:` → `prompt:` dans vos `.prompt.yaml`
- [ ] Ajouter `{prompt}` dans vos `.template.yaml`
- [ ] Tester avec vos fichiers réels

---

## 7. Ordre d'implémentation recommandé

1. **Data Models** (5 min)
   - Rapide, un seul champ à renommer

2. **Parser + Validation** (30 min)
   - Critique : empêche les fichiers invalides d'entrer dans le système
   - Tests faciles à écrire

3. **Inheritance Resolver** (1-2h)
   - Cœur de la logique, complexe
   - Beaucoup de cas à gérer

4. **Tests** (1h)
   - Valide que tout fonctionne
   - Couvre tous les edge cases

5. **Documentation** (30 min)
   - Finalise la migration

**Temps total estimé : ~3-4h**

---

## 8. Risques et points d'attention

### ⚠️ Breaking changes

Tous les fichiers `.prompt.yaml` existants doivent être modifiés :
```yaml
# Avant
template: |
  1girl, beautiful

# Après
prompt: |
  1girl, beautiful
```

Tous les fichiers `.template.yaml` doivent contenir `{prompt}` :
```yaml
# Avant (peut-être absent)
template: |
  masterpiece, detailed

# Après (obligatoire)
template: |
  masterpiece, {prompt}, detailed
```

### ⚠️ Injection récursive

Attention à l'ordre de résolution :
```
base.template → manga.template → portrait.prompt
  {prompt}        {prompt}          prompt content
```

L'injection doit se faire **de bas en haut** (leaf-to-root).

### ⚠️ Normalisation

Après injection, il peut y avoir des virgules en trop :
```
"masterpiece, , detailed"  # Double virgule
```

La normalisation doit gérer ça (déjà implémentée normalement).

---

**Prêt à commencer l'implémentation ?**
