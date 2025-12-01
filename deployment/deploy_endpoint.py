"""
Script to deploy the Opportunity Scout backend to Azure ML.

Run this script from your local machine with Azure CLI logged in.
"""

import os
import argparse
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    ManagedOnlineEndpoint,
    ManagedOnlineDeployment,
    Environment,
    CodeConfiguration
)
from azure.identity import DefaultAzureCredential

def deploy_endpoint(
    subscription_id: str,
    resource_group: str,
    workspace_name: str,
    endpoint_name: str = "opportunity-scout-endpoint"
):
    """
    Deploy the Opportunity Scout backend to Azure ML.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group: Resource group name
        workspace_name: Azure ML workspace name
        endpoint_name: Name for the endpoint
    """
    print("Connecting to Azure ML workspace...")
    
    # Get ML client
    credential = DefaultAzureCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name
    )
    
    print(f"Connected to workspace: {workspace_name}")
    
    # Create endpoint
    print(f"Creating endpoint: {endpoint_name}")
    endpoint = ManagedOnlineEndpoint(
        name=endpoint_name,
        description="Opportunity Scout - Speaking opportunity finder",
        auth_mode="key"
    )
    
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("Endpoint created!")
    
    # Create environment
    print("Creating environment...")
    env = Environment(
        name="opportunity-scout-env",
        description="Environment for Opportunity Scout",
        conda_file="environment.yml",
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest"
    )
    
    # Create deployment
    print("Creating deployment...")
    deployment = ManagedOnlineDeployment(
        name="default",
        endpoint_name=endpoint_name,
        model=None,  # No model file, using external APIs
        environment=env,
        code_configuration=CodeConfiguration(
            code="../backend",
            scoring_script="score.py"
        ),
        instance_type="Standard_DS2_v2",
        instance_count=1,
        environment_variables={
            "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
            "BING_SEARCH_API_KEY": os.getenv("BING_SEARCH_API_KEY")
        }
    )
    
    ml_client.online_deployments.begin_create_or_update(deployment).result()
    print("Deployment created!")
    
    # Set traffic to 100%
    endpoint.traffic = {"default": 100}
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    
    # Get endpoint details
    endpoint = ml_client.online_endpoints.get(endpoint_name)
    print(f"\n✅ Deployment complete!")
    print(f"Endpoint URL: {endpoint.scoring_uri}")
    print(f"Get API key with: az ml online-endpoint get-credentials --name {endpoint_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Opportunity Scout to Azure ML")
    parser.add_argument("--subscription-id", required=True, help="Azure subscription ID")
    parser.add_argument("--resource-group", required=True, help="Resource group name")
    parser.add_argument("--workspace-name", required=True, help="Azure ML workspace name")
    parser.add_argument("--endpoint-name", default="opportunity-scout-endpoint", 
                        help="Endpoint name")
    
    args = parser.parse_args()
    
    deploy_endpoint(
        subscription_id=args.subscription_id,
        resource_group=args.resource_group,
        workspace_name=args.workspace_name,
        endpoint_name=args.endpoint_name
    )