


explain how the YAML files in the manager/metadata are being transformed into GUI?   what is the specification for deciding the
  transformation?   and which modules are doing all the transformation?


• I'm inspecting metadata manager and model metadata files to understand how YAML metadata transforms into GUI components, focusing
  on dynamic widgets, layout, and search features.

• Ran for f in spaceone/inventory/manager/metadata/metadata_manager.py spaceone/inventory/model/metadata/metadata_dynamic_widget.py
  │ spaceone/inventory/model/metadata/metadata_dynamic_layout.py spaceone/inventory/model/metadata/metadata_dynamic_field.py
  │ spaceone/inventory/model/metadata/metadata_dynamic_search.py spaceone/inventory/model/metadata/metadata.py; do echo "--- $f";
  │ … +1 lines
  └ /opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted
    --- spaceone/inventory/manager/metadata/metadata_manager.py
    … +828 lines
            table_meta = MetaDataViewTable({'layout': QuerySearchTableDynamicLayout.set_fields(name, fields)})
            return cls({'view': MetaDataView({'table': table_meta, 'search': search, 'widget': widget})})

• I'm tracing how metadata_manager loads YAML widget files by focusing on the get_data_from_yaml function and searching for
  metadata_manager references. This will clarify the transformation process for these YAML configs.

• Explored
  └ Search MetadataManager
    Read collector_manager.py, __init__.py

• I'm focusing on logic that converts YAML widget definitions into models, noting that metadata_manager might use
  get_data_from_yaml and dynamic widget classes for this. I'll explore those further to clarify the approach.

• Explored
  └ Search total_running_count_conf in metadata_manager.py
    Read metadata_manager.py

• The YAML files load via utilities into metadata_manager, then use BaseDynamicWidget subclasses to validate and transform specs
  for cards and charts with filters and options. This metadata feeds into CloudServiceType models that the frontend’s SpaceONE
  console uses to render dynamic GUIs.

• Explored
  └ Read cloud_service_type.py

• I’m mapping how metadata set on cloud service types propagates through the collector output and collector manager's resource
  listing, noting that CloudServiceTypeResourceResponse models reference this metadata; next I’ll review resource model files like
  ServerResourceResponse to confirm usage.

• Explored
  └ Read resource.py

• The console builds dynamic views from metadata defined primarily in YAML files parsed into Python dicts. These dicts create
  CardWidget and ChartWidget instances in metadata_manager, which are transformed through BaseDynamicWidget schematics into typed
  metadata. This metadata is injected into CloudServiceTypeMetadata, emitted by CollectorManager, and exposed via gRPC to the
  console frontend for rendering. Aggregated queries combine filters automatically (e.g., provider, service type) and use
  operations like unwind/group/count as defined in metadata_dynamic_widget classes. Key modules involved are libs/utils for YAML
  loading, metadata_dynamic_widget for widget modeling and aggregation specs, metadata_manager for metadata construction,
  collector_manager for emission of cloud service types, and service API layers handling gRPC delivery.

─ Worked for 42s ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• - The YAMLs are loaded in spaceone/inventory/manager/metadata/metadata_manager.py via get_data_from_yaml (from libs/utils.py).
    Each YAML supplies parameters to CardWidget.set or ChartWidget.set, which call BaseDynamicWidget.set (model/metadata/
    metadata_dynamic_widget.py) to build a typed widget model.
  - BaseDynamicWidget.set normalizes the YAML into schematics models: it turns query.aggregate/filter entries into
    BaseDynamicWidgetQuery* objects, injects required filters (provider=aws, cloud_service_group=EC2, cloud_service_type=Instance),
    and converts options.name_options/value_options and chart_type into typed option classes.
  - Those widget models are assembled into a CloudServiceTypeMetadata object in MetadataManager.get_cloud_service_type_metadata()
    and attached to the Cloud Service Type returned by CollectorManager.list_cloud_service_types(). The gRPC service (service/
    collector_service.py → api/plugin/collector.py) streams that metadata back to the SpaceONE console, which renders the GUI
    dynamically from the metadata payload.
  - Specification that drives the transformation lives in the schematics models under spaceone/inventory/model/metadata/:
      - metadata_dynamic_widget.py: defines allowed widget fields (name, type card/chart, options.chart_type in {COLUMN, DONUT,
        TREEMAP}, options.name_options/value_options types, aggregation ops unwind/group/count/sort/project, filters, etc.).
      - metadata_dynamic_layout.py / metadata_dynamic_field.py / metadata_dynamic_search.py: define the parallel spec for tables/
        layouts/fields/search (used for the main resource view, not the widgets).
      - metadata.py: wraps widgets/layouts/search into the CloudServiceTypeMetadata envelope sent to the UI.
  - Modules doing the work: YAML loader (libs/utils.py), metadata builder (manager/metadata/metadata_manager.py), widget/model
    converters (model/metadata/*.py), and the collector pipeline that returns metadata (manager/collector_manager.py, service/
    collector_service.py, api/plugin/collector.py). The actual rendering is handled by the SpaceONE console, which interprets the
    returned metadata schema.

