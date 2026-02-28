# Azure Deployment Placeholder

## Target service mapping
- PostgreSQL: Azure Database for PostgreSQL Flexible Server
- API + batch jobs: Azure Container Registry + Azure Container Apps
- UI: Azure Static Web Apps (or Container Apps)

## Configuration
- Keep a single `DATABASE_URL` setting for local and Azure.
- In Azure, point `DATABASE_URL` to the PostgreSQL Flexible Server connection string.
- Keep `OPENFDA_API_KEY` optional and inject via Azure secrets.

## Notes
- Deployment scripts are intentionally not implemented in this iteration.
- Future work: Bicep/Terraform modules and CI/CD pipelines.
