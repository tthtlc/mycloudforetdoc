
kubectl -n cloudforet port-forward svc/inventory 50051:50051

grpcurl -plaintext localhost:50051 list
grpcurl -plaintext localhost:50051 describe spaceone.api.inventory.plugin.Collector
grpcurl -plaintext   -d '{"options":{}}'   localhost:50051 spaceone.api.inventory.plugin.Collector/init
grpcurl -plaintext   -d '{"options":{}, "secret_data":{}}'   localhost:50051 spaceone.api.inventory.plugin.Collector/verify
####Call collect (server-streaming; should print 3 streamed messages: CloudServiceType, CloudService, Region):
grpcurl -plaintext   -d '{"options":{}, "secret_data":{}, "filter":{}}'   localhost:50051 spaceone.api.inventory.plugin.Collector/collect

ubuntu@instance-20251024-1642:~/tcy$ bash simplified.sh 
grpc.health.v1.Health
spaceone.api.core.v1.ServerInfo
spaceone.api.inventory.plugin.Collector
spaceone.api.inventory.plugin.Collector is a service:
service Collector {
  rpc collect ( .spaceone.api.inventory.plugin.CollectRequest ) returns ( stream .spaceone.api.inventory.plugin.ResourceInfo );
  rpc init ( .spaceone.api.inventory.plugin.InitRequest ) returns ( .spaceone.api.inventory.plugin.PluginInfo );
  rpc verify ( .spaceone.api.inventory.plugin.VerifyRequest ) returns ( .google.protobuf.Empty );
}
{
  "metadata": {
    "filter_format": [],
    "options_schema": {
      "properties": {},
      "type": "object"
    },
    "supported_features": [],
    "supported_resource_type": [
      "inventory.CloudService",
      "inventory.Region",
      "inventory.CloudServiceType"
    ],
    "supported_schedules": [
      "hours"
    ]
  }
}
{}
{
  "state": "SUCCESS",
  "resource_type": "inventory.CloudServiceType",
  "match_rules": {
    "1": [
      "name",
      "group",
      "provider"
    ]
  },
  "resource": {
    "group": "EC2",
    "is_primary": true,
    "labels": [
      "Compute"
    ],
    "name": "Instance",
    "provider": "aws",
    "service_code": "AmazonEC2"
  }
}
{
  "state": "SUCCESS",
  "resource_type": "inventory.CloudService",
  "match_rules": {
    "1": [
      "reference.resource_id",
      "provider",
      "cloud_service_type",
      "cloud_service_group",
      "account"
    ]
  },
  "resource": {
    "account": "123456789012",
    "cloud_service_group": "EC2",
    "cloud_service_type": "Instance",
    "data": {
      "instance_id": "i-hardcoded1234567890",
      "instance_type": "t3.micro",
      "launched_at": "2025-01-01T00:00:00+00:00",
      "private_ip": "10.0.0.10",
      "public_ip": "203.0.113.10",
      "state": "running"
    },
    "name": "hardcoded-ec2-01",
    "provider": "aws",
    "reference": {
      "external_link": "https://example.invalid/ec2/i-hardcoded1234567890",
      "resource_id": "i-hardcoded1234567890"
    },
    "region_code": "us-east-1",
    "tags": {
      "Name": "hardcoded-ec2-01",
      "managed-by": "cloudforet-minimal-plugin"
    }
  }
}
{
  "state": "SUCCESS",
  "resource_type": "inventory.Region",
  "match_rules": {
    "1": [
      "region_code",
      "provider"
    ]
  },
  "resource": {
    "name": "US East (N. Virginia)",
    "provider": "aws",
    "region_code": "us-east-1"
  }
}

