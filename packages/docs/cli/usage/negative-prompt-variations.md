# Negative Prompt Variations

## Overview

You can use placeholders in both the **prompt** and **negative prompt** to vary the negative prompts across different model styles (SDXL, Illustrious, Pony, etc.).

This is useful when:
- Testing the same subject with different negative prompt styles
- Comparing model-specific negative prompts
- Creating variation sets with different quality filters

## Basic Usage

### JSON Config Format

```json
{
  "version": "1.0",
  "name": "Negative Prompt Variations Example",
  "prompt": {
    "template": "masterpiece, {Subject}, highly detailed",
    "negative": "{NegStyle}"
  },
  "variations": {
    "Subject": "./subjects.txt",
    "NegStyle": "./negative_styles.txt"
  }
}
```

### Variation File Example

**negative_styles.txt:**
```
# Model-specific negative prompts
sdxl→low quality, bad anatomy, blurry, watermark
illustrious→worst quality, low quality, displeasing, very displeasing
pony→3d, worst quality, low quality, bad anatomy, text
none→
```

## Shared Placeholders

You can use the **same placeholder** in both prompt and negative prompt to ensure consistency:

```json
{
  "prompt": {
    "template": "{Style} artwork, beautiful landscape",
    "negative": "bad {Style}, low quality"
  },
  "variations": {
    "Style": "./styles.txt"
  }
}
```

**styles.txt:**
```
anime
realistic
oil painting
watercolor
```

**Result:**
- When `Style = "anime"` → Prompt: `"anime artwork, beautiful landscape"` / Negative: `"bad anime, low quality"`
- When `Style = "realistic"` → Prompt: `"realistic artwork, beautiful landscape"` / Negative: `"bad realistic, low quality"`

## Advanced Selectors

All placeholder selectors work in negative prompts:

### Limit to N variations

```json
{
  "prompt": {
    "template": "masterpiece, beautiful girl",
    "negative": "{NegStyle:2}"
  }
}
```

Uses only 2 random negative styles.

### Select Specific Indices

```json
{
  "prompt": {
    "template": "masterpiece, beautiful girl",
    "negative": "{NegStyle:#|0|2}"
  }
}
```

Uses only index 0 and 2 from the negative styles file.

### Priority Weights

```json
{
  "prompt": {
    "template": "{Subject:$5}, {Style:$10}",
    "negative": "{NegStyle:$2}"
  }
}
```

Controls the order of combinatorial loops (lower weight = outer loop).

## Combinations

When using placeholders in both prompt and negative, all combinations are generated:

**Example:**

```json
{
  "prompt": {
    "template": "{Subject}",
    "negative": "{NegStyle}"
  },
  "variations": {
    "Subject": ["girl", "boy"],
    "NegStyle": ["style1", "style2"]
  }
}
```

**Generates 4 images:**
1. Subject: girl, NegStyle: style1
2. Subject: girl, NegStyle: style2
3. Subject: boy, NegStyle: style1
4. Subject: boy, NegStyle: style2

## Use Cases

### 1. Model Comparison

Compare the same prompt with different model-specific negatives:

```json
{
  "prompt": {
    "template": "masterpiece, beautiful anime girl, detailed face"
  },
  "negative": "{ModelNeg}"
  },
  "variations": {
    "ModelNeg": "./model_negatives.txt"
  }
}
```

### 2. Quality Level Testing

Test different quality filter levels:

```json
{
  "negative": "{QualityFilter}"
  },
  "variations": {
    "QualityFilter": ["low quality", "worst quality, low quality", "worst quality, low quality, bad anatomy"]
  }
}
```

### 3. Combined Subject + Negative Testing

```json
{
  "prompt": {
    "template": "{Character}, {Pose}"
  },
  "negative": "{NegStyle}, {Defect}"
  },
  "variations": {
    "Character": "./characters.txt",
    "Pose": "./poses.txt",
    "NegStyle": "./neg_styles.txt",
    "Defect": ["blurry", "distorted", "low resolution"]
  }
}
```

This generates all combinations of characters, poses, negative styles, and defects.

## Metadata

All negative prompt variations are saved in the `metadata.json`:

```json
{
  "variations": {
    "NegStyle": {
      "sdxl": "low quality, bad anatomy, blurry, watermark",
      "illustrious": "worst quality, low quality, displeasing"
    }
  },
  "prompt": {
    "template": "masterpiece, {Subject}",
    "negative_template": "{NegStyle}"
  }
}
```

## Empty Negative Prompts

You can include an empty negative prompt as a variation:

```
sdxl→low quality, bad anatomy
illustrious→worst quality, displeasing
none→
```

The `none` option will generate images with no negative prompt.

## Tips

1. **Model-Specific Testing**: Create separate files for each model's recommended negative prompts
2. **Incremental Quality**: Test different levels of quality filters to find the optimal balance
3. **Shared Styles**: Use the same `{Style}` placeholder in both prompts to maintain consistency
4. **Filename Keys**: Include `"NegStyle"` in `output.filename_keys` to identify which negative was used

## Example Complete Config

```json
{
  "version": "1.0",
  "name": "Model Negative Comparison",
  "description": "Test same subject across different model negatives",
  "prompt": {
    "template": "masterpiece, {Subject}, highly detailed, best quality",
    "negative": "{ModelNeg}"
  },
  "variations": {
    "Subject": "./subjects.txt",
    "ModelNeg": "./model_negatives.txt"
  },
  "generation": {
    "mode": "combinatorial",
    "seed": 42,
    "seed_mode": "progressive",
    "max_images": -1
  },
  "parameters": {
    "width": 512,
    "height": 768,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler": "DPM++ 2M Karras"
  },
  "output": {
    "session_name": "model_neg_comparison",
    "filename_keys": ["Subject", "ModelNeg"]
  }
}
```

This will generate all combinations of subjects × model negatives with progressive seeds.
