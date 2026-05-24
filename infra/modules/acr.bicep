targetScope = 'resourceGroup'

@description('Name of the Azure Container Registry.')
param acrName string

@description('Azure region for the registry.')
param location string = resourceGroup().location

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

var credentials = listCredentials(acr.id, '2023-07-01')

output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
output acrAdminUsername string = credentials.username
@secure()
output acrAdminPassword string = credentials.passwords[0].value
