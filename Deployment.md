# Deployment Guide

This document explains the GitHub Actions CI/CD pipeline defined in `.github/workflows/deploy-containerapp.yml`. The pipeline deploys the application to **Azure Container Apps** using a two-stage approach to ensure the Docker image is built and pushed before the full infrastructure is provisioned.

---

## Table of Contents

1. [Trigger Conditions](#trigger-conditions)
2. [Permissions](#permissions)
3. [Environment Variables](#environment-variables)
4. [Pipeline Overview](#pipeline-overview)
5. [Stage 1 — Deploy ACR & Build Image](#stage-1--deploy-acr--build-image)
   - [Extract params from bicepparam](#step-extract-params-from-bicepparam)
   - [Azure login (OIDC)](#step-azure-login-oidc)
   - [Deploy ACR (Stage 1 Bicep)](#step-deploy-acr-stage-1-bicep)
   - [Get ACR login server](#step-get-acr-login-server)
   - [Build & push Docker image](#step-build--push-docker-image)
6. [Stage 2 — Deploy App Infrastructure](#stage-2--deploy-app-infrastructure)
   - [Install Bicep & compile params](#step-install-bicep--compile-params)
   - [Azure login (OIDC)](#step-azure-login-oidc-1)
   - [Deploy app infrastructure (main.bicep)](#step-deploy-app-infrastructure-mainbicep)
   - [Print Container App URL](#step-print-container-app-url)
7. [Required Secrets & Variables](#required-secrets--variables)
8. [Infrastructure Files](#infrastructure-files)

---

## Trigger Conditions

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

The pipeline runs automatically on every push to the `main` branch, and can also be triggered manually from the GitHub Actions UI via `workflow_dispatch`.

---

## Permissions

```yaml
permissions:
  id-token: write
  contents: read
```

- **`id-token: write`** — Required for OpenID Connect (OIDC) authentication with Azure. This allows GitHub to generate a short-lived token that Azure trusts, eliminating the need for long-lived client secrets stored in GitHub.
- **`contents: read`** — Allows the workflow to check out the repository code.

---

## Environment Variables

```yaml
env:
  AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
  AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
```

These make the three Azure identity secrets available as shell environment variables (`$AZURE_SUBSCRIPTION_ID`, etc.) for local debugging and scripting. In the workflow itself, the `azure/login` action reads them directly from `secrets.*`.

---

## Pipeline Overview

```
push to main
     │
     ▼
┌─────────────────────────────────────┐
│  Stage 1: deploy-acr-and-build      │
│  1. Extract params from .bicepparam  │
│  2. Login to Azure (OIDC)            │
│  3. Deploy ACR via stage1.bicep      │
│  4. Read ACR login server URL        │
│  5. Build & push Docker image        │
└──────────────┬──────────────────────┘
               │  outputs: container_image, resource_group, acr_name
               ▼
┌─────────────────────────────────────┐
│  Stage 2: deploy-app                │
│  1. Install Bicep CLI               │
│  2. Compile .bicepparam → .json     │
│  3. Login to Azure (OIDC)           │
│  4. Deploy full infra via main.bicep│
│  5. Print the Container App URL     │
└─────────────────────────────────────┘
```

Stage 2 only starts after Stage 1 completes successfully (`needs: deploy-acr-and-build`). The fully-qualified Docker image reference built in Stage 1 is passed to Stage 2 via job outputs.

---

## Stage 1 — Deploy ACR & Build Image

**Job ID:** `deploy-acr-and-build`  
**Runner:** `ubuntu-latest`

### Job Outputs

| Output | Source step | Description |
|---|---|---|
| `acr_login_server` | `acr-output` | Hostname of the Azure Container Registry (e.g. `vczavaacr260524.azurecr.io`) |
| `container_image` | `acr-output` | Fully-qualified image reference with the commit SHA tag |
| `resource_group` | `params` | Resource group name read from the `.bicepparam` file |
| `acr_name` | `params` | ACR resource name read from the `.bicepparam` file |

---

### Step: Extract params from bicepparam

```yaml
- name: Extract params from bicepparam
  id: params
  run: |
    set -euo pipefail
    RG=$(grep 'param resourceGroupName' infra/parameters.bicepparam | sed "s/.*= '\(.*\)'/\1/")
    ACR=$(grep 'param acrName' infra/parameters.bicepparam | sed "s/.*= '\(.*\)'/\1/")
    LOC=$(grep 'param location' infra/parameters.bicepparam | sed "s/.*= '\(.*\)'/\1/")
    echo "resource_group=$RG" >> "$GITHUB_OUTPUT"
    echo "acr_name=$ACR"      >> "$GITHUB_OUTPUT"
    echo "location=$LOC"      >> "$GITHUB_OUTPUT"
```

**Purpose:** Reads `resourceGroupName`, `acrName`, and `location` out of `infra/parameters.bicepparam` using `grep`/`sed`, then publishes them as step outputs. This keeps the resource names as the single source of truth in the `.bicepparam` file rather than duplicating them in the YAML.

**`set -euo pipefail`** — Shell strict mode:
- `-e` — exit immediately if any command fails
- `-u` — treat unset variables as errors
- `-o pipefail` — a pipeline fails if any command in it fails (not just the last one)

This prevents silent failures where an empty `grep` result would pass undetected into later steps.

---

### Step: Azure login (OIDC)

```yaml
- name: Azure login (OIDC)
  uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

**Purpose:** Authenticates the runner to Azure using **OIDC (Workload Identity Federation)**. GitHub generates a short-lived OIDC token and exchanges it for an Azure access token. No long-lived passwords or certificates are stored in GitHub Secrets — only the app registration IDs.

**Prerequisite:** The Azure AD app registration identified by `AZURE_CLIENT_ID` must have a **federated credential** configured for `repo:Chinjila/Hackathon-starter:ref:refs/heads/main`.

---

### Step: Deploy ACR (Stage 1 Bicep)

```yaml
- name: Deploy ACR (Stage 1 Bicep)
  run: |
    az deployment sub create \
      --name "stage1-${{ github.run_id }}" \
      --location "${{ steps.params.outputs.location }}" \
      --template-file infra/stage1.bicep \
      --parameters \
        resourceGroupName="${{ steps.params.outputs.resource_group }}" \
        location="${{ steps.params.outputs.location }}" \
        acrName="${{ steps.params.outputs.acr_name }}"
```

**Purpose:** Runs a subscription-scoped Bicep deployment using `infra/stage1.bicep`, which creates the resource group and the Azure Container Registry (ACR). This is done as a separate stage so the Docker image can be built and pushed before the Container App infrastructure is provisioned (which needs the image reference at deploy time).

**Deployment name** is `stage1-<run_id>` — unique per workflow run, used in the next step to query outputs.

**`infra/stage1.bicep`** — A lightweight Bicep template that provisions only:
- Resource group
- Azure Container Registry (with admin user enabled)

---

### Step: Get ACR login server

```yaml
- name: Get ACR login server
  id: acr-output
  run: |
    set -euo pipefail
    SERVER=$(az deployment sub show \
      --name "stage1-${{ github.run_id }}" \
      --query "properties.outputs.acrLoginServer.value" \
      -o tsv)
    IMAGE="${SERVER}/hackathon-starter:${{ github.sha }}"
    echo "acr_login_server=$SERVER" >> "$GITHUB_OUTPUT"
    echo "container_image=$IMAGE"   >> "$GITHUB_OUTPUT"
```

**Purpose:** Queries the completed Stage 1 deployment to retrieve the ACR's login server hostname from its Bicep output (`acrLoginServer`). Constructs the full Docker image tag as `<acr-hostname>/hackathon-starter:<git-sha>`, which uniquely identifies this build. Both values are published as job outputs for consumption in Stage 2.

Using the **commit SHA** as the image tag (rather than `latest`) ensures every deployment is traceable to an exact commit and prevents cache ambiguity.

---

### Step: Build & push Docker image

```yaml
- name: Build & push Docker image
  run: |
    set -euo pipefail
    az acr login --name "${{ steps.params.outputs.acr_name }}"
    docker build -t "${{ steps.acr-output.outputs.container_image }}" .
    docker push "${{ steps.acr-output.outputs.container_image }}"
```

**Purpose:** 
1. **`az acr login`** — Authenticates Docker to the ACR using the currently logged-in Azure identity (no separate password needed).
2. **`docker build`** — Builds the container image from the `Dockerfile` in the repo root, tagging it with the full ACR image reference.
3. **`docker push`** — Pushes the built image to ACR. Stage 2 will reference this image when creating the Container App.

**Prerequisite:** The service principal must have the **`AcrPush`** role (or `Contributor`) on the ACR resource.

---

## Stage 2 — Deploy App Infrastructure

**Job ID:** `deploy-app`  
**Runner:** `ubuntu-latest`  
**Depends on:** `deploy-acr-and-build` (runs only after Stage 1 succeeds)

---

### Step: Install Bicep & compile params

```yaml
- name: Install Bicep & compile params
  run: |
    az bicep install
    az bicep build-params --file infra/parameters.bicepparam --outfile infra/parameters.json
```

**Purpose:** 

- **`az bicep install`** — Downloads the Bicep CLI binary onto the runner. While `ubuntu-latest` includes Azure CLI, the Bicep binary may be absent or outdated. This ensures a current version is always present.
- **`az bicep build-params`** — Compiles `infra/parameters.bicepparam` (Bicep typed parameter syntax) into a standard ARM JSON parameters file (`parameters.json`). This is necessary because older Azure CLI versions do not natively understand the `.bicepparam` format when passed via `--parameters @file`. The compiled JSON file is universally supported.

**Why a placeholder?** `parameters.bicepparam` includes `param containerImage = 'placeholder'` because `az bicep build-params` validates that all required parameters (those without defaults in `main.bicep`) have an assignment. The placeholder satisfies the compiler; the real image reference overrides it at deploy time via `--parameters containerImage=...`.

---

### Step: Azure login (OIDC)

Same OIDC login as Stage 1 — each job runs on a fresh runner so authentication must be repeated.

---

### Step: Deploy app infrastructure (main.bicep)

```yaml
- name: Deploy app infrastructure (main.bicep)
  run: |
    az deployment sub create \
      --name "stage2-${{ github.run_id }}" \
      --location canadacentral \
      --template-file 'infra/main.bicep' \
      --parameters @infra/parameters.json \
      --parameters \
        containerImage="${{ needs.deploy-acr-and-build.outputs.container_image }}" \
        postgresAdminPassword="${{ secrets.POSTGRES_ADMIN_PASSWORD }}" \
        azureOpenAiApiKey="${{ secrets.AZURE_OPENAI_API_KEY }}" \
        azureOpenAiEndpoint="${{ vars.AZURE_OPENAI_ENDPOINT }}" \
        azureOpenAiDeploymentName="${{ vars.AZURE_OPENAI_DEPLOYMENT_NAME }}"
```

**Purpose:** Runs the full subscription-scoped Bicep deployment using `infra/main.bicep`, which provisions all remaining infrastructure:
- Resource group (idempotent)
- Azure Container Registry (idempotent)
- Log Analytics Workspace
- Application Insights
- PostgreSQL Flexible Server + database
- Container Apps Environment
- Container App (using the image built in Stage 1)

**Two `--parameters` flags:** Azure CLI accepts multiple `--parameters` flags. The first (`@infra/parameters.json`) loads all default values from the compiled file. The second block **overrides** specific values with runtime data (secrets, the live image reference). Later flags take precedence over earlier ones.

**Parameter sources:**

| Parameter | Source | Reason |
|---|---|---|
| `containerImage` | Stage 1 job output | Built dynamically — not known until Stage 1 completes |
| `postgresAdminPassword` | `secrets.*` | Sensitive — must never be stored in files |
| `azureOpenAiApiKey` | `secrets.*` | Sensitive — must never be stored in files |
| `azureOpenAiEndpoint` | `vars.*` | Non-sensitive config — safe to store as a repo variable |
| `azureOpenAiDeploymentName` | `vars.*` | Non-sensitive config — safe to store as a repo variable |

---

### Step: Print Container App URL

```yaml
- name: Print Container App URL
  run: |
    set -euo pipefail
    RG="${{ needs.deploy-acr-and-build.outputs.resource_group }}"
    APP=$(grep 'param containerAppName' infra/parameters.bicepparam | sed "s/.*= '\(.*\)'/\1/")
    URL=$(az containerapp show \
      --name "$APP" \
      --resource-group "$RG" \
      --query "properties.configuration.ingress.fqdn" \
      -o tsv)
    echo "Container App URL: https://$URL"
```

**Purpose:** After a successful deployment, queries the Container App's fully-qualified domain name (FQDN) from Azure and prints it to the workflow log. This gives a quick, clickable confirmation that the app is live.

---

## Required Secrets & Variables

Configure these in your repository under **Settings → Secrets and variables → Actions**.

### Secrets (`secrets.*`)

| Name | Description |
|---|---|
| `AZURE_CLIENT_ID` | Application (client) ID of the Azure AD app registration used for OIDC |
| `AZURE_TENANT_ID` | Azure Active Directory tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID to deploy into |
| `POSTGRES_ADMIN_PASSWORD` | Password for the PostgreSQL Flexible Server admin user |
| `AZURE_OPENAI_API_KEY` | API key for the Azure OpenAI service |

### Repository Variables (`vars.*`)

| Name | Example Value | Description |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | `https://swedencentral.api.cognitive.microsoft.com/` | Azure OpenAI service endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4.1` | Name of the deployed model in Azure OpenAI |

### OIDC Federated Credential

The app registration (`AZURE_CLIENT_ID`) must have a federated identity credential with:

- **Issuer:** `https://token.actions.githubusercontent.com`
- **Subject:** `repo:Chinjila/Hackathon-starter:ref:refs/heads/main`
- **Audience:** `api://AzureADTokenExchange`

### RBAC

The service principal needs the following role assignments:

| Role | Scope | Required for |
|---|---|---|
| `Contributor` | Subscription | Creating resource groups and all resources via Bicep |
| `AcrPush` | ACR resource | `docker push` in Stage 1 (covered by `Contributor` on the subscription) |

---

## Infrastructure Files

| File | Scope | Purpose |
|---|---|---|
| `infra/stage1.bicep` | Subscription | Creates resource group + ACR only |
| `infra/main.bicep` | Subscription | Creates all resources (ACR, monitoring, DB, Container App) |
| `infra/parameters.bicepparam` | — | Default parameter values for `main.bicep` (Bicep typed syntax) |
| `infra/modules/acr.bicep` | Resource group | Azure Container Registry module |
| `infra/modules/database.bicep` | Resource group | PostgreSQL Flexible Server module |
| `infra/modules/containerapp.bicep` | Resource group | Container Apps Environment + Container App module |
| `infra/modules/monitoring.bicep` | Resource group | Log Analytics Workspace + Application Insights module |
