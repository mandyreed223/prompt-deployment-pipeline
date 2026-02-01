#!/usr/bin/env python3

# Standard library imports
import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

# Third-party imports
import boto3


# Project folders
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PROJECT_ROOT / "prompts"
TEMPLATES_DIR = PROJECT_ROOT / "prompt_templates"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Bedrock model configuration (required)
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"


def load_json(path: Path) -> Dict[str, Any]:
    # Read and parse JSON config
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    # Read text file contents
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def render_template(template_text: str, variables: Dict[str, Any]) -> str:
    """
    Replace placeholders like {{student_name}} with values from variables dict.
    """
    rendered = template_text

    # Replace each placeholder with its string value
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        rendered = rendered.replace(placeholder, str(value))

    # Optional: detect leftover placeholders so beginners can catch mistakes early
    leftover = re.findall(r"\{\{[^}]+\}\}", rendered)
    if leftover:
        # Leaving placeholders unresolved is usually a mistake
        raise ValueError(
            f"Unresolved template placeholders found: {sorted(set(leftover))}. "
            f"Check your config variables match your template placeholders."
        )

    return rendered


def call_bedrock(prompt: str, max_tokens: int) -> str:
    """
    Invoke Amazon Bedrock using on-demand (real-time) inference.
    Requires AWS credentials + region in environment.
    """
    # Create the Bedrock Runtime client
    client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION"))

    # Required payload structure from your project spec
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": f"""Human: {prompt}"""
            }
        ]
    }

    # Invoke model (on-demand)
    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    # Bedrock returns a streaming-like body wrapper
    raw = response["body"].read().decode("utf-8")
    data = json.loads(raw)

    # Claude responses are typically in content blocks; handle common structure
    # Example shape often includes: {"content":[{"type":"text","text":"..."}], ...}
    content_blocks = data.get("content", [])
    if content_blocks and isinstance(content_blocks, list):
        text_parts = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        if text_parts:
            return "\n".join(text_parts).strip()

    # Fallback if response shape differs
    return json.dumps(data, indent=2)


def ensure_outputs_dir() -> None:
    # Create outputs directory if missing
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def process_one_config(config_path: Path, dry_run: bool) -> Path:
    """
    Process a single prompt config:
    - Load config
    - Load template
    - Render prompt
    - (Optional) send to Bedrock
    - Save output file to outputs/
    Returns the output file path.
    """
    config = load_json(config_path)

    # Validate required fields
    template_file = config.get("template_file")
    output_file = config.get("output_file")
    variables = config.get("variables", {})
    max_tokens = int(config.get("max_tokens", 700))

    if not template_file or not output_file:
        raise ValueError(
            f"Config missing required keys. Need 'template_file' and 'output_file'. "
            f"Problem file: {config_path}"
        )

    template_path = TEMPLATES_DIR / template_file
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}. Check template_file in {config_path.name}."
        )

    # Load template and render prompt
    template_text = load_text(template_path)
    rendered_prompt = render_template(template_text, variables)

    # Decide what gets saved:
    # - dry_run: save the rendered prompt (so you can confirm template substitution)
    # - real run: save the model response
    if dry_run:
        result_text = (
            "DRY RUN MODE\n\n"
            "This is the rendered prompt that would be sent to Bedrock:\n\n"
            + rendered_prompt
        )
    else:
        result_text = call_bedrock(rendered_prompt, max_tokens=max_tokens)

    # Write output to outputs/
    ensure_outputs_dir()
    output_path = OUTPUTS_DIR / output_file
    output_path.write_text(result_text, encoding="utf-8")

    return output_path


def list_prompt_configs() -> List[Path]:
    # Collect all .json configs in prompts/
    if not PROMPTS_DIR.exists():
        return []
    return sorted(PROMPTS_DIR.glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process prompt configs + templates, optionally invoke Bedrock, and save outputs."
    )
    parser.add_argument(
        "--config",
        help="Path to a single config JSON (example: prompts/welcome_prompt.json). If omitted, processes all configs in prompts/."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call Bedrock. Save rendered prompt into outputs/ instead."
    )

    args = parser.parse_args()

    # Decide which configs to process
    if args.config:
        config_path = (PROJECT_ROOT / args.config).resolve()
        configs = [config_path]
    else:
        configs = list_prompt_configs()

    if not configs:
        print("No prompt configs found. Add .json files under prompts/ and try again.")
        return 1

    # Process
    print(f"Found {len(configs)} config file(s).")
    for cfg in configs:
        print(f"\nProcessing: {cfg}")
        out_path = process_one_config(cfg, dry_run=args.dry_run)
        print(f"Saved output: {out_path}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
