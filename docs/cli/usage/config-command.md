# Config Command

The `sdgen config` command provides an interface to read and write configuration values in `sdgen_config.json`, inspired by `git config`.

## Usage

```bash
sdgen config [OPTIONS] [KEY] [VALUE]
```

## Modes

### 1. List all config keys

Display all configuration keys and their values in a table:

```bash
sdgen config list
# or
sdgen config --list
# or
sdgen config -l
```

**Output example:**

```
Configuration
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Key         ┃ Value                 ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ api_url     │ http://127.0.0.1:7860 │
│ configs_dir │ ./prompts             │
│ output_dir  │ ./results             │
│ webui_token │ abc***xyz             │
└─────────────┴───────────────────────┘
```

**Note:** The `webui_token` value is partially masked for security (shows first 3 and last 3 characters only).

### 2. Read a config value

Read the value of a specific config key:

```bash
sdgen config <key>
```

**Examples:**

```bash
# Read API URL
sdgen config api_url
# Output: http://127.0.0.1:7860

# Read configs directory
sdgen config configs_dir
# Output: ./prompts

# Read output directory
sdgen config output_dir
# Output: ./results

# Read webui token (full value, not masked)
sdgen config webui_token
# Output: your-full-token-here
```

### 3. Write a config value

Write a new value to a config key:

```bash
sdgen config <key> <value>
```

**Examples:**

```bash
# Change API URL
sdgen config api_url http://172.29.128.1:7860
# Output: ✓ api_url set to http://172.29.128.1:7860

# Change configs directory
sdgen config configs_dir ./my-prompts
# Output: ✓ configs_dir set to ./my-prompts

# Change output directory
sdgen config output_dir ./my-results
# Output: ✓ output_dir set to ./my-results

# Set webui token
sdgen config webui_token my-secure-token-12345
# Output: ✓ webui_token set to my-secure-token-12345
```

## Valid Config Keys

The following keys are valid in `sdgen_config.json`:

| Key           | Type   | Description                                  | Example                       |
|---------------|--------|----------------------------------------------|-------------------------------|
| `api_url`     | string | URL of the Automatic1111 API                 | `http://127.0.0.1:7860`       |
| `configs_dir` | string | Directory containing template files          | `./prompts`                   |
| `output_dir`  | string | Directory where generated images are saved   | `./results`                   |
| `webui_token` | string | Authentication token for WebUI (optional)    | `abc123...xyz789`             |

## Error Handling

### No config file found

If `sdgen_config.json` doesn't exist in the current directory:

```bash
$ sdgen config list
✗ No config file found.
→ Run 'sdgen init' first.
```

**Solution:** Run `sdgen init` to create the config file.

### Invalid config key

If you try to read or write an invalid key:

```bash
$ sdgen config invalid_key
✗ Config key 'invalid_key' does not exist.
→ Valid keys: api_url, configs_dir, output_dir, webui_token
```

**Solution:** Use one of the valid keys listed above.

### Corrupted JSON file

If the config file contains invalid JSON:

```bash
$ sdgen config list
✗ Config file is invalid.
→ Please fix or recreate with 'sdgen init'.
```

**Solution:** Fix the JSON syntax manually or run `sdgen init --force` to recreate the file.

## Common Workflows

### Check current configuration

```bash
# View all settings
sdgen config list

# Check specific setting
sdgen config api_url
```

### Change API URL (for WSL/Docker)

```bash
# Default (localhost)
sdgen config api_url http://127.0.0.1:7860

# WSL (Windows host)
sdgen config api_url http://172.29.128.1:7860

# Remote server
sdgen config api_url http://192.168.1.100:7860
```

### Change directory paths

```bash
# Use different directory names
sdgen config configs_dir ./templates
sdgen config output_dir ./generated

# Use absolute paths
sdgen config configs_dir /home/user/sd-templates
sdgen config output_dir /mnt/storage/sd-output
```

### Configure WebUI authentication

```bash
# Set authentication token
sdgen config webui_token my-secure-token-12345

# Verify it was set (token will be masked in list)
sdgen config list

# Read full token value (if needed)
sdgen config webui_token
```

## Integration with Other Commands

The `config` command modifies the same `sdgen_config.json` file used by all other `sdgen` commands:

```bash
# Initialize config
sdgen init

# Modify via config command
sdgen config api_url http://172.29.128.1:7860

# Use in other commands
sdgen generate -t template.yaml  # Uses updated api_url
sdgen status                     # Validates config file
sdgen start                      # Uses config for service startup
```

## Scripting and Automation

The `config` command can be used in scripts:

```bash
#!/bin/bash

# Check if config exists
if ! sdgen config list &> /dev/null; then
    echo "Config not found, initializing..."
    sdgen init --force
fi

# Set API URL based on environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows - use localhost
    sdgen config api_url http://127.0.0.1:7860
else
    # WSL - use Windows host IP
    sdgen config api_url http://172.29.128.1:7860
fi

# Verify config
echo "Current API URL: $(sdgen config api_url)"
```

## Security Considerations

- The `webui_token` is **masked** in `sdgen config list` output for security
- The token is stored in **plain text** in `sdgen_config.json`
- To read the full token value, use `sdgen config webui_token`
- Consider setting file permissions to `600` (user-only) for sensitive configs:
  ```bash
  chmod 600 sdgen_config.json
  ```

## See Also

- [`sdgen init`](./init-command.md) - Initialize configuration file
- [`sdgen status`](./status-command.md) - Check services status (validates config)
- [Global Configuration](../../cli/technical/global-config.md) - Technical details about config system
