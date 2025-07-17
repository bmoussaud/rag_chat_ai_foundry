// Main Bicep file for RAG CHAT AI Foundry deployment
// Deploys ACA for hosting, AI Foundry model, and Chainlit frontend

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@description('Location for the resources.')
param location string = resourceGroup().location

@description('Location for AI Foundry resources.')
param aiFoundryLocation string = 'swedencentral' //'westus' 'switzerlandnorth' 'swedencentral'

@description('Name of the managed identity.')
param managedIdentityName string = 'rag-chat-identity'

@description('Name of the resource group to deploy to.')
param rootname string = 'universalragchat'

@description('Indicates if the latest image exists in the ACR.')
param isLatestImageExist bool = false

var tags = {
  // Tag all resources with the environment name.
  'azd-env-name': environmentName
}

#disable-next-line no-unused-vars
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

module applicationInsights 'modules/app-insights.bicep' = {
  name: 'application-insights'
  params: {
    location: location
    workspaceName: logAnalyticsWorkspace.outputs.name
    applicationInsightsName: '${rootname}-app-insights'
  }
}

module logAnalyticsWorkspace 'modules/log-analytics-workspace.bicep' = {
  name: 'log-analytics-workspace'
  params: {
    location: location
    logAnalyticsName: '${rootname}-log-analytics'
  }
}

resource applicationIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
}

resource containerApplicationIdentityAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, applicationIdentity.id, 'ACR Pull Role RG')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: applicationIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Module: Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: '${rootname}${uniqueString(resourceToken)}'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
  }
  tags: tags
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' = {
  name: rootname
  location: location
  tags: tags
  properties: {
    appInsightsConfiguration: {
      connectionString: applicationInsights.outputs.connectionString
    }
    openTelemetryConfiguration: {
      tracesConfiguration: {
        destinations: ['appInsights']
      }
      logsConfiguration: {
        destinations: ['appInsights']
      }
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.outputs.customerId
        sharedKey: logAnalyticsWorkspace.outputs.primarySharedKey
      }
    }
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${applicationIdentity.id}': {}
    }
  }
  dependsOn: [
    containerApplicationIdentityAcrPull
  ]
}

module chatApp 'modules/container-app.bicep' = {
  name: 'chat-app'
  params: {
    name: 'chat-app'
    location: location
    managedEnvironmentId: containerAppsEnv.id
    acrLoginServer: acr.properties.loginServer
    identityId: applicationIdentity.id
    isLatestImageExist: isLatestImageExist
    secrets: []
    envVars: [
      {
        name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
        value: applicationInsights.outputs.connectionString
      }
    ]
  }
}

// Module: AI Foundry Model (placeholder, update with real resource type)
module aiFoundryModel 'modules/ai-foundry.bicep' = {
  name: 'aiFoundryModel'
  params: {
    rootname: rootname
    aiFoundryLocation: aiFoundryLocation
    environmentName: environmentName
    managedIdentityName: managedIdentityName
    applicationInsightsCS: applicationInsights.outputs.connectionString
    applicationInsightsId: applicationInsights.outputs.aiId
  }
}
