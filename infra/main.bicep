targetScope = 'subscription'

@description('Name of the resource group that will contain the hackathon stack.')
param resourceGroupName string = 'rg-azure-hackathon'

@description('Azure region for the resource group and all child resources.')
param location string = deployment().location

@description('Name of the Azure Container Registry.')
param acrName string

@description('Name of the Container Apps environment.')
param containerAppEnvironmentName string

@description('Name of the Azure Container App.')
param containerAppName string

@description('Name of the Log Analytics workspace.')
param logAnalyticsWorkspaceName string

@description('Name of the Application Insights resource.')
param appInsightsName string

@description('Name of the PostgreSQL Flexible Server.')
param postgresServerName string = 'vc260524pgserver'

@description('Name of the PostgreSQL database to create.')
param postgresDatabaseName string = 'vc260524db'

@description('PostgreSQL admin username.')
param postgresAdminUsername string = 'pgadmin'

@secure()
@description('PostgreSQL admin password.')
param postgresAdminPassword string

@description('Container image repository in ACR.')
param containerImageRepository string = 'hackathon-starter'

@description('Container image tag.')
param containerImageTag string = 'latest'

@description('Azure OpenAI endpoint.')
param azureOpenAiEndpoint string

@secure()
@description('Azure OpenAI API key.')
param azureOpenAiApiKey string

@description('Azure OpenAI deployment name.')
param azureOpenAiDeploymentName string

@description('Azure OpenAI API version.')
param azureOpenAiApiVersion string = '2024-02-15-preview'

@description('Allowed CORS origins.')
param corsOrigins string = '*'

@description('Application environment value.')
param environment string = 'production'

@description('Minimum replicas for the Container App.')
param minReplicas int = 0

@description('Maximum replicas for the Container App.')
param maxReplicas int = 3

@description('Port exposed by the FastAPI container.')
param containerPort int = 8000

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: {
    scenario: 'rg-azure-hackathon'
    workload: 'ai'
    application: 'zava-ai-portal'
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acrDeployment'
  scope: resourceGroup
  params: {
    acrName: acrName
    location: location
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoringDeployment'
  scope: resourceGroup
  params: {
    location: location
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
    appInsightsName: appInsightsName
  }
}

module database 'modules/database.bicep' = {
  name: 'databaseDeployment'
  scope: resourceGroup
  params: {
    location: location
    postgresServerName: postgresServerName
    postgresDatabaseName: postgresDatabaseName
    postgresAdminUsername: postgresAdminUsername
    postgresAdminPassword: postgresAdminPassword
  }
}

var databaseUrl = 'postgresql+asyncpg://${postgresAdminUsername}:${postgresAdminPassword}@${database.outputs.postgresServerFqdn}:5432/${database.outputs.postgresDatabaseName}'
var containerImage = '${acr.outputs.acrLoginServer}/${containerImageRepository}:${containerImageTag}'

module containerApp 'modules/containerapp.bicep' = {
  name: 'containerAppDeployment'
  scope: resourceGroup
  params: {
    location: location
    containerAppName: containerAppName
    containerAppEnvironmentName: containerAppEnvironmentName
    containerImage: containerImage
    containerPort: containerPort
    minReplicas: minReplicas
    maxReplicas: maxReplicas
    acrLoginServer: acr.outputs.acrLoginServer
    acrAdminUsername: acr.outputs.acrAdminUsername
    acrAdminPassword: acr.outputs.acrAdminPassword
    databaseUrl: databaseUrl
    azureOpenAiEndpoint: azureOpenAiEndpoint
    azureOpenAiApiKey: azureOpenAiApiKey
    azureOpenAiDeploymentName: azureOpenAiDeploymentName
    azureOpenAiApiVersion: azureOpenAiApiVersion
    corsOrigins: corsOrigins
    environment: environment
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    logAnalyticsWorkspaceCustomerId: monitoring.outputs.logAnalyticsWorkspaceCustomerId
    logAnalyticsWorkspaceSharedKey: monitoring.outputs.logAnalyticsWorkspaceSharedKey
  }
}

output resourceGroupName string = resourceGroup.name
output containerAppName string = containerApp.outputs.containerAppName
output containerAppFqdn string = containerApp.outputs.containerAppFqdn
output acrLoginServer string = acr.outputs.acrLoginServer
output postgresServerFqdn string = database.outputs.postgresServerFqdn
