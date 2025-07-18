// AI Search (Cognitive Search) Bicep module for RAG CHAT AI Foundry
// Deploys an Azure Cognitive Search instance with basic configuration

@description('Name of the Azure Cognitive Search service.')
param searchServiceName string

@description('Location for the Azure Cognitive Search service.')
param location string

@description('SKU for the Azure Cognitive Search service.')
@allowed(['basic', 'standard', 'standard2', 'standard3', 'storage_optimized_l1', 'storage_optimized_l2'])
param skuName string = 'basic'

@description('Tags to apply to the resource.')
param tags object = {}

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  sku: {
    name: skuName
  }
  properties: {
    hostingMode: 'default'
    partitionCount: 1
    replicaCount: 1
    publicNetworkAccess: 'enabled'
  }
  tags: tags
}

output searchServiceId string = search.id
output searchServiceName string = search.name
output searchServiceEndpoint string = 'https://${search.name}.search.windows.net'
