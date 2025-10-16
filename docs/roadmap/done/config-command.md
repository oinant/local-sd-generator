# Config Command

**Status:** done
**Priority:** 5
**Component:** cli
**Created:** 2025-10-16
**Completed:** 2025-10-16

## Description

Ajouter une commande `sdgen config` pour lire/écrire les valeurs de configuration, inspirée de `git config`.

Interface utilisateur simple et intuitive pour gérer `sdgen_config.json` sans éditer manuellement le fichier.

## Use Cases

```bash
# Afficher l'aide
sdgen config --help

# Lister toutes les config keys et leurs valeurs
sdgen config list

# Lire une valeur
sdgen config api_url
# Output: http://127.0.0.1:7860

# Écrire une valeur
sdgen config api_url http://172.29.128.1:7860
# Output: ✓ api_url set to http://172.29.128.1:7860

# Lire une config inexistante
sdgen config foo
# Output: ✗ Config key 'foo' does not exist

# Écrire dans une clé inexistante
sdgen config foo bar
# Output: ✗ Config key 'foo' does not exist
#         Valid keys: api_url, configs_dir, output_dir, webui_token
```

## Implementation

### Command signature

```python
@app.command(name="config")
def config_command(
    key: Optional[str] = typer.Argument(None, help="Config key to read/write"),
    value: Optional[str] = typer.Argument(None, help="Value to set (optional)"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all config keys"),
) -> None:
    """
    Read or write configuration values.

    Examples:
        sdgen config list              # List all config
        sdgen config api_url           # Read api_url
        sdgen config api_url http://... # Set api_url
    """
```

### Behavior

1. **`sdgen config --list`** ou **`sdgen config list`**
   - Affiche toutes les clés et valeurs dans un tableau Rich
   - Format : Table avec colonnes `Key | Value`
   - Si `webui_token` est défini, masquer partiellement (`abc***xyz`)

2. **`sdgen config <key>`** (read mode)
   - Vérifie que `sdgen_config.json` existe
   - Vérifie que `<key>` est une clé valide
   - Affiche la valeur brute (pas de formatting)
   - Exit code 0 si succès, 1 si erreur

3. **`sdgen config <key> <value>`** (write mode)
   - Vérifie que `sdgen_config.json` existe
   - Vérifie que `<key>` est une clé valide
   - Écrit la nouvelle valeur dans le fichier JSON
   - Affiche confirmation : `✓ <key> set to <value>`
   - Exit code 0 si succès, 1 si erreur

4. **Error handling**
   - Si pas de `sdgen_config.json` → Message : "No config file found. Run 'sdgen init' first."
   - Si clé invalide → Lister les clés valides
   - Si JSON corrompu → Message : "Config file is invalid. Please fix or recreate with 'sdgen init'."

### Valid config keys

Les clés valides correspondent aux champs de `GlobalConfig` :
- `api_url` (str)
- `configs_dir` (str)
- `output_dir` (str)
- `webui_token` (Optional[str])

### Type validation

- Pas de validation de type stricte pour l'instant (tout est string)
- Validation basique : chemins relatifs OK, URLs OK
- Future improvement : validation de type selon la clé

## Tasks

- [x] Créer fonction `config_command()` dans `commands.py`
- [x] Implémenter mode `list` (table Rich)
- [x] Implémenter mode `read` (afficher valeur)
- [x] Implémenter mode `write` (modifier JSON)
- [x] Gérer erreurs (fichier manquant, clé invalide, JSON corrompu)
- [x] Masquer partiellement `webui_token` dans `list`
- [x] Ajouter tests unitaires pour les 3 modes
- [x] Ajouter doc utilisateur dans `docs/cli/usage/config-command.md`
- [x] Mettre à jour `--help` principal avec mention de `config`

## Success Criteria

- ✅ `sdgen config list` affiche toutes les config
- ✅ `sdgen config <key>` lit une valeur
- ✅ `sdgen config <key> <value>` écrit une valeur
- ✅ Erreurs claires si fichier manquant ou clé invalide
- ✅ Tests unitaires couvrant les 3 modes + erreurs
- ✅ Mypy strict OK

## Tests

### Unit tests à créer

```python
# tests/commands/test_config_command.py

def test_config_list_displays_all_keys(tmp_path):
    """Test that 'config list' shows all config keys"""
    pass

def test_config_read_existing_key(tmp_path):
    """Test reading a valid config key"""
    pass

def test_config_read_invalid_key(tmp_path):
    """Test reading an invalid key shows error"""
    pass

def test_config_write_existing_key(tmp_path):
    """Test writing to a valid config key"""
    pass

def test_config_write_invalid_key(tmp_path):
    """Test writing to invalid key shows error"""
    pass

def test_config_no_file_shows_error():
    """Test error when no config file exists"""
    pass

def test_config_list_masks_webui_token(tmp_path):
    """Test that webui_token is partially masked in list output"""
    pass
```

Environ 7-10 tests unitaires.

## Documentation

- **Usage:** `docs/cli/usage/config-command.md`
- **Technical:** Déjà couvert par `global_config.py` docs

## Notes

### Alternative syntaxes considérées

1. **Flags pour read/write** (rejeté - trop verbeux)
   ```bash
   sdgen config --get api_url
   sdgen config --set api_url http://...
   ```

2. **Subcommands** (rejeté - moins intuitif que git)
   ```bash
   sdgen config get api_url
   sdgen config set api_url http://...
   ```

3. **Syntaxe actuelle** (choisie - la plus simple)
   ```bash
   sdgen config api_url          # read
   sdgen config api_url value    # write
   ```

### Future improvements

- [ ] Validation de type selon la clé (URLs valides, chemins existants, etc.)
- [ ] Support de `--unset` pour supprimer une valeur (webui_token → null)
- [ ] Support de `--edit` pour ouvrir l'éditeur
- [ ] Support de `--global` pour une config globale (~/.sdgen/config.json)
- [ ] Autocomplétion des clés (shell completion)

### Security considerations

- `webui_token` doit être masqué dans `list` (afficher `abc***xyz`)
- Pas d'échappement spécial nécessaire (JSON natif)
- Permissions du fichier : user-only (644 ou 600)

## Dependencies

- `rich` (déjà installé) pour le tableau
- `typer` (déjà installé) pour les arguments
- Standard library `json` pour read/write

## Estimated effort

**Small** (~2-3h)
- Command implementation : 1h
- Tests : 1h
- Documentation : 30min

## Implementation Summary

**Completed:** 2025-10-16

### Files Modified/Created

1. **Command Implementation:**
   - `packages/sd-generator-cli/sd_generator_cli/commands.py:236-330` - Added `config_command()` function
   - `packages/sd-generator-cli/sd_generator_cli/cli.py:77,84` - Registered command in CLI app

2. **Tests:**
   - `packages/sd-generator-cli/tests/unit/test_config_command.py` - 17 unit tests (all passing)
   - `packages/sd-generator-cli/tests/test_cli_commands.py:156-164` - Integration test for help

3. **Documentation:**
   - `docs/cli/usage/config-command.md` - Complete usage documentation with examples

### Test Coverage

**17 tests (100% passing):**
- 1 help test
- 4 list mode tests (including token masking)
- 3 read mode tests
- 4 write mode tests
- 5 error handling tests

### Type Safety

- ✅ All functions have complete type hints
- ✅ Mypy strict mode passes with no errors
- ✅ Exit codes: 0 for success, 1 for errors

### Features Implemented

1. **List mode** (`sdgen config list`):
   - Rich table display with all config keys
   - Automatic masking of `webui_token` (shows `abc***xyz`)
   - Shows "not set" for missing optional values

2. **Read mode** (`sdgen config <key>`):
   - Outputs raw value to stdout
   - Error handling for invalid keys with helpful suggestions

3. **Write mode** (`sdgen config <key> <value>`):
   - Updates JSON file with new value
   - Preserves JSON formatting (2-space indentation)
   - Success confirmation message

4. **Error handling:**
   - Missing config file → Suggests `sdgen init`
   - Invalid key → Lists all valid keys
   - Corrupted JSON → Clear error message

### Security

- `webui_token` is masked in list output (first 3 + last 3 chars only)
- Full token readable via `sdgen config webui_token` when needed
- JSON file written with proper formatting and trailing newline
