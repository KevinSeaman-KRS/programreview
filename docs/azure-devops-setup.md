# Azure DevOps — Program Details

Enterprise home for the UAGC program performance report and related HTML deliverables.

**Project:** [Marketing](https://dev.azure.com/UAGC-Solutions/Marketing)  
**Repository:** Program Details

## Live / published HTML

After a pipeline run on `main`, download the **`program-report-html`** artifact from the run summary. It contains:

| File | Purpose |
|------|---------|
| `index.html` | Main program report (matrix + all detail pages) |
| `program-insights.html` | Standalone YoY mix & program-change analysis |
| `program_report_shareable.html` | Self-contained shareable report (embedded images) |

Optional: configure Azure Storage static website hosting (see below) for a stable internal URL.

## Regenerate reports locally

Requires BigQuery + SQL Server access (see `docs/mcp-setup-guide.md`).

```powershell
cd <repo-root>
uv run python pull_full_data.py
uv run python pull_program_demographics.py
uv run python pull_program_detail_widgets.py
uv run python pull_sankey_flow.py
uv run python pull_program_migration.py
uv run python pull_portfolio_mix_yoy.py
uv run python generate_full_report.py
uv run python generate_program_insights.py
```

Commit and push changes under `deploy/` to trigger the publish pipeline.

## Clone

```powershell
git clone "https://UAGC-Solutions@dev.azure.com/UAGC-Solutions/Marketing/_git/Program%20Details"
```

Use a [Personal Access Token (PAT)](https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate) with **Code (Read & write)** when Git prompts for a password.

## Pipeline

`azure-pipelines.yml` publishes the `deploy/` folder as artifact **`program-report-html`** on every push to `main` that touches `deploy/`.

To enable the pipeline the first time:

1. Azure DevOps → **Pipelines** → **New pipeline**
2. Select **Azure Repos Git** → **Program Details**
3. Choose **Existing Azure Pipelines YAML file** → `/azure-pipelines.yml`
4. Save and run

## Optional: Azure Storage static website

For a persistent internal URL (instead of downloading artifacts):

1. Create a Storage account with **Static website** enabled (`$web` container).
2. Add an Azure Resource Manager service connection in Project Settings.
3. Extend `azure-pipelines.yml` with `AzureFileCopy@6` or `az storage blob upload-batch` to sync `deploy/` → `$web`.

Contact your Azure admin for naming, network rules, and Entra ID access to the site.

## Migration from GitHub

This repo was migrated from `KevinSeaman-KRS/programreview` on GitHub. GitHub Pages and `.github/workflows/deploy-pages.yml` are **legacy**; Azure DevOps is the source of truth for enterprise use.

To add Azure as a remote on an existing clone:

```powershell
git remote add azure "https://UAGC-Solutions@dev.azure.com/UAGC-Solutions/Marketing/_git/Program%20Details"
git push -u azure main
```

## Screenshots

Landing-page screenshots (`deploy/screenshots/`) are generated locally via `capture_all_screenshots.py` and are **gitignored**. For sharing without screenshots, use `program_report_shareable.html` or run `scripts/build_shareable_report.py`.
