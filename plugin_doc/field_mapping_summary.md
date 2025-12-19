# Field Mapping Quick Reference

## Overview

This document provides a quick reference for mapping UI fields in the Cloudforet console to their source code locations in the AWS EC2 plugin.

---

## UI Table Columns → Source Code Mapping

### Column Headers (from preview2.webp)

| # | Column Name | Metadata Path | Data Source Function | AWS API | Line Numbers |
|---|-------------|---------------|---------------------|---------|--------------|
| 1 | **Name** | N/A (default) | `generate_name()` | `Tags[Key='Name']` | `ec2_instance_manager.py:221-226` |
| 2 | **Instance State** | `data.compute.instance_state` | `get_compute_data()` | `State.Name` | `ec2_instance_manager.py:160` |
| 3 | **Instance Type** | `data.compute.instance_type` | `get_compute_data()` | `InstanceType` | `ec2_instance_manager.py:161` |
| 4 | **Core** | `data.hardware.core` | `get_hardware_data()` | `VCpuInfo.DefaultVCpus` | `ec2_instance_manager.py:149` |
| 5 | **Memory** | `data.hardware.memory` | `get_hardware_data()` | `MemoryInfo.SizeInMiB` | `ec2_instance_manager.py:150` |
| 6 | **Availability Zone** | `data.compute.az` | `get_compute_data()` | `Placement.AvailabilityZone` | `ec2_instance_manager.py:159` |
| 7 | **OS** | `data.os.os_distro` | `extract_os_distro()` | `Images[*].Name` | `ec2_instance_manager.py:237-253` |
| 8 | **Primary IP** | `data.primary_ip_address` | Direct assignment | `PrivateIpAddress` | `collector_manager.py:136` |
| 9 | **Account ID** | `account` | Direct from API | `Reservations[*].OwnerId` | `ec2_connector.py:107` |
| 10 | **Provider** | `provider` | Static default | N/A | `server.py:43` |
| 11 | **Region** | `region_code` | Collection param | Job parameter | `ec2_instance_manager.py:96` |

---

## File Structure Overview

```
src/spaceone/inventory/
│
├── connector/
│   └── ec2_connector.py              # AWS API calls (boto3)
│       ├── list_instances()          # describe_instances()
│       ├── list_instance_types()     # describe_instance_types()
│       └── list_images()             # describe_images()
│
├── manager/
│   ├── collector_manager.py          # Main orchestration
│   │   └── list_instances()          # Coordinates collection
│   │
│   ├── ec2/
│   │   └── ec2_instance_manager.py   # Data transformation
│   │       ├── get_server_info()     # Main entry point
│   │       ├── get_compute_data()    # instance_state, type, az
│   │       ├── get_hardware_data()   # core, memory
│   │       ├── get_os_data()         # os_distro, os_type
│   │       └── generate_name()       # Extract Name tag
│   │
│   └── metadata/
│       └── metadata_manager.py       # UI field definitions
│           ├── get_cloud_service_type_metadata()  # Table columns
│           └── get_server_metadata()              # Detail layouts
│
└── model/
    ├── server.py                     # Server resource model
    ├── compute.py                    # Compute data model
    ├── hardware.py                   # Hardware specs model
    ├── os.py                         # OS information model
    └── metadata/
        └── metadata_dynamic_field.py # Field type definitions
```

---

## Key Metadata Field Definitions

### EnumDyField - Instance State with Color Indicators

```python
# File: metadata_manager.py:31-36

EnumDyField.data_source('Instance State', 'data.compute.instance_state',
    default_state={
        'safe': ['RUNNING'],                    # Green dot
        'warning': ['PENDING', 'STOPPING'],     # Yellow dot
        'alert': ['STOPPED'],                   # Red dot
        'disable': ['TERMINATED']               # Gray dot
    }
)
```

**Result:** `● RUNNING` (green circle)

### TextDyField - Simple Text Display

```python
# File: metadata_manager.py:38-70

TextDyField.data_source('Instance Type', 'data.compute.instance_type')
TextDyField.data_source('Core', 'data.hardware.core')
TextDyField.data_source('Memory', 'data.hardware.memory')
TextDyField.data_source('Availability Zone', 'data.compute.az')
TextDyField.data_source('OS', 'data.os.os_distro')
TextDyField.data_source('Primary IP', 'data.primary_ip_address')
TextDyField.data_source('Account ID', 'account')
```

---

## AWS API → Data Path Mapping

### 1. Instance State

```
AWS API: describe_instances()
├─ Response: instance['State']['Name'] = "running"
├─ Transform: .upper() → "RUNNING"
└─ Data Path: data.compute.instance_state
```

### 2. Hardware Specs (Core & Memory)

```
AWS API: describe_instance_types(InstanceTypes=['t2.micro'])
├─ Response:
│  ├─ VCpuInfo.DefaultVCpus = 1
│  └─ MemoryInfo.SizeInMiB = 1024
├─ Transform:
│  └─ memory: 1024 MiB ÷ 1024 = 1.0 GB
└─ Data Paths:
   ├─ data.hardware.core = 1
   └─ data.hardware.memory = 1.0
```

### 3. OS Distribution

```
AWS API Chain:
1. describe_instances() → instance['ImageId'] = "ami-xxx"
2. describe_images(ImageIds=['ami-xxx']) → image['Name'] = "ubuntu-jammy-22.04..."

Transform: extract_os_distro()
├─ Parse image name: "ubuntu-jammy-22.04..."
├─ Match keyword: 'ubuntu' in image_name
└─ Return: 'ubuntu'

Data Path: data.os.os_distro = "ubuntu"
```

### 4. Account ID

```
AWS API: describe_instances()
├─ Response: reservation['OwnerId'] = "565199754239"
├─ Extracted in: ec2_connector.py:107
└─ Data Path: account = "565199754239"
```

---

## Special Field Handling

### Name Field (from Tags)

```python
# File: ec2_instance_manager.py:221-226

@staticmethod
def generate_name(resource):
    for resource_tag in resource.get('Tags', []):
        if resource_tag['Key'] == "Name":
            return resource_tag["Value"]
    return ''  # Empty if no Name tag
```

**AWS API:** `instance['Tags']` array
**Logic:** Find tag with Key="Name", return its Value
**Result:** Empty string if tag doesn't exist

### Memory Unit Conversion

```python
# File: ec2_instance_manager.py:150

memory = round(float((itype.get('MemoryInfo', {}).get('SizeInMiB', 0))/1024), 2)
```

**Input:** MemoryInfo.SizeInMiB (from AWS)
**Conversion:** MiB → GB (divide by 1024)
**Rounding:** 2 decimal places
**Example:** 1024 MiB → 1.0 GB

### OS Distribution Detection

```python
# File: ec2_instance_manager.py:237-253

os_map = {
    'ubuntu': 'ubuntu',
    'amazon': 'amazonlinux',
    'amzn': 'amazonlinux',
    'rhel': 'redhat',
    'centos': 'centos',
    'suse': 'suse',
    'debian': 'debian',
    'fedora': 'fedora'
}

# Search for keywords in AMI name (case-insensitive)
for key in os_map:
    if key in image_name.lower():
        return os_map[key]
```

**Logic:** Pattern matching on AMI name
**Example:** "ubuntu-jammy-22.04-amd64-server-20231201" → "ubuntu"

---

## Color Scheme for Instance State

| State | UI Color | Icon Color | Metadata Key | States |
|-------|----------|-----------|--------------|--------|
| **Running** | Green | `green.500` | `safe` | `['RUNNING']` |
| **Pending** | Yellow | `yellow.500` | `warning` | `['PENDING', 'STOPPING']` |
| **Stopped** | Red | `red.500` | `alert` | `['STOPPED']` |
| **Terminated** | Gray | `gray.400` | `disable` | `['TERMINATED']` |

**Defined in:**
- Metadata: `metadata_manager.py:31-36`
- Color rendering: `metadata_dynamic_field.py:299-313`

---

## Data Model Hierarchy

```
Server (server.py)
├── name: StringType
├── region_code: StringType
├── account: StringType
├── provider: StringType (default='aws')
├── cloud_service_type: StringType (default='Instance')
├── cloud_service_group: StringType (default='EC2')
│
└── data: ServerData
    ├── compute: Compute (compute.py)
    │   ├── instance_state: StringType
    │   ├── instance_type: StringType
    │   ├── instance_id: StringType
    │   ├── az: StringType
    │   └── launched_at: DateTimeType
    │
    ├── hardware: Hardware (hardware.py)
    │   ├── core: IntType
    │   └── memory: FloatType
    │
    ├── os: OS (os.py)
    │   ├── os_distro: StringType
    │   ├── os_arch: StringType
    │   ├── os_type: StringType
    │   └── details: StringType
    │
    ├── primary_ip_address: StringType
    ├── nics: List[NIC]
    ├── disks: List[Disk]
    ├── vpc: VPC
    ├── subnet: Subnet
    ├── security_group: List[SecurityGroup]
    └── load_balancer: List[LoadBalancer]
```

---

## AWS Boto3 API Calls Used

| API Method | Purpose | Returns | Used In |
|------------|---------|---------|---------|
| `describe_instances()` | Get instance details | Instance state, type, IPs, tags, AZ | `ec2_connector.py:95-109` |
| `describe_instance_types()` | Get hardware specs | vCPU count, memory size | `ec2_connector.py:111-120` |
| `describe_images()` | Get AMI information | AMI name for OS detection | `ec2_connector.py:236-239` |
| `describe_volumes()` | Get disk/volume info | Volume details | `ec2_connector.py:225-234` |
| `describe_vpcs()` | Get VPC information | VPC details | `ec2_connector.py:215-223` |
| `describe_subnets()` | Get subnet info | Subnet details | `ec2_connector.py:204-213` |
| `describe_security_groups()` | Get security groups | Security group rules | `ec2_connector.py:193-202` |

---

## Quick Debugging Guide

### To find where a UI field comes from:

1. **Check metadata definition:** `metadata_manager.py:28-257`
   - Look for `TextDyField.data_source('Field Name', 'data.path')`

2. **Trace data path:** Follow the data path (e.g., `data.compute.instance_state`)
   - `data.` → ServerData model in `server.py`
   - `compute.` → Compute model in `compute.py`
   - `instance_state` → Field in Compute model

3. **Find data assignment:** Search for the field name in manager files
   - Usually in `ec2_instance_manager.py` methods
   - Look for dictionary assignment: `'instance_state': ...`

4. **Locate AWS API source:** Check `ec2_connector.py`
   - Find the API method returning the data
   - Check the response parsing

### Example: Tracing "Core" field

1. Metadata: `metadata_manager.py:39` → `'data.hardware.core'`
2. Model: `hardware.py:6` → `core = IntType(default=0)`
3. Assignment: `ec2_instance_manager.py:149` → `'core': itype.get('VCpuInfo', {}).get('DefaultVCpus', 0)`
4. API: `ec2_connector.py:111-120` → `describe_instance_types()` → `VCpuInfo.DefaultVCpus`

---

## Common Data Transformations

| Field | Input (AWS) | Transformation | Output (UI) |
|-------|-------------|----------------|-------------|
| Instance State | `"running"` | `.upper()` | `"RUNNING"` |
| Memory | `1024 MiB` | `÷ 1024, round(2)` | `1.0 GB` |
| OS Distro | AMI name with "ubuntu" | Pattern match | `"ubuntu"` |
| Account ID | OwnerId | Direct | `"565199754239"` |
| Name | Tags array | Find Key="Name" | Value or `""` |

---

## Plugin Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     Plugin Entry Point                       │
│                      (main.py)                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Collector Manager                          │
│             (collector_manager.py)                          │
│  • Orchestrates entire collection process                   │
│  • Calls managers in sequence                               │
│  • Enriches data with cross-resource info                   │
└────────┬──────────────────────────────────────┬─────────────┘
         │                                      │
         ▼                                      ▼
┌──────────────────────┐              ┌──────────────────────┐
│  EC2 Connector       │              │  EC2 Instance Mgr    │
│  (ec2_connector.py)  │◄─────────────│  (ec2_instance_      │
│  • AWS API calls     │              │   manager.py)        │
│  • boto3 client      │              │  • Data transform    │
│  • Pagination        │              │  • Field mapping     │
└──────────────────────┘              └──────────────────────┘
         │                                      │
         │ Returns raw AWS responses            │ Returns structured data
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Models                             │
│  (server.py, compute.py, hardware.py, os.py)                │
│  • Validate data structure                                   │
│  • Type checking                                             │
│  • Default values                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Metadata Manager                           │
│              (metadata_manager.py)                          │
│  • Define UI field mappings                                  │
│  • Specify display types (text, enum, etc.)                 │
│  • Configure colors, badges, icons                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cloudforet Console                         │
│  • Renders table with columns                               │
│  • Displays data according to metadata                       │
│  • Provides filtering, sorting, search                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- **Complete Field Mapping:** `field_source_mapping.md`
- **Visual Field Traces:** `visual_field_trace.md`
- **Previous Analysis:** `aws-ec2-plugin-field-mapping.md`, `mapping_to_console_ui.md`
