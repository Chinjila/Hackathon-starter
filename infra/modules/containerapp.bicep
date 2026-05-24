targetScope = 'resourceGroup'

@description('Azure region for the Container Apps environment and app.')
param location string = resourceGroup().location

@description('Name of the Container App.')
param containerAppName string

@description('Name of the Container Apps environment.')
param containerAppEnvironmentName string

@description('Fully qualified container image reference in ACR.')
param containerImage string

@description('Exposed container port.')
param containerPort int = 8000

@description('Minimum replica count.')
param minReplicas int = 0

@description('Maximum replica count.')
param maxReplicas int = 3

@description('ACR login server hostname (e.g. myacr.azurecr.io).')
param acrLoginServer string

@description('Name of the Azure Container Registry (used for AcrPull role assignment).')
param acrName string

@secure()
@description('Database connection string for the FastAPI app.')
param databaseUrl string

@description('Azure OpenAI endpoint.')
param azureOpenAiEndpoint string

@secure()
@description('Azure OpenAI API key.')
param azureOpenAiApiKey string

@description('Azure OpenAI deployment name.')
param azureOpenAiDeploymentName string

@description('Allowed CORS origins.')
param corsOrigins string = '*'

@description('Application environment value.')
param environment string = 'production'

@description('Application Insights connection string.')
param applicationInsightsConnectionString string

@description('Log Analytics workspace customer ID.')
param logAnalyticsWorkspaceCustomerId string

@secure()
@description('Log Analytics workspace shared key.')
param logAnalyticsWorkspaceSharedKey string

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspaceCustomerId
        sharedKey: logAnalyticsWorkspaceSharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: containerPort
        allowInsecure: false
        transport: 'auto'
      }
      registries: [
        {
          server: acrLoginServer
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'database-url'
          value: databaseUrl
        }
        {
          name: 'azure-openai-api-key'
          value: azureOpenAiApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          image: containerImage
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-openai-api-key'
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT_NAME'
              value: azureOpenAiDeploymentName
            }
            {
              name: 'CORS_ORIGINS'
              value: corsOrigins
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: applicationInsightsConnectionString
            }
          ]
          resources: {
            cpu: 1
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

// Grant the Container App's system-assigned managed identity AcrPull on the registry.
// This replaces the previous admin-credential approach.
resource existingAcr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

var acrPullRoleDefinitionId = '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull built-in role

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(existingAcr.id, containerApp.id, acrPullRoleDefinitionId)
  scope: existingAcr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output containerAppName string = containerApp.name
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
