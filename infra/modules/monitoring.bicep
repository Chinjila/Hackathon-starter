targetScope = 'resourceGroup'

@description('Azure region for monitoring resources.')
param location string = resourceGroup().location

@description('Name of the Log Analytics workspace.')
param logAnalyticsWorkspaceName string

@description('Name of the Application Insights resource.')
param appInsightsName string

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  sku: {
    name: 'PerGB2018'
  }
  properties: {
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

var logAnalyticsSharedKey = listKeys(logAnalyticsWorkspace.id, '2020-08-01').primarySharedKey

output logAnalyticsWorkspaceResourceId string = logAnalyticsWorkspace.id
output logAnalyticsWorkspaceCustomerId string = logAnalyticsWorkspace.properties.customerId
output logAnalyticsWorkspaceSharedKey string = logAnalyticsSharedKey
output applicationInsightsConnectionString string = appInsights.properties.ConnectionString