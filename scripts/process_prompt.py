#!/usr/bin/env python3

# Standard library imports
import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

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
    # Read and parse a JSON config file
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    # Read a text file (template)
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def ensure_outputs_dir() -> None:
    # Create outputs directory if missing
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def render_template(template_text: str, variables: Dict[str, Any]) -> str:
    """
    Replace placeholders like {{student_name}} with values from variables dict.
    """
    rendered = template_text

    # Replace each placeholder with its string value
    for key, value in variables.items():
        # Build placeholder token used in templates
        placeholder = "{{" + key + "}}"

        # Replace placeholder with the provided value
        rendered = rendered.replace(placeholder, str(value))

    # Detect leftover placeholders so you can catch mistakes early
    leftover = re.findall(r"\{\{[^}]+\}\}", rendered)
    if leftover:
        raise ValueError(
            f"Unresolved template placeholders found: {sorted(set(leftover))}. "
            "Make sure your JSON variables match the template placeholders."
        )

    return rendered


def call_bedrock(prompt: str, max_tokens: int) -> str:
    """
    Invoke Amazon Bedrock using on-demand (real-time) inference only.
    """
    # Read region from environment (GitHub Actions will pass this in)
    aws_region = os.environ.get("AWS_REGION")
    if not aws_region:
        raise ValueError("AWS_REGION is not set. Add it as a GitHub secret and pass it into the workflow env.")

    # Create the Bedrock Runtime client
    client = boto3.client("bedrock-runtime", region_name=aws_region)

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
        # Use the exact model ID requested
        modelId=MODEL_ID,
        # Serialize JSON body
        body=json.dumps(body),
        # Content type for Bedrock runtime
        contentType="application/json",
        # Desired response type
        accept="application/json",
    )

    # Read and decode response body
    raw = response["body"].read().decode("utf-8")

    # Parse JSON response
    data = json.loads(raw)

    # Claude responses commonly come back as content blocks like:
    # {"content":[{"type":"text","text":"..."}], ...}
    content_blocks = data.get("content", [])
    if isinstance(content_blocks, list) and content_blocks:
        text_parts: List[str] = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        if text_parts:
            return "\n".join(text_parts).strip()

    # Fallback in case the response shape differs
    return json.dumps(data, indent=2)


def upload_to_s3(local_path: Path, bucket: str, key: str) -> None:
    """
    Upload a local file to S3 at s3://bucket/key
    """
    # Read region from environment
    aws_region = os.environ.get("AWS_REGION")
    if not aws_region:
        raise ValueError("AWS_REGION is not set. Add it as a GitHub secret and pass it into the workflow env.")

    # Create an S3 client
    s3 = boto3.client("s3", region_name=aws_region)

    # Upload the file to S3
    s3.upload_file(str(local_path), bucket, key)


def list_prompt_configs() -> List[Path]:
    # Collect all .json configs in prompts/
    if not PROMPTS_DIR.exists():
        return []
    return sorted(PROMPTS_DIR.glob("*.json"))


def get_bucket_for_env(deploy_env: str) -> str:
    # Select the correct bucket based on environment
    if deploy_env == "beta":
        bucket = os.environ.get("S3_BUCKET_BETA")
    else:
        bucket = os.environ.get("S3_BUCKET_PROD")

    # Validate bucket is present
    if not bucket:
        raise ValueError(
            "Missing S3 bucket environment variables. "
            "Set S3_BUCKET_BETA and S3_BUCKET_PROD in GitHub Secrets and pass them into the workflow env."
        )

    return bucket


def process_one_config(config_path: Path, dry_run: bool, deploy_env: str) -> Path:
    """
    Process a single prompt config:
    - Load config
    - Load template
    - Render prompt
    - (Optional) send to Bedrock
    - Save output file to outputs/
    - (Optional) upload to S3 under beta/ or prod/ prefix
    Returns the output file path.
    """
    # Load the config JSON
    config = load_json(config_path)

    # Read required fields from config
    template_file = config.get("template_file")
    output_file = config.get("output_file")

    # Read optional fields from config
    variables = config.get("variables", {})
    max_tokens = int(config.get("max_tokens", 700))

    # Validate config has the required keys
    if not template_file or not output_file:
        raise ValueError(
            "Config missing required keys. Need 'template_file' and 'output_file'. "
            f"Problem file: {config_path}"
        )

    # Build path to template file
    template_path = TEMPLATES_DIR / template_file

    # Validate template file exists
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}. Check template_file in {config_path.name}."
        )

    # Load template content
    template_text = load_text(template_path)

    # Render the template using the provided variables
    rendered_prompt = render_template(template_text, variables)

    # Ensure outputs directory exists
    ensure_outputs_dir()

    # Build local output path
    output_path = OUTPUTS_DIR / output_file

    # If dry-run, save the rendered prompt so you can confirm substitutions
    if dry_run:
        result_text = (
            "DRY RUN MODE\n\n"
            "This is the rendered prompt that would be sent to Bedrock:\n\n"
            + rendered_prompt
        )
    else:
        # If not dry-run, call Bedrock and save the model response
        result_text = call_bedrock(rendered_prompt, max_tokens=max_tokens)

    # Write output file locally
    output_path.write_text(result_text, encoding="utf-8")

    # Upload to S3 only when not dry-run
    if not dry_run:
        # Get the correct bucket for this environment
        bucket = get_bucket_for_env(deploy_env)

        # Required S3 key format: beta/outputs/... or prod/outputs/...
        s3_key = f"{deploy_env}/outputs/{output_file}"

        # Upload to S3
        upload_to_s3(output_path, bucket=bucket, key=s3_key)

        # Print a clear confirmation line for Actions logs
        print(f"Uploaded to s3://{bucket}/{s3_key}")

    return output_path


def main() -> int:
    # Set up CLI arguments
    parser = argparse.ArgumentParser(
        description="Process prompt configs + templates, optionally invoke Bedrock, save outputs, and upload to S3."
    )
    parser.add_argument(
        "--config",
        help="Path to a single config JSON (example: prompts/welcome_prompt.json). If omitted, processes all configs in prompts/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call Bedrock or upload to S3. Save rendered prompt into outputs/ instead.",
    )

    # Parse CLI arguments
    args = parser.parse_args()

    # Read DEPLOY_ENV from environment (GitHub Actions sets this)
    deploy_env = os.environ.get("DEPLOY_ENV", "beta").strip().lower()

    # Validate DEPLOY_ENV is one of the two allowed values
    if deploy_env not in ("beta", "prod"):
        raise ValueError("DEPLOY_ENV must be 'beta' or 'prod'.")

    # Decide which config(s) to process
    if args.config:
        # Build the config path from repo root + provided relative path
        config_path = (PROJECT_ROOT / args.config).resolve()
        configs = [config_path]
    else:
        # If no config specified, process all configs in prompts/
        configs = list_prompt_configs()

    # If no configs found, exit with a clear message
    if not configs:
        print("No prompt configs found. Add .json files under prompts/ and try again.")
        return 1

    # Print how many configs were found (helps Actions logs)
    print(f"Found {len(configs)} config file(s).")

    # Process each config
    for cfg in configs:
        # Print which config is being processed
        print(f"\nProcessing: {cfg}")

        # Process one config and write output
        out_path = process_one_config(cfg, dry_run=args.dry_run, deploy_env=deploy_env)

        # Print where the output was saved locally
        print(f"Saved output: {out_path}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

