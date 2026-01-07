
 Authentication Mechanism                                                                                                         
                                                                                                                                   
  Base URL: https://{ip_address}:9440/api/nutanix/v3                                                                               
                                                                                                                                   
  Authentication Types Supported:                                                                                                  
                                                                                                                                   
  1. Basic Authentication: Send username and password with every request in the Authorization header                               
  2. Session Authentication: Credentials are stored in cookies after the first request                                             
                                                                                                                                   
  How to Authenticate                                                                                                              
                                                                                                                                   
  You authenticate by including a Basic Authentication header with any API request:                                                
                                                                                                                                   
  Authorization: Basic <base64_encoded_credentials>                                                                                
                                                                                                                                   
  Where <base64_encoded_credentials> is base64(username:password)                                                                  
                                                                                                                                   
  Example Authentication Flow                                                                                                      
                                                                                                                                   
  Python Example (from the spec):                                                                                                  
  import requests                                                                                                                  
  from base64 import b64encode                                                                                                     
                                                                                                                                   
  username = 'admin'                                                                                                               
  password = 'password'                                                                                                            
  base_url = 'https://10.0.0.1:9440/api/nutanix/v3'                                                                                
                                                                                                                                   
  # Encode credentials                                                                                                             
  encoded_credentials = b64encode(bytes(f'{username}:{password}', encoding='ascii')).decode('ascii')                               
  auth_header = f'Basic {encoded_credentials}'                                                                                     
                                                                                                                                   
  # Make any API request with auth header                                                                                          
  headers = {                                                                                                                      
      'Accept': 'application/json',                                                                                                
      'Content-Type': 'application/json',                                                                                          
      'Authorization': auth_header                                                                                                 
  }                                                                                                                                
                                                                                                                                   
  # Example: List VMs                                                                                                              
  response = requests.post(                                                                                                        
      f'{base_url}/vms/list',                                                                                                      
      json={"kind": "vm"},                                                                                                         
      headers=headers,                                                                                                             
      verify=False                                                                                                                 
  )                                                                                                                                
                                                                                                                                   
  Cookie-Based Session (Recommended)                                                                                               
                                                                                                                                   
  To reduce authentication overhead, make your first request with Basic Auth, then cache the returned cookies for subsequent requests:
                                                                                                                                   
  For Prism Central with IAMv2 enabled:                                                                                            
  - NTNX_MERCURY_IAM_SESSION                                                                                                       
  - NTNX_IAM_SESSION                                                                                                               
  - NTNX_MERCURY_IAM_REFRESH_TOKEN                                                                                                 
                                                                                                                                   
  For Prism Central with IAMv2 disabled or Prism Element:                                                                          
  - NTNX_IGW_SESSION                                                                                                               
  - NTNX_MERCURY_IGW_SESSION                                                                                                       
  - JSESSIONID (if present)                                                                                                        
                                                                                                                                   
  Upon cookie expiration, send Basic Auth credentials again to obtain new cookies.      


› explain how the plugin worked - how it get the authentication details and connect to AWS / GCP etc.   and where are the
  credentials stored.    after collecting the data, where the data passed to,   what is the standard format and structures of the
  data collected.   so if another cloud provider is to be added to the system, then which structure/functions should be modified,
  and what functions added.   who is the caller or this pplugin.

• The plugin uses secret_data containing an API key and endpoint from SpaceONE's DB to access identity services and fetch inventory
  and monitoring endpoints via connectors using gRPC. It collects metrics through these services, aggregates them into ResourceInfo
  objects, and yields them back via the plugin gRPC interface. Provider additions require extending the manager list, implementing
  new resource and metric schemas, and adapting inventory filtering. The data format centers on CloudServiceResponse with nested
  monitoring metrics per resource.

• The plugin doesn't connect directly to AWS/GCP but uses SpaceONE microservices authenticated via service account tokens, with
  secrets like API keys stored centrally. The collector aggregates data using these tokens passed as gRPC metadata and retrieves
  data sources filtered by monitoring type from the monitoring manager, highlighting reliance on intermediary services rather than
  direct provider connections.

• The collector plugin runs within SpaceONE's inventory service plugin system, using gRPC streaming via its Collector service
  interface. Authentication relies on secret_data carrying SpaceONE service account credentials (api_key, api_key_id, endpoint)
  decoded via JWT tokens. The plugin fetches provider credentials indirectly through monitoring service data sources, not directly
  storing AWS/GCP creds. Data collection delegates to provider-specific manager classes that gather inventory and metric data via
  monitoring and inventory managers, outputting standardized resource responses streamed back via the plugin runner to update the
  inventory DB. Adding a new provider entails creating a new manager subclass with metric schemas, updating the execute_managers
  list and relevant filters in inventory/monitoring.

• Authentication & endpoints

  - CollectorService.list_resources (src/spaceone/inventory/service/collector_service.py) expects secret_data with api_key,
    api_key_id, and identity endpoint. @authentication_handler injects the token into the transaction; the domain id is extracted
    from the JWT in _extract_domain_id.
  - No cloud creds are stored in the plugin repo. The only secrets it reads are the SpaceONE service-account key/endpoint passed in
    secret_data at runtime (SpaceONE stores these service-account secrets).
  - Using the token, IdentityManager.get_endpoints (src/spaceone/inventory/manager/identity_manager.py) calls the Identity service
    to fetch the Inventory and Monitoring gRPC endpoints. Connectors send the token via transaction.get_connection_meta() on each
    call.

  Where provider credentials live

  - Actual AWS/GCP/Azure credentials are expected to be registered as Monitoring “data sources” inside SpaceONE.
    MonitoringManager.get_data_source (src/spaceone/inventory/manager/monitoring_manager.py) lists data sources of monitoring_type
    == METRIC; those data-source records (in the Monitoring service) contain the cloud credentials. The plugin itself never persists
    or reads cloud keys directly.

  Data collection flow

  - CollectorService.list_resources loops over execute_managers (currently only AWSManager) and calls collect_resources(...).
  - CollectorManager.collect_resources (src/spaceone/inventory/manager/collector/manager.py):
      - Updates endpoints for Inventory/Monitoring via Identity.
      - Gets monitoring data_source_ids for the provider.
      - For each data source, delegates to _collect_metric_data_per_provider (provider-specific).
  - AWSManager._collect_metric_data_per_provider (src/spaceone/inventory/manager/collector/aws_manager.py):
      - Lists EC2 servers from Inventory (InventoryManager.list_servers) filtered by provider.
      - Groups by account, batches server ids (_list_resource_ids), then for each metric in METRIC_SCHEMA it calls
        MonitoringManager.get_metric_data with stat AVERAGE and MAX, start/end window derived from supported_period (days) and the
        current UTC time.
      - _append_to_servers merges the returned values into server_vo['data']['monitoring'] using dotted keys (cpu.utilization,
        disk.write_iops, etc.).
      - Builds ServerAwsInstanceResponse objects and yields them.
  - The gRPC API layer Collector.collect (src/spaceone/inventory/api/plugin/collector.py) streams these resources back as
    ResourceInfo messages.

  Output shape / standard format

  - Each streamed item is a ResourceInfo proto with fields: state, message, resource_type, match_rules, resource, options.
  - For servers, resource is a CloudServiceResource (see src/spaceone/inventory/model/server.py). Key payload pieces:
      - resource_type: inventory.Server
      - match_rules: { '1': ['reference.resource_id'] }
      - resource.data.monitoring holds nested metrics: e.g. data.monitoring.cpu.utilization.avg/max, disk.write_throughput.avg/max,
        network.sent_pps.avg/max, etc., with values already aggregated (avg/max) over the requested period.
      - Cloud-service metadata (provider, group/type, layouts) is attached for UI/rendering.

  Adding another cloud provider

  - Create a new manager subclass of CollectorManager (e.g., GCPManager, AzureManager) with its own METRIC_SCHEMA, default_metrics,
    and _collect_metric_data_per_provider implementation that:
      - Determines which resources to pull (InventoryManager.list_servers or .list_cloud_services with provider-specific filters).
      - Batches resource ids and calls MonitoringManager.get_metric_data for each metric/stat combination.
      - Maps results into provider-specific CloudServiceResource/Response models (add new classes in src/spaceone/inventory/model/
        server.py or a new model module if layout differs).
  - Register the manager in CollectorService.execute_managers (src/spaceone/inventory/service/collector_service.py) and, if needed,
    extend provider filters in InventoryManager for that provider’s cloud_service groups/types.
  - If the output structure differs, add corresponding response classes and layout metadata.

  Who calls the plugin

  - The gRPC service Collector (src/spaceone/inventory/api/plugin/collector.py) implements the SpaceONE plugin interface (init,
    verify, collect). It is invoked by the SpaceONE plugin runner / Inventory service when metric collection is triggered. The
    caller supplies secret_data (SpaceONE service account) and options (metric selection, period, endpoint type), and consumes the
    streamed ResourceInfo responses to update Inventory.
