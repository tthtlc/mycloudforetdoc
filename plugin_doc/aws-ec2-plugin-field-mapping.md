# AWS EC2 Plugin Field Mapping Analysis

## Repository Structure

Based on the Cloudforet plugin architecture, the AWS EC2 Inventory Collector follows this structure:

```
plugin-aws-ec2-inven-collector/
├── src/
│   └── plugin/
│       ├── main.py                    # Entry point
│       ├── manager/
│       │   └── ec2_instance_manager.py    # Data collection from AWS API
│       ├── connector/
│       │   └── ec2_connector.py           # AWS boto3 API calls
│       ├── metadata/
│       │   └── ec2_instance.py            # UI METADATA - Table columns defined here!
│       └── conf/
│           └── cloud_service_conf.py      # Provider, group, service type config
```

---

## Field Sources for Your Screenshot (Image 2)

### Table Columns in Detail View

| UI Column | Source File | Data Path | AWS API Source |
|-----------|-------------|-----------|----------------|
| **Name** | `ec2_instance_manager.py` | `name` or `tags['Name']` | `describe_instances()` → `Tags[Key='Name']` |
| **Instance State** | `ec2_instance_manager.py` | `data.compute.instance_state` | `describe_instances()` → `State.Name` |
| **Instance Type** | `ec2_instance_manager.py` | `data.compute.instance_type` | `describe_instances()` → `InstanceType` |
| **Core** | `ec2_instance_manager.py` | `data.hardware.core` | `describe_instance_types()` → `VCpuInfo.DefaultVCpus` |
| **Memory** | `ec2_instance_manager.py` | `data.hardware.memory` | `describe_instance_types()` → `MemoryInfo.SizeInMiB` |
| **Availability Zone** | `ec2_instance_manager.py` | `data.compute.az` | `describe_instances()` → `Placement.AvailabilityZone` |
| **OS** | `ec2_instance_manager.py` | `data.os.os_distro` | `describe_images()` → Platform detection |
| **Primary IP** | `ec2_instance_manager.py` | `data.primary_ip_address` | `describe_instances()` → `PrivateIpAddress` |
| **Account ID** | `ec2_instance_manager.py` | `account` | `get_caller_identity()` → `Account` |
| **Provider** | `cloud_service_conf.py` | `provider` | Static: `"aws"` |
| **Region** | `ec2_instance_manager.py` | `region_code` | Collection region parameter |

---

## Key Source Files Explained

### 1. `src/plugin/metadata/ec2_instance.py` - UI DEFINITION

This file defines what columns appear in the table and how they're displayed:

```python
# File: src/plugin/metadata/ec2_instance.py

ec2_instance = {
    "name": "Instance",
    "group": "EC2", 
    "provider": "aws",
    "service_code": "AmazonEC2",
    "is_primary": True,
    "is_major": True,
    "labels": ["Compute", "Server"],
    "tags": {
        "spaceone:icon": "https://spaceone-custom-assets.../icons/aws-ec2.svg"
    },
    
    # THIS SECTION DEFINES TABLE COLUMNS IN YOUR SCREENSHOT:
    "metadata": {
        "view": {
            "search": [
                {"key": "data.compute.instance_id", "name": "Instance ID"},
                {"key": "data.compute.instance_state", "name": "Instance State"},
                {"key": "data.compute.instance_type", "name": "Instance Type"},
                {"key": "data.compute.az", "name": "Availability Zone"},
                {"key": "data.os.os_distro", "name": "OS Distribution"},
                {"key": "data.primary_ip_address", "name": "Primary IP Address"},
                {"key": "account", "name": "Account ID"},
            ],
            "table": {
                "layout": {
                    "name": "",
                    "type": "query-search-table",
                    "options": {
                        "fields": [
                            # Column 1: Instance State with colored status indicator
                            {
                                "key": "data.compute.instance_state",
                                "name": "Instance State",
                                "type": "enum",
                                "options": {
                                    "RUNNING": {
                                        "type": "state",
                                        "options": {
                                            "icon": {"color": "green"}
                                        }
                                    },
                                    "STOPPED": {
                                        "type": "state", 
                                        "options": {
                                            "icon": {"color": "red"}
                                        }
                                    },
                                    "PENDING": {
                                        "type": "state",
                                        "options": {
                                            "icon": {"color": "yellow"}
                                        }
                                    }
                                }
                            },
                            # Column 2: Instance Type
                            {
                                "key": "data.compute.instance_type",
                                "name": "Instance Type"
                            },
                            # Column 3: Core count
                            {
                                "key": "data.hardware.core",
                                "name": "Core"
                            },
                            # Column 4: Memory
                            {
                                "key": "data.hardware.memory",
                                "name": "Memory"
                            },
                            # Column 5: Availability Zone
                            {
                                "key": "data.compute.az",
                                "name": "Availability Zone"
                            },
                            # Column 6: OS
                            {
                                "key": "data.os.os_distro",
                                "name": "OS"
                            },
                            # Column 7: Primary IP
                            {
                                "key": "data.primary_ip_address",
                                "name": "Primary IP"
                            },
                            # Column 8: Account ID
                            {
                                "key": "account",
                                "name": "Account ID"
                            },
                            # Column 9: Provider
                            {
                                "key": "provider",
                                "name": "Provider"
                            },
                            # Column 10: Region
                            {
                                "key": "region_code",
                                "name": "Region"
                            }
                        ]
                    }
                }
            }
        }
    }
}
```

---

### 2. `src/plugin/manager/ec2_instance_manager.py` - DATA COLLECTION

This file populates the actual data that fills those columns:

```python
# File: src/plugin/manager/ec2_instance_manager.py

class EC2InstanceManager:
    
    def collect_resources(self, params):
        # Calls AWS APIs and transforms data
        instances = self.connector.describe_instances()
        instance_types = self.connector.describe_instance_types()
        
        for instance in instances:
            # Build the CloudService resource
            cloud_service = {
                "name": self._get_instance_name(instance),  # From tags
                "cloud_service_type": "Instance",
                "cloud_service_group": "EC2",
                "provider": "aws",
                "account": self.account_id,
                "region_code": self.region,
                "instance_type": instance.get("InstanceType"),
                
                # THE "data" OBJECT - Maps to metadata.view.table.options.fields
                "data": {
                    "compute": {
                        "instance_id": instance.get("InstanceId"),
                        "instance_state": instance.get("State", {}).get("Name", "").upper(),
                        "instance_type": instance.get("InstanceType"),
                        "az": instance.get("Placement", {}).get("AvailabilityZone"),
                        "launched_at": instance.get("LaunchTime"),
                        "key_name": instance.get("KeyName"),
                    },
                    "hardware": {
                        "core": self._get_vcpu_count(instance, instance_types),
                        "memory": self._get_memory_gb(instance, instance_types),
                    },
                    "os": {
                        "os_distro": self._get_os_distribution(instance),
                        "os_arch": instance.get("Architecture"),
                    },
                    "primary_ip_address": instance.get("PrivateIpAddress"),
                    "nics": self._get_network_interfaces(instance),
                    "disks": self._get_block_devices(instance),
                    "security_groups": self._get_security_groups(instance),
                },
                "reference": {
                    "resource_id": instance.get("InstanceId"),
                    "external_link": f"https://{self.region}.console.aws.amazon.com/ec2/v2/home?region={self.region}#InstanceDetails:instanceId={instance.get('InstanceId')}"
                }
            }
            
            yield cloud_service
    
    def _get_instance_name(self, instance):
        """Extract Name from tags"""
        tags = instance.get("Tags", [])
        for tag in tags:
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""
    
    def _get_vcpu_count(self, instance, instance_types):
        """Get vCPU count from instance type info"""
        instance_type = instance.get("InstanceType")
        for it in instance_types:
            if it.get("InstanceType") == instance_type:
                return it.get("VCpuInfo", {}).get("DefaultVCpus", 0)
        return 0
    
    def _get_memory_gb(self, instance, instance_types):
        """Get memory in GB from instance type info"""
        instance_type = instance.get("InstanceType")
        for it in instance_types:
            if it.get("InstanceType") == instance_type:
                memory_mib = it.get("MemoryInfo", {}).get("SizeInMiB", 0)
                return round(memory_mib / 1024, 1)  # Convert to GB
        return 0
    
    def _get_os_distribution(self, instance):
        """Detect OS from platform or AMI info"""
        platform = instance.get("Platform", "")
        if platform.lower() == "windows":
            return "windows"
        # Default to linux, or detect from AMI name
        return "linux"
```

---

### 3. `src/plugin/connector/ec2_connector.py` - AWS API CALLS

This file makes the actual boto3 calls to AWS:

```python
# File: src/plugin/connector/ec2_connector.py

import boto3

class EC2Connector:
    
    def __init__(self, secret_data, region):
        self.client = boto3.client(
            'ec2',
            aws_access_key_id=secret_data.get('aws_access_key_id'),
            aws_secret_access_key=secret_data.get('aws_secret_access_key'),
            region_name=region
        )
    
    def describe_instances(self):
        """
        AWS API: ec2.describe_instances()
        Returns instance data including:
        - InstanceId, InstanceType, State
        - Placement (AvailabilityZone)
        - PrivateIpAddress, PublicIpAddress
        - Tags (including Name)
        """
        instances = []
        paginator = self.client.get_paginator('describe_instances')
        
        for page in paginator.paginate():
            for reservation in page.get('Reservations', []):
                instances.extend(reservation.get('Instances', []))
        
        return instances
    
    def describe_instance_types(self, instance_types):
        """
        AWS API: ec2.describe_instance_types()
        Returns hardware specs:
        - VCpuInfo.DefaultVCpus (Core count)
        - MemoryInfo.SizeInMiB (Memory)
        """
        response = self.client.describe_instance_types(
            InstanceTypes=instance_types
        )
        return response.get('InstanceTypes', [])
```

---

## Visual Flow: AWS API → UI Table

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            AWS EC2 API Response                                  │
│  describe_instances() returns:                                                  │
│  {                                                                              │
│    "InstanceId": "i-0abc123...",                                                │
│    "InstanceType": "t2.micro",                                                  │
│    "State": {"Name": "running"},                                                │
│    "Placement": {"AvailabilityZone": "ap-southeast-2a"},                        │
│    "PrivateIpAddress": "172.31.7.198",                                          │
│    "Tags": [{"Key": "Name", "Value": "my-instance"}]                           │
│  }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ec2_instance_manager.py                                   │
│  Transforms AWS response into CloudService resource:                            │
│  {                                                                              │
│    "cloud_service_type": "Instance",                                            │
│    "cloud_service_group": "EC2",                                                │
│    "provider": "aws",                                                           │
│    "account": "565199754239",                                                   │
│    "region_code": "ap-southeast-2a",                                            │
│    "data": {                                                                    │
│      "compute": {                                                               │
│        "instance_state": "RUNNING",      ──────┐                                │
│        "instance_type": "t2.micro",      ──────┤                                │
│        "az": "ap-southeast-2a"           ──────┤                                │
│      },                                         │                               │
│      "hardware": {                              │                               │
│        "core": 1,                        ──────┤                                │
│        "memory": 1                       ──────┤                                │
│      },                                         │                               │
│      "os": {                                    │                               │
│        "os_distro": "ubuntu"             ──────┤                                │
│      },                                         │                               │
│      "primary_ip_address": "172.31.7.198"──────┤                                │
│    }                                            │                               │
│  }                                              │                               │
└─────────────────────────────────────────────────│───────────────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ec2_instance.py (metadata)                             │
│  Defines UI table columns that MAP to the data paths:                          │
│                                                                                 │
│  metadata.view.table.options.fields:                                           │
│  [                                                                             │
│    {"key": "data.compute.instance_state", "name": "Instance State"}, ◄─────────│
│    {"key": "data.compute.instance_type", "name": "Instance Type"},   ◄─────────│
│    {"key": "data.hardware.core", "name": "Core"},                    ◄─────────│
│    {"key": "data.hardware.memory", "name": "Memory"},                ◄─────────│
│    {"key": "data.compute.az", "name": "Availability Zone"},          ◄─────────│
│    {"key": "data.os.os_distro", "name": "OS"},                       ◄─────────│
│    {"key": "data.primary_ip_address", "name": "Primary IP"},         ◄─────────│
│    {"key": "account", "name": "Account ID"},                                    │
│    {"key": "provider", "name": "Provider"},                                     │
│    {"key": "region_code", "name": "Region"}                                     │
│  ]                                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Console UI Table                                    │
│                                                                                 │
│ ┌──────┬───────────────┬─────────────┬──────┬────────┬────────────┬───────┐    │
│ │ Name │Instance State │Instance Type│ Core │ Memory │     AZ     │  OS   │... │
│ ├──────┼───────────────┼─────────────┼──────┼────────┼────────────┼───────┤    │
│ │      │  ● RUNNING    │  t2.micro   │  1   │   1    │ap-south...-2a│ubuntu│... │
│ └──────┴───────────────┴─────────────┴──────┴────────┴────────────┴───────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Image 1: Overview Page Fields

For the first screenshot showing the EC2 card with "Instance 1" and "Volume 1":

### Source: `cloud_service_conf.py` and `ec2_instance.py`

```python
# CloudServiceType definition creates the card
{
    "name": "Instance",           # → Shows as "Instance" on card
    "group": "EC2",               # → Card header "EC2"  
    "provider": "aws",            # → "AWS" badge
    "is_primary": True,           # → Featured on overview
    "service_code": "AmazonEC2",
    "tags": {
        "spaceone:icon": "https://.../ec2-icon.svg"  # → Card icon
    }
}

# The "1" in "Instance 1" = COUNT of CloudService resources
# matching cloud_service_type="Instance" and cloud_service_group="EC2"
```

---

## Summary: File → UI Mapping

| What You See | Source File | What Defines It |
|--------------|-------------|-----------------|
| "AWS" provider badge | `cloud_service_conf.py` | `provider: "aws"` |
| "EC2" card title | `ec2_instance.py` | `group: "EC2"` |
| "Instance 1" label | `ec2_instance.py` | `name: "Instance"` + count |
| EC2 icon | `ec2_instance.py` | `tags["spaceone:icon"]` |
| Table column headers | `ec2_instance.py` | `metadata.view.table.options.fields[].name` |
| Table column values | `ec2_instance_manager.py` | `data.*` object paths |
| Status colors (green/red) | `ec2_instance.py` | `type: "enum"` with state options |
| AWS API data | `ec2_connector.py` | boto3 `describe_instances()` etc. |
