# Tools - Utilities for SD Generator

**Helper scripts and tools for the SD Generator project.**

---

## Available Tools

### `reverse_config.py` - Generate JSON Config from Session

Reverse engineers a JSON config file from an existing session directory.

**What it does:**
1. Parses `session_config.txt` to extract prompts and parameters
2. Extracts PNG metadata (seed, sampler, etc.) from first image
3. Detects placeholders in prompt template
4. Generates a complete JSON config file

**Usage:**

```bash
# Generate config from session
python3 tools/reverse_config.py --session apioutput/20250928_203333_facial_expressions

# Preview without writing (dry-run)
python3 tools/reverse_config.py --session apioutput/20250928_203333_facial_expressions --dry-run

# Custom output path
python3 tools/reverse_config.py --session apioutput/20250928_203333_facial_expressions --output configs/my_config.json

# Use inline variations (experimental)
python3 tools/reverse_config.py --session apioutput/20250928_203333_facial_expressions --inline
```

**What gets extracted:**

✅ **From `session_config.txt`:**
- Prompt template (with placeholders)
- Negative prompt
- Generation parameters (steps, CFG, sampler, etc.)
- Session name and date
- Number of images requested
- Base seed

✅ **From PNG metadata (first image):**
- Actual seed used
- Sampler (overrides session_config if different)
- Image dimensions
- Steps and CFG scale

✅ **Auto-detected:**
- Placeholders in prompt (`{PlaceholderName}`)
- Filename keys for output

**What you need to update manually:**

⚠️ **Variation file paths** - Script generates placeholder paths like:
```json
"variations": {
  "FacialExpression": "./variations/facialexpressions.txt"
}
```

You need to update these to the actual file paths or use inline variations.

⚠️ **Generation modes** - Script defaults to:
- `mode: "combinatorial"`
- `seed_mode: "progressive"`

Update if your original session used different modes.

**Example workflow:**

```bash
# 1. Generate config from old session
python3 tools/reverse_config.py --session CLI/apioutput/2025-09-28_203333_facial_expressions

# 2. Edit the generated config
#    - Update variation file paths
#    - Verify generation modes
nano configs/regenerate_facial_expressions.json

# 3. Test the config
python3 CLI/generator_cli.py --config configs/regenerate_facial_expressions.json --list

# 4. Run generation
python3 CLI/generator_cli.py --config configs/regenerate_facial_expressions.json
```

**Requirements:**
- Python 3.8+
- PIL/Pillow (for PNG metadata extraction)

**Exit codes:**
- `0` - Success
- `1` - Error (missing session, invalid config, etc.)

---

## Future Tools (Planned)

- `batch_process.py` - Process multiple configs in sequence
- `config_template.py` - Create config from templates
- `variation_extractor.py` - Extract variations from session filenames
- `thumbnail_generator.py` - Generate WebP thumbnails for existing sessions

---

**Last Updated:** 2025-10-01
