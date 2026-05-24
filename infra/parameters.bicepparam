using './main.bicep'

param resourceGroupName = 'rg-zava-hackathon'
param location = 'eastus'
param acrName = 'zavahackacr001'
param containerAppEnvironmentName = 'zava-aca-env'
param containerAppName = 'zava-api-app'
param logAnalyticsWorkspaceName = 'zava-law'
param appInsightsName = 'zava-appinsights'
param postgresServerName = 'zava-postgres-flex'
param postgresDatabaseName = 'zava'
param postgresAdminUsername = 'pgadmin'
param postgresAdminPassword = ''
param containerImageRepository = 'hackathon-starter'
param containerImageTag = 'latest'
param azureOpenAiEndpoint = 'https://your-resource.openai.azure.com'
param azureOpenAiApiKey = ''
param azureOpenAiDeploymentName = 'gpt-4o-mini'
param corsOrigins = '*'
param environment = 'production'
param minReplicas = 0
param maxReplicas = 3
param containerPort = 8000
