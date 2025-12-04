from azure.ai.ml import MLClient
from azure.ai.ml.entities import ManagedOnlineEndpoint
from azure.identity import DefaultAzureCredential

# ============ UPDATE THESE VALUES ============
SUBSCRIPTION_ID = "1a522cdf-c3bd-41da-bc8e-21aa5eb69527"
RESOURCE_GROUP = "opportunityscout"
WORKSPACE_NAME = "amlstudioadditional"
ENDPOINT_NAME = "proposal-architect-endpoint"  # Choose your endpoint name
# =============================================

# Connect to Azure ML Workspace
credential = DefaultAzureCredential()
ml_client = MLClient(
    credential=credential,
    subscription_id=SUBSCRIPTION_ID,
    resource_group_name=RESOURCE_GROUP,
    workspace_name=WORKSPACE_NAME
)

# Create the endpoint
endpoint = ManagedOnlineEndpoint(
    name=ENDPOINT_NAME,
    description="My custom endpoint without a model",
    auth_mode="key"  # or "aml_token" for token-based auth
)

# Create or update the endpoint
print(f"Creating endpoint: {ENDPOINT_NAME}...")
ml_client.online_endpoints.begin_create_or_update(endpoint).result()
print(f"Endpoint '{ENDPOINT_NAME}' created successfully!")

# Get endpoint details
endpoint = ml_client.online_endpoints.get(name=ENDPOINT_NAME)
print(f"Endpoint URI: {endpoint.scoring_uri}")
print(f"Endpoint State: {endpoint.provisioning_state}")