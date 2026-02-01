# Prompt Deployment Pipeline  
CI/CD automation for AI‑generated content using Amazon Bedrock, GitHub Actions, and S3

---

## Summary

This project demonstrates how prompt engineering can be operationalized as a production‑grade CI/CD workflow.

Prompt templates and variables are stored in GitHub. GitHub Actions orchestrates environment‑aware deployments. Amazon Bedrock generates content in real time. Amazon S3 publishes outputs as static websites.

The pipeline treats AI prompts like application code: versioned, reviewed, tested, and deployed.

---

## Key Skills Demonstrated

- CI/CD automation with GitHub Actions  
- Real‑time AI inference using Amazon Bedrock  
- Prompt engineering with structured templates and variables  
- Environment‑based deployments (beta vs production)  
- Secure credential management using GitHub Secrets  
- Static website publishing with Amazon S3  
- Python automation with boto3  

---

## What the Pipeline Does

- Reads structured prompt configuration files (JSON)  
- Renders prompt templates with variables  
- Invokes Amazon Bedrock using real‑time inference  
- Generates HTML or Markdown content  
- Uploads outputs to S3 static website buckets  
- Separates preview and production deployments using branch‑based workflows  
  - Pull requests generate **beta** content  
  - Merges to `main` publish **production** content  

---

## Architecture Overview

- **Source Control:** GitHub  
- **CI/CD:** GitHub Actions  
- **AI Inference:** Amazon Bedrock  
- **Compute:** Serverless (no model hosting)  
- **Storage & Hosting:** Amazon S3 Static Website Hosting  

---

## Repository Structure

    prompts/            Prompt configuration files
    prompt_templates/   Prompt templates
    scripts/            Python automation scripts
    outputs/            Generated content
    .github/workflows/  CI/CD workflows

---

## AI Model Configuration

- **Model:** anthropic.claude-3-sonnet-20240229-v1:0  
- **Invocation type:** Real‑time (on‑demand)  
- **Provisioned throughput:** Not used  

This ensures predictable cost, low operational overhead, and fast execution.

---

## CI/CD Workflows

### Pull Request Workflow
- **Trigger:** Pull requests targeting `main`  
- **Action:** Generate AI content  
- **Output:** Uploaded to `beta/` prefix in S3  

### Merge Workflow
- **Trigger:** Push to `main`  
- **Action:** Generate AI content  
- **Output:** Uploaded to `prod/` prefix in S3  

---

## Security & Configuration

- AWS credentials managed via GitHub Secrets  
- No credentials or sensitive values hardcoded  
- IAM permissions scoped to Bedrock invocation and S3 uploads  

---

## Why This Project Matters

This project demonstrates how AI workflows can be built with the same discipline as modern software systems:

- Automated  
- Version‑controlled  
- Environment‑aware  
- Production‑ready  

It showcases practical cloud engineering, not just model usage.
