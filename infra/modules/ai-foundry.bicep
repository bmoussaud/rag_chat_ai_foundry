// Module: AI Foundry Model (placeholder)
param environmentName string
param rootname string
param aiFoundryLocation string
param managedIdentityName string
param applicationInsightsId string
param applicationInsightsCS string

@description('Model deployments for OpenAI')
param modelDeploymentsParameters array = [
  {
    name: '${rootname}-gpt-4.1-mini'
    model: 'gpt-4.1-mini'
    capacity: 1000
    deployment: 'GlobalStandard'
    version: '2025-04-14'
    format: 'OpenAI'
  }
  /*
  {
    name: '${rootname}-gpt-4.1-nano'
    model: 'gpt-4.1-nano'
    capacity: 1
    deployment: 'GlobalStandard'
    version: '2025-04-14'
    format: 'OpenAI'
  }

  {
    name: '${rootname}-phi-4'
    model: 'Phi-4'
    version: '7'
    format: 'Microsoft'
    capacity: 1
    deployment: 'GlobalStandard'
    settings: {
      enableAutoToolChoice: true
      toolCallParser: 'default'
    }
  }*/
]

resource applicationIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managedIdentityName
}

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: '${rootname}-ai-foundry-${aiFoundryLocation}'
  location: aiFoundryLocation
  tags: {
    'azd-service-name': 'ai-foundry'
    'azd-env-name': environmentName
  }
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    // required to work in AI Foundry
    allowProjectManagement: true
    // Defines developer API endpoint subdomain
    customSubDomainName: '${rootname}-ai-foundry-${aiFoundryLocation}'
    publicNetworkAccess: 'Enabled'

    //disableLocalAuth: true
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiFoundry
  name: '${rootname}-project-${aiFoundryLocation}'
  location: aiFoundryLocation
  properties: {
    description: 'an universal chat agent project'
    displayName: rootname
  }
  identity: {
    type: 'SystemAssigned'
  }
}

resource aiFoundryRoleAssignmentOnApplicationIdentity 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(aiFoundry.id, applicationIdentity.id, 'AI Foundry Azure AI User role')
  scope: aiFoundry
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
    )
    //Principal ID of the current user
    principalId: applicationIdentity.properties.principalId
  }
}

//https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-azure-ai-foundry?pivots=fdp-project#azure-ai-account-owner
resource aiFoundryProjectRoleAssignmentOnApplicationIdentity 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(project.id, applicationIdentity.id, 'AI Foundry Project Azure AI User role')
  scope: project
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User
    )
    //Principal ID of the current user
    principalId: applicationIdentity.properties.principalId
  }
}

@batchSize(1)
resource modelDeployments 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [
  for deployment in modelDeploymentsParameters: {
    parent: aiFoundry
    name: deployment.name
    sku: {
      capacity: deployment.capacity
      name: deployment.deployment
    }
    properties: {
      model: {
        format: deployment.format
        name: deployment.model
        version: deployment.version
      }
    }
  }
]

// Creates the Azure Foundry connection to your Azure App Insights resource
resource connectionAppInsight 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  name: '${aiFoundry.name}-appinsights-connection'
  parent: aiFoundry
  properties: {
    category: 'AppInsights'
    target: applicationInsightsId
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: applicationInsightsCS
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: applicationInsightsId
    }
  }
}

output aiFoundryId string = aiFoundry.id
output projectEndpoint string = project.properties.endpoints['AI Foundry API']
output modelDeploymentsName string = modelDeploymentsParameters[0].name
