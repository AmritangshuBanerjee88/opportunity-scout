"""
Deploy only the deployment to existing Backend B endpoint.
"""

import os
import sys
from pathlib import Path

try:
    from azure.ai.ml import MLClient
    from azure.ai.ml.entities import (
        ManagedOnlineDeployment,
        Environment,
        CodeConfiguration,
        OnlineRequestSettings
    )
    from azure.identity import DefaultAzureCredential
except ImportError:
    print("Required packages not installed.")
    sys.exit(1)

SUBSCRIPTION_ID = "48fe2677-a5b2-4de4-bcee-caa5c6f8ca8b"
RESOURCE_GROUP = "rg-infrastructure-agent"
WORKSPACE_NAME = "aml-infrastructure-agent"
ENDPOINT_NAME = "proposal-architect-endpoint"


def main():
    print("Checking environment variables...")
    
    env_vars = {}
    for var in ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_API_KEY"]:
        value = os.getenv(var)
        if not value:
            print(f"Missing: {var}")
            sys.exit(1)
        env_vars[var] = value
        print(f"  ✅ {var}: {value[:8]}...")
    
    print("\nConnecting to Azure ML...")
    credential = DefaultAzureCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP,
        workspace_name=WORKSPACE_NAME
    )
    print("✅ Connected!")
    
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent / "backend_b"
    environment_file = script_dir / "environment_b.yml"
    
    print(f"\nBackend directory: {backend_dir}")
    
    print("\nCreating environment...")
    env = Environment(
        name="proposal-architect-env-v2",
        description="Environment for Proposal Architect",
        conda_file=str(environment_file),
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest"
    )
    
    print("\nCreating deployment (10-20 minutes)...")
    print("☕ Grab a coffee!\n")
    
    deployment = ManagedOnlineDeployment(
        name="default",
        endpoint_name=ENDPOINT_NAME,
        environment=env,
        code_configuration=CodeConfiguration(
            code=str(backend_dir),
            scoring_script="score.py"
        ),
        instance_type="Standard_DS3_v2",
        instance_count=1,
        environment_variables=env_vars,
        request_settings=OnlineRequestSettings(
            request_timeout_ms=180000,
            max_concurrent_requests_per_instance=5
        )
    )
    
    try:
        poller = ml_client.online_deployments.begin_create_or_update(deployment)
        print("⏳ Deployment in progress...")
        poller.result()
        print("✅ Deployment created!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    print("\nSetting traffic to 100%...")
    endpoint = ml_client.online_endpoints.get(ENDPOINT_NAME)
    endpoint.traffic = {"default": 100}
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("✅ Traffic configured!")
    
    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT COMPLETE!")
    print("=" * 60)
    
    endpoint = ml_client.online_endpoints.get(ENDPOINT_NAME)
    keys = ml_client.online_endpoints.get_keys(ENDPOINT_NAME)
    
    print(f"\n📌 Endpoint URL:\n   {endpoint.scoring_uri}")
    print(f"\n🔑 API Key:\n   {keys.primary_key}")
    print("\n📝 SAVE THESE FOR STREAMLIT!")
    print("=" * 60)


if __name__ == "__main__":
    main()
