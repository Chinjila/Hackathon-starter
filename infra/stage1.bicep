targetScope = 'subscription'

@description('Name of the resource group to create.')
param resourceGroupName string = 'rg-azure-hackathon'

@description('Azure region for all resources.')
param location string = 'canadacentral'

@description('Name of the Azure Container Registry.')
param acrName string

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
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
  scope: rg
  params: {
    acrName: acrName
    location: location
  }
}

output acrLoginServer string = acr.outputs.acrLoginServer
