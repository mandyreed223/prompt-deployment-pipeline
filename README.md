# Prompt Deployment Pipeline  
CI/CD automation for AI-generated content using Amazon Bedrock, GitHub Actions, and Amazon S3

---

## Overview

This project demonstrates how prompt engineering can be operationalized as a production-grade CI/CD workflow.

Instead of running prompts manually or managing outputs by hand, prompt templates and variables are version-controlled in GitHub, automatically executed through GitHub Actions, and published as static content using Amazon S3.

The result is a repeatable, auditable system where AI prompts are treated like application code — versioned, reviewed, tested, and deployed across environments.

---

## What This Project Does

The pipeline automatically:

- Reads structured prompt configuration files  
- Renders prompt templates with variables  
- Invokes foundation models in real time using Amazon Bedrock  
- Generates HTML or Markdown output  
- Publishes content to static websites hosted in Amazon S3  
- Separates beta and production deployments using branch-based workflows  
  - Pull requests generate preview content  
  - Merges to the main branch publish production content  

---

## Key Skills Demonstrated

- CI/CD automation with GitHub Actions  
- Prompt engineering with structured templates and variables  
- Real-time AI inference (no model hosting)  
- Environment-aware deployments (beta vs production)  
- Secure credential management with GitHub Secrets  
- Static website publishing with Amazon S3  
- Python automation using boto3  

---

## Architecture Overview

- **Source Control:** GitHub  
- **CI/CD:** GitHub Actions  
- **AI Inference:** Amazon Bedrock (real-time only)  
- **Compute:** Serverless  
- **Storage & Hosting:** Amazon S3 Static Website Hosting  

No servers.  
No endpoints.  
No manual uploads.

---

## Repository Structure

    prompts/            Prompt configuration files (JSON)
    prompt_templates/   Prompt templates with variables
    scripts/            Python automation scripts
    outputs/            Generated content
    .github/workflows/  CI/CD workflows
    requirements.txt    Python dependencies
    README.md           Project documentation

---

## AI Model Configuration

- **Model:** anthropic.claude-3-sonnet-20240229-v1:0  
- **Invocation Type:** Real-time (on-demand)  
- **Provisioned Throughput:** Not used  

This keeps costs predictable while avoiding infrastructure management.

---

## CI/CD Workflows

### Pull Request Workflow (Beta)

**Trigger:** Pull requests targeting `main`  

**Behavior:**  
- Renders prompts  
- Invokes Amazon Bedrock  
- Uploads generated content to the `beta/outputs/` prefix in S3  

**Purpose:** Preview and review content before promotion  

---

### Merge Workflow (Production)

**Trigger:** Push or merge to `main`  

**Behavior:**  
- Re-generates content  
- Uploads output to the `prod/outputs/` prefix in S3  

**Purpose:** Publish production-ready content  

---

## Setup and Execution

### Prerequisites

- An AWS account with Amazon Bedrock access enabled  
- Access approved for the Claude 3 Sonnet model  
- Two S3 buckets configured for static website hosting:  
  - one for beta  
  - one for production  
- An IAM user or role with permissions for:  
  - `bedrock:InvokeModel`  
  - `s3:PutObject`  
  - `s3:ListBucket`  
- GitHub Actions enabled on the repository  

---

## Configure GitHub Secrets

Add the following secrets to the repository:

    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_REGION
    S3_BUCKET_BETA
    S3_BUCKET_PROD

Credentials are never hardcoded.

---

## Create Prompt Content

- Prompt configs live in `prompts/`  
- Templates live in `prompt_templates/`  

Templates use simple placeholders such as:

    {{student_name}}
    {{course_name}}

Each output is fully traceable to its config, template, and commit.

---

## Local Validation (Dry Run)

Before invoking cloud services, prompts can be tested locally:

    python scripts/process_prompt.py --dry-run --config prompts/welcome_prompt.json

This renders templates and writes output locally without calling Bedrock or uploading to S3.

---

## Trigger a Deployment

- **Beta:** Open a pull request targeting `main`  
- **Production:** Merge the pull request into `main`  

No manual deployment steps are required.

---

## View Published Content

Generated outputs can be accessed via the S3 static website endpoints, for example:

    /beta/outputs/welcome_jordan.html
    /prod/outputs/summary_module1.md

---

## Project Walkthrough

A full technical walkthrough of this project — including architecture decisions, implementation steps, and issues encountered — is available in the accompanying Medium article.

👉 https://medium.com/@mandymreed/teaching-the-cloud-how-to-write-bbfcd091634f

---

## Why This Project Matters

This project demonstrates how AI workflows can be built with the same discipline as modern software systems.

- Prompts become version-controlled assets.  
- AI output becomes reproducible.  
- Deployment becomes automated.  

It showcases practical cloud engineering, not just model usage.
