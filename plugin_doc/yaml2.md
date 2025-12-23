

› explain the logic of the source code - explaining what is purpose of metric, manager, and all the different subdirectories in
  plugin directory.


• Explored
  └ List ls
    Search AGENTS.md in ..
    List plugin
    Search rg --files plugin
    Read main.py
    Search rg --files plugin/manager
    Read base.py, instance_count.yaml, namespace.yaml, instance_manager.py, container_manager.py

• I’m going to explain the purpose of metrics, the manager, and the subdirectories involved, likely tying everything back to the
  cloud_service_conf configuration. I want to clarify how these components relate and fit together.

• Explored
  └ Read cloud_service_conf.py, instance.yaml, functions_connector.py, container_instances_connector.py,
virtual_machines_connector.py,
         __init__.py, container.yaml
    Search subscriptions in plugin
    Search *subscriptions* in plugin

• I notice there's no subscriptions manager in this source, though it's referenced and probably comes from another module—I'll
  highlight that for clarity. I'll explain the directory structure under /plugin, covering config, connector, manager, metadata,
  metrics, and main.py, including the init.py. I'll detail the metrics provided for VirtualMachines, ContainerInstances, and
  Functions, focusing on instance_count, vcpu_count, and memory, and their role in AzureBaseManager.collect_metrics. I'll describe
  the manager module architecture: a base manager defining collection flow, extended by service-specific managers that gather
  resources via connectors, plus mention sub-managers like those in virtual_machines for disks and network interfaces, possibly
  glancing at disk_manager for accuracy. This should give a coherent overview the user can follow.

• Explored
  └ Read disk_manager.py, nic_manager.py

• I'm outlining how the SpaceONE collector plugin works, starting from the entrypoint in plugin/main.py that uses
  CollectorPluginServer and handles resource types via managers. I'll describe the roles of various managers in plugin/manager/,
  their reliance on connectors in plugin/connector/, and how metrics and metadata YAML definitions in plugin/metrics/ and plugin/
  metadata/ shape data collection and UI presentation. I'll highlight key files like plugin/manager/virtual_machines/
  instance_manager.py and note that subscription managers are referenced but missing from the repo. This overview will include file
  path mentions and cover the flow for cloud service creation, metric collection, and namespace/metric emission by
  AzureBaseManager.collect_metrics.

• Explored
  └ Read __init__.py

─ Worked for 1m 25s ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

• Here’s a focused walkthrough of how this plugin works and what each directory is for, with pointers to the exact sources.

  Overall flow

  - plugin/main.py is the entrypoint that wires the SpaceONE CollectorPluginServer and routes Collector.init, Collector.verify,
    Collector.collect, and Job.get_tasks. It selects managers based on cloud_service_groups and resource_type, and switches to
    metric/region collection when requested. plugin/main.py
  - AzureBaseManager is the shared orchestration layer: it wraps cloud service types/resources into SpaceONE responses, handles
    error wrapping, and includes metric/region collection helpers. plugin/manager/base.py

  Managers (what “manager” means here)

  - Managers are “resource assemblers.” Each concrete manager defines:
      - create_cloud_service_type() to emit the CloudServiceType definition.
      - create_cloud_service() to fetch Azure resources and normalize them into SpaceONE CloudService records.
      - These are invoked by AzureBaseManager.collect_resources() and AzureBaseManager.collect_cloud_services(). plugin/manager/
        base.py
  - VirtualMachinesManager fetches VM inventory and enriches it by delegating to helper managers for disks, NICs, VNet, NSG, and
    load balancer data. plugin/manager/virtual_machines/instance_manager.py, plugin/manager/virtual_machines/disk_manager.py,
    plugin/manager/virtual_machines/nic_manager.py, plugin/manager/virtual_machines/vnet_manager.py, plugin/manager/
    virtual_machines/network_security_group_manager.py, plugin/manager/virtual_machines/load_balancer_manager.py, plugin/manager/
    virtual_machines/vm_manager.py
  - ContainerInstancesManage collects container group details and computes display fields like CPU/memory/GPU counts and volume
    metadata. plugin/manager/container_instances/container_manager.py
  - FunctionsManager enumerates Function Apps and joins App Service Plan details via REST to compute plan metadata (pricing tier,
    instance count, OS, zone redundancy). plugin/manager/functions/instance_manager.py

  Connectors (Azure API access)

  - AzureBaseConnector sets up Azure SDK clients from secret data and provides a raw REST helper for endpoints not covered by the
    SDK. plugin/connector/base.py
  - Service-specific connectors wrap the SDK clients or REST calls for each service. plugin/connector/virtual_machines/
    virtual_machines_connector.py, plugin/connector/container_instances/container_instances_connector.py, plugin/connector/
    functions/functions_connector.py

  Metrics (what “metric” means here)

  - Metrics are YAML definitions that describe how SpaceONE should compute/aggregate inventory metrics for collected resources.
    They’re not live polling rules; they are metadata describing aggregation (e.g., count by region/type).
  - AzureBaseManager.collect_metrics() reads these YAML files and emits inventory.Namespace and inventory.Metric responses. plugin/
    manager/base.py
  - Examples:
      - VM metrics such as instance count, vCPU count, memory size under VirtualMachines/Instance. plugin/metrics/VirtualMachines/
        Instance/instance_count.yaml, plugin/metrics/VirtualMachines/Instance/vcpu_count.yaml, plugin/metrics/VirtualMachines/
        Instance/memory_size.yaml, plugin/metrics/VirtualMachines/Instance/namespace.yaml
      - Container Instance metrics like container count, vCPU, memory, GPU. plugin/metrics/ContainerInstances/Container/
        container_count.yaml, plugin/metrics/ContainerInstances/Container/vcpu_count.yaml, plugin/metrics/ContainerInstances/
        Container/memory_size.yaml, plugin/metrics/ContainerInstances/Container/gpu_size.yaml, plugin/metrics/ContainerInstances/
        Container/namespace.yaml
      - Functions metrics for function app instance count. plugin/metrics/Functions/Instance/instance_count.yaml, plugin/metrics/
        Functions/Instance/namespace.yaml

  Metadata (UI schema)

  - These YAML files define how resources are displayed in the SpaceONE UI: search fields, table columns, and detail tabs. plugin/
    metadata/virtual_machines/instance.yaml, plugin/metadata/container_instances/container.yaml

  Config

  - plugin/conf/cloud_service_conf.py just centralizes the icon base URL used by managers when constructing CloudServiceType
    definitions. plugin/conf/cloud_service_conf.py

  Directory map inside plugin/

  - plugin/conf/: shared configuration values. plugin/conf/cloud_service_conf.py
  - plugin/connector/: Azure SDK/REST wrappers per service. plugin/connector/base.py, plugin/connector/virtual_machines/
    virtual_machines_connector.py, plugin/connector/container_instances/container_instances_connector.py, plugin/connector/
    functions/functions_connector.py
  - plugin/manager/: resource assembly logic per service group plus base orchestration. plugin/manager/base.py, plugin/manager/
    virtual_machines/instance_manager.py, plugin/manager/container_instances/container_manager.py, plugin/manager/functions/
    instance_manager.py
  - plugin/metadata/: UI metadata schemas. plugin/metadata/virtual_machines/instance.yaml, plugin/metadata/container_instances/
    container.yaml
  - plugin/metrics/: metric/namespace definitions for inventory aggregation. plugin/metrics/VirtualMachines/Instance/
    instance_count.yaml, plugin/metrics/ContainerInstances/Container/namespace.yaml, plugin/metrics/Functions/Instance/
    instance_count.yaml
  - plugin/main.py: plugin entrypoint and task routing. plugin/main.py

  Note on missing pieces

  - The code references a subscriptions manager and connector (SubscriptionsManager, SubscriptionsConnector) but those files are
    not present in this repo snapshot, so they must be provided by another package/module or are missing. plugin/main.py, plugin/
    manager/base.py, plugin/manager/virtual_machines/instance_manager.py

  If you want, I can also diagram the end-to-end flow for a specific resource type (e.g., VirtualMachines or Functions).
