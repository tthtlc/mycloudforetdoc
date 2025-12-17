
}
ubuntu@instance-20251024-1642:~/tcy$  grpcurl -plaintext localhost:50051 list
grpc.health.v1.Health
spaceone.api.core.v1.ServerInfo
spaceone.api.inventory.v1.ChangeHistory
spaceone.api.inventory.v1.CloudService
spaceone.api.inventory.v1.CloudServiceQuerySet
spaceone.api.inventory.v1.CloudServiceReport
spaceone.api.inventory.v1.CloudServiceStats
spaceone.api.inventory.v1.CloudServiceType
spaceone.api.inventory.v1.Collector
spaceone.api.inventory.v1.CollectorRule
spaceone.api.inventory.v1.Job
spaceone.api.inventory.v1.JobTask
spaceone.api.inventory.v1.Metric
spaceone.api.inventory.v1.MetricData
spaceone.api.inventory.v1.MetricExample
spaceone.api.inventory.v1.Namespace
spaceone.api.inventory.v1.Note
spaceone.api.inventory.v1.Region
ubuntu@instance-20251024-1642:~/tcy$ grpcurl -plaintext localhost:50051 describe spaceone.api.inventory.plugin.Collector
Failed to resolve symbol "spaceone.api.inventory.plugin.Collector": Symbol not found: spaceone.api.inventory.plugin.Collector
ubuntu@instance-20251024-1642:~/tcy$ grpcurl -plaintext localhost:50051 describe spaceone.api.inventory.v1.Collector
spaceone.api.inventory.v1.Collector is a service:
service Collector {
  rpc collect ( .spaceone.api.inventory.v1.CollectRequest ) returns ( .spaceone.api.inventory.v1.JobInfo ) {
    option (.google.api.http) = { post: "/inventory/v1/collector/collect", body: "*" };
  }
  rpc create ( .spaceone.api.inventory.v1.CreateCollectorRequest ) returns ( .spaceone.api.inventory.v1.CollectorInfo ) {
    option (.google.api.http) = { post: "/inventory/v1/collector/create", body: "*" };
  }
  rpc delete ( .spaceone.api.inventory.v1.CollectorRequest ) returns ( .google.protobuf.Empty ) {
    option (.google.api.http) = { post: "/inventory/v1/collector/delete", body: "*" };
  }
  rpc get ( .spaceone.api.inventory.v1.CollectorRequest ) returns ( .spaceone.api.inventory.v1.CollectorInfo ) {
} } option (.google.api.http) = { post: "/inventory/v1/collector/verify-plugin", body: "*" };obuf.Empty ) {.CollectorInfo ) 
