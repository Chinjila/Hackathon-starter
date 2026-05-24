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

@description('ACR login server.')
param acrLoginServer string

@description('ACR admin username.')
param acrAdminUsername string

@secure()
@description('ACR admin password.')
param acrAdminPassword string

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

@description('Azure OpenAI API version.')
param azureOpenAiApiVersion string

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
          username: acrAdminUsername
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acrAdminPassword
        }
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
              name: 'AZURE_OPENAI_API_VERSION'
              value: azureOpenAiApiVersion
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
            memory: '0.5Gi'
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

output containerAppName string = containerApp.name
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
