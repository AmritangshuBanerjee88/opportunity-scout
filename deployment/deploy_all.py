"""
Universal Deployment Script for Opportunity Scout & Proposal Architect

This script deploys both backends to ANY Azure ML workspace.
Just provide your Azure configuration and credentials.

Usage:
  python3 deploy_all.py --interactive     # Guided setup (recommended)
  python3 deploy_all.py --config myenv    # Use saved config file
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    from azure.ai.ml import MLClient
    from azure.ai.ml.entities import (
        ManagedOnlineEndpoint,
        ManagedOnlineDeployment,
        Environment,
        CodeConfiguration,
        OnlineRequestSettings
    )
    from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
except ImportError:
    print("❌ Required packages not installed.")
    print("Run: pip install azure-ai-ml azure-identity")
    sys.exit(1)


class DeploymentConfig:
    """Configuration for deployment."""
    
    def __init__(self):
        # Azure ML
        self.subscription_id = ""
        self.resource_group = ""
        self.workspace_name = ""
        
        # Endpoint names
        self.endpoint_a_name = "opportunity-scout-endpoint"
        self.endpoint_b_name = "proposal-architect-endpoint"
        
        # Environment variables for endpoints
        self.azure_openai_endpoint = ""
        self.azure_openai_api_key = ""
        self.azure_search_endpoint = ""
        self.azure_search_api_key = ""
        self.serper_api_key = ""
    
    def save(self, filename: str):
        """Save config to file (without secrets)."""
        config = {
            "subscription_id": self.subscription_id,
            "resource_group": self.resource_group,
            "workspace_name": self.workspace_name,
            "endpoint_a_name": self.endpoint_a_name,
            "endpoint_b_name": self.endpoint_b_name,
            "azure_openai_endpoint": self.azure_openai_endpoint,
            "azure_search_endpoint": self.azure_search_endpoint,
            # Note: We don't save API keys to file for security
        }
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Config saved to {filename}")
        print("⚠️ API keys are NOT saved. Set them as environment variables.")
    
    def load(self, filename: str):
        """Load config from file."""
        with open(filename, 'r') as f:
            config = json.load(f)
        
        self.subscription_id = config.get("subscription_id", "")
        self.resource_group = config.get("resource_group", "")
        self.workspace_name = config.get("workspace_name", "")
        self.endpoint_a_name = config.get("endpoint_a_name", "opportunity-scout-endpoint")
        self.endpoint_b_name = config.get("endpoint_b_name", "proposal-architect-endpoint")
        self.azure_openai_endpoint = config.get("azure_openai_endpoint", "")
        self.azure_search_endpoint = config.get("azure_search_endpoint", "")
        
        # Load API keys from environment
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY", "")
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")
    
    def validate(self) -> bool:
        """Validate all required fields are set."""
        missing = []
        
        if not self.subscription_id:
            missing.append("subscription_id")
        if not self.resource_group:
            missing.append("resource_group")
        if not self.workspace_name:
            missing.append("workspace_name")
        if not self.azure_openai_endpoint:
            missing.append("azure_openai_endpoint")
        if not self.azure_openai_api_key:
            missing.append("azure_openai_api_key")
        if not self.azure_search_endpoint:
            missing.append("azure_search_endpoint")
        if not self.azure_search_api_key:
            missing.append("azure_search_api_key")
        if not self.serper_api_key:
            missing.append("serper_api_key")
        
        if missing:
            print(f"❌ Missing required fields: {', '.join(missing)}")
            return False
        
        return True


def interactive_setup() -> DeploymentConfig:
    """Interactively gather configuration."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     OPPORTUNITY SCOUT & PROPOSAL ARCHITECT                   ║
║            Interactive Deployment Setup                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    config = DeploymentConfig()
    
    print("📋 Step 1: Azure ML Workspace Configuration")
    print("-" * 50)
    config.subscription_id = input("  Azure Subscription ID: ").strip()
    config.resource_group = input("  Resource Group Name: ").strip()
    config.workspace_name = input("  Azure ML Workspace Name: ").strip()
    
    print("\n📋 Step 2: Endpoint Names (press Enter for defaults)")
    print("-" * 50)
    name_a = input(f"  Backend A endpoint name [{config.endpoint_a_name}]: ").strip()
    if name_a:
        config.endpoint_a_name = name_a
    
    name_b = input(f"  Backend B endpoint name [{config.endpoint_b_name}]: ").strip()
    if name_b:
        config.endpoint_b_name = name_b
    
    print("\n📋 Step 3: Azure OpenAI Configuration")
    print("-" * 50)
    config.azure_openai_endpoint = input("  Azure OpenAI Endpoint URL: ").strip()
    config.azure_openai_api_key = input("  Azure OpenAI API Key: ").strip()
    
    print("\n📋 Step 4: Azure AI Search Configuration")
    print("-" * 50)
    config.azure_search_endpoint = input("  Azure AI Search Endpoint URL: ").strip()
    config.azure_search_api_key = input("  Azure AI Search Admin Key: ").strip()
    
    print("\n📋 Step 5: Serper.dev Configuration")
    print("-" * 50)
    config.serper_api_key = input("  Serper API Key: ").strip()
    
    # Ask to save config
    print("\n" + "-" * 50)
    save_config = input("💾 Save configuration for future use? (y/n): ").strip().lower()
    if save_config == 'y':
        config_name = input("  Config name (e.g., 'production', 'dev'): ").strip() or "default"
        config.save(f"config_{config_name}.json")
    
    return config


def get_ml_client(config: DeploymentConfig) -> MLClient:
    """Get authenticated ML client."""
    print("\n🔐 Authenticating with Azure...")
    
    try:
        credential = DefaultAzureCredential()
        ml_client = MLClient(
            credential=credential,
            subscription_id=config.subscription_id,
            resource_group_name=config.resource_group,
            workspace_name=config.workspace_name
        )
        # Test connection
        ml_client.workspaces.get(config.workspace_name)
        print("✅ Authentication successful!")
        return ml_client
    
    except Exception as e:
        print(f"⚠️ Default credential failed: {e}")
        print("🌐 Opening browser for interactive login...")
        
        credential = InteractiveBrowserCredential()
        ml_client = MLClient(
            credential=credential,
            subscription_id=config.subscription_id,
            resource_group_name=config.resource_group,
            workspace_name=config.workspace_name
        )
        print("✅ Authentication successful!")
        return ml_client


def deploy_endpoint(
    ml_client: MLClient,
    endpoint_name: str,
    backend_dir: Path,
    environment_file: Path,
    env_vars: dict,
    description: str
) -> dict:
    """Deploy a single endpoint."""
    
    print(f"\n{'='*60}")
    print(f"🚀 Deploying: {endpoint_name}")
    print(f"{'='*60}")
    
    # Create endpoint
    print("\n1️⃣ Creating endpoint...")
    endpoint = ManagedOnlineEndpoint(
        name=endpoint_name,
        description=description,
        auth_mode="key"
    )
    
    try:
        ml_client.online_endpoints.begin_create_or_update(endpoint).result()
        print("   ✅ Endpoint created!")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   ℹ️ Endpoint already exists, will update deployment...")
        else:
            raise e
    
    # Create environment
    print("\n2️⃣ Creating environment...")
    env = Environment(
        name=f"{endpoint_name}-env",
        description=f"Environment for {endpoint_name}",
        conda_file=str(environment_file),
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest"
    )
    
    # Create deployment
    print("\n3️⃣ Creating deployment (this takes 10-20 minutes)...")
    print("   ☕ Feel free to grab a coffee!\n")
    
    deployment = ManagedOnlineDeployment(
        name="default",
        endpoint_name=endpoint_name,
        environment=env,
        code_configuration=CodeConfiguration(
            code=str(backend_dir),
            scoring_script="score.py"
        ),
        instance_type="Standard_DS2_v2",
        instance_count=1,
        environment_variables=env_vars,
        request_settings=OnlineRequestSettings(
            request_timeout_ms=180000,
            max_concurrent_requests_per_instance=5
        )
    )
    
    try:
        poller = ml_client.online_deployments.begin_create_or_update(deployment)
        print("   ⏳ Deployment in progress...")
        poller.result()
        print("   ✅ Deployment created!")
    except Exception as e:
        print(f"   ❌ Deployment failed: {e}")
        raise e
    
    # Set traffic
    print("\n4️⃣ Setting traffic to 100%...")
    endpoint = ml_client.online_endpoints.get(endpoint_name)
    endpoint.traffic = {"default": 100}
    ml_client.online_endpoints.begin_create_or_update(endpoint).result()
    print("   ✅ Traffic configured!")
    
    # Get credentials
    endpoint = ml_client.online_endpoints.get(endpoint_name)
    keys = ml_client.online_endpoints.get_keys(endpoint_name)
    
    return {
        "endpoint_url": endpoint.scoring_uri,
        "api_key": keys.primary_key
    }


def deploy_all(config: DeploymentConfig):
    """Deploy both backends."""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║              DEPLOYING BOTH BACKENDS                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Validate config
    if not config.validate():
        print("\n❌ Configuration incomplete. Please provide all required values.")
        sys.exit(1)
    
    # Get paths
    script_dir = Path(__file__).parent.absolute()
    repo_dir = script_dir.parent
    
    backend_a_dir = repo_dir / "backend"
    backend_b_dir = repo_dir / "backend_b"
    env_a_file = script_dir / "environment.yml"
    env_b_file = script_dir / "environment_b.yml"
    
    # Verify paths exist
    for path, name in [(backend_a_dir, "backend"), (backend_b_dir, "backend_b"), 
                       (env_a_file, "environment.yml"), (env_b_file, "environment_b.yml")]:
        if not path.exists():
            print(f"❌ Missing: {name} at {path}")
            sys.exit(1)
    
    # Get ML client
    ml_client = get_ml_client(config)
    
    # Environment variables for Backend A
    env_vars_a = {
        "AZURE_OPENAI_ENDPOINT": config.azure_openai_endpoint,
        "AZURE_OPENAI_API_KEY": config.azure_openai_api_key,
        "SERPER_API_KEY": config.serper_api_key
    }
    
    # Environment variables for Backend B
    env_vars_b = {
        "AZURE_OPENAI_ENDPOINT": config.azure_openai_endpoint,
        "AZURE_OPENAI_API_KEY": config.azure_openai_api_key,
        "AZURE_SEARCH_ENDPOINT": config.azure_search_endpoint,
        "AZURE_SEARCH_API_KEY": config.azure_search_api_key
    }
    
    results = {}
    
    # Deploy Backend A
    try:
        result_a = deploy_endpoint(
            ml_client=ml_client,
            endpoint_name=config.endpoint_a_name,
            backend_dir=backend_a_dir,
            environment_file=env_a_file,
            env_vars=env_vars_a,
            description="Opportunity Scout - Speaking opportunity finder"
        )
        results["backend_a"] = result_a
    except Exception as e:
        print(f"\n❌ Backend A deployment failed: {e}")
        results["backend_a"] = {"error": str(e)}
    
    # Deploy Backend B
    try:
        result_b = deploy_endpoint(
            ml_client=ml_client,
            endpoint_name=config.endpoint_b_name,
            backend_dir=backend_b_dir,
            environment_file=env_b_file,
            env_vars=env_vars_b,
            description="Proposal Architect - Profile ranking and proposal generation"
        )
        results["backend_b"] = result_b
    except Exception as e:
        print(f"\n❌ Backend B deployment failed: {e}")
        results["backend_b"] = {"error": str(e)}
    
    # Print summary
    print("\n")
    print("=" * 70)
    print("🎉 DEPLOYMENT COMPLETE!")
    print("=" * 70)
    
    if "error" not in results.get("backend_a", {}):
        print(f"""
📌 BACKEND A - Opportunity Scout:
   Endpoint: {results['backend_a']['endpoint_url']}
   API Key:  {results['backend_a']['api_key']}
        """)
    else:
        print(f"\n❌ Backend A: Failed - {results['backend_a']['error']}")
    
    if "error" not in results.get("backend_b", {}):
        print(f"""
📌 BACKEND B - Proposal Architect:
   Endpoint: {results['backend_b']['endpoint_url']}
   API Key:  {results['backend_b']['api_key']}
        """)
    else:
        print(f"\n❌ Backend B: Failed - {results['backend_b']['error']}")
    
    # Print Streamlit secrets
    if "error" not in results.get("backend_a", {}) and "error" not in results.get("backend_b", {}):
        print("""
╔══════════════════════════════════════════════════════════════╗
║              STREAMLIT SECRETS (Copy this!)                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        print(f'''
# Add these to your Streamlit.io secrets:

APP_PASSWORD = "YourChosenPassword"

AZURE_ML_ENDPOINT_A = "{results['backend_a']['endpoint_url']}"
AZURE_ML_KEY_A = "{results['backend_a']['api_key']}"

AZURE_ML_ENDPOINT_B = "{results['backend_b']['endpoint_url']}"
AZURE_ML_KEY_B = "{results['backend_b']['api_key']}"
        ''')
    
    print("\n" + "=" * 70)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Opportunity Scout & Proposal Architect to Azure ML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 deploy_all.py --interactive          # Guided setup
  python3 deploy_all.py --config production    # Use saved config
  python3 deploy_all.py --env                  # Use environment variables
        """
    )
    
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Interactive guided setup")
    parser.add_argument("--config", "-c", type=str,
                       help="Use saved config file (without .json extension)")
    parser.add_argument("--env", "-e", action="store_true",
                       help="Use environment variables for all config")
    
    args = parser.parse_args()
    
    if args.interactive:
        config = interactive_setup()
    elif args.config:
        config_file = f"config_{args.config}.json"
        if not os.path.exists(config_file):
            print(f"❌ Config file not found: {config_file}")
            sys.exit(1)
        config = DeploymentConfig()
        config.load(config_file)
        
        # Load API keys from environment or prompt
        if not config.azure_openai_api_key:
            config.azure_openai_api_key = input("Azure OpenAI API Key: ").strip()
        if not config.azure_search_api_key:
            config.azure_search_api_key = input("Azure AI Search API Key: ").strip()
        if not config.serper_api_key:
            config.serper_api_key = input("Serper API Key: ").strip()
            
    elif args.env:
        config = DeploymentConfig()
        config.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID", "")
        config.resource_group = os.getenv("AZURE_RESOURCE_GROUP", "")
        config.workspace_name = os.getenv("AZURE_ML_WORKSPACE", "")
        config.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        config.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        config.azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        config.azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY", "")
        config.serper_api_key = os.getenv("SERPER_API_KEY", "")
    else:
        # Default to interactive
        config = interactive_setup()
    
    deploy_all(config)


if __name__ == "__main__":
    main()

