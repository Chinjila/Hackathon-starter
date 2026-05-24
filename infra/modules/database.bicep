targetScope = 'resourceGroup'

@description('Azure region for the PostgreSQL server.')
param location string = resourceGroup().location

@description('Name of the PostgreSQL Flexible Server.')
param postgresServerName string

@description('Name of the PostgreSQL database to create.')
param postgresDatabaseName string = 'zava'

@description('PostgreSQL administrator username.')
param postgresAdminUsername string

@secure()
@description('PostgreSQL administrator password.')
param postgresAdminPassword string

@description('PostgreSQL major version.')
param postgresVersion string = '15'

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: postgresServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: postgresVersion
    administratorLogin: postgresAdminUsername
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

resource allowAllFirewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: postgresServer
  name: 'AllowAllPublicAccess'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '255.255.255.255'
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgresServer
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.UTF8'
  }
}

output postgresServerName string = postgresServer.name
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
output postgresDatabaseName string = postgresDatabase.name
output postgresAdminUsername string = postgresAdminUsername