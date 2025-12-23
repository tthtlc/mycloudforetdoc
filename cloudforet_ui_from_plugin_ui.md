

Great question! Let me explain how Cloudforet's Cloud Service UI is generated from plugin data.

## Architecture Overview

The UI is **dynamically generated** based on metadata provided by the inventory collector plugin. There are two key data structures:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Plugin yields two resource types:                                  │
│                                                                     │
│  1. CloudServiceType  →  Defines the "card" on overview page        │
│     (EC2, IAM, etc.)     + table columns, search fields             │
│                                                                     │
│  2. CloudService      →  Actual resource data (instances, users)    │
│     (individual items)                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. CloudServiceType (Defines the UI Structure)

This is what creates the **EC2 card** on the first page and defines the **table columns** on the second page:

```python
{
    "resource_type": "inventory.CloudServiceType",
    "resource": {
        "name": "Instance",                    # Shows as "Instance 1"
        "group": "EC2",                        # Groups under "EC2" card
        "provider": "aws",                     # Shows "AWS" badge
        "is_primary": True,                    # Featured on overview
        "is_major": True,
        "service_code": "AmazonEC2",
        "tags": {
            "spaceone:icon": "https://.../ec2.svg"  # Icon on card
        },
        "labels": ["Compute", "Server"],
        
        # THIS DEFINES THE TABLE COLUMNS AND SEARCH FIELDS:
        "metadata": {
            "view": {
                "search": [
                    {"key": "data.compute.instance_state", "name": "Instance State"},
                    {"key": "data.compute.instance_type", "name": "Instance Type"},
                    {"key": "data.compute.az", "name": "Availability Zone"},
                    {"key": "data.os.os_distro", "name": "OS"},
                ],
                "table": {
                    "layout": {
                        "name": "",
                        "type": "query-search-table",
                        "options": {
                            "fields": [
                                {"key": "data.compute.instance_state", "name": "Instance State",
                                 "type": "enum",
                                 "options": {
                                     "RUNNING": {"type": "state", "options": {"icon": {"color": "green"}}},
                                     "STOPPED": {"type": "state", "options": {"icon": {"color": "red"}}}
                                 }},
                                {"key": "data.compute.instance_type", "name": "Instance Type"},
                                {"key": "data.hardware.core", "name": "Core"},
                                {"key": "data.hardware.memory", "name": "Memory"},
                                {"key": "data.compute.az", "name": "Availability Zone"},
                                {"key": "data.os.os_distro", "name": "OS"},
                                {"key": "data.primary_ip_address", "name": "Primary IP"},
                                {"key": "account", "name": "Account ID"},
                                {"key": "provider", "name": "Provider"},
                                {"key": "region_code", "name": "Region"},
                            ]
                        }
                    }
                }
            }
        }
    }
}
```

---

## 2. CloudService (The Actual Data)

This is the EC2 instance data that fills the table:

```python
{
    "resource_type": "inventory.CloudService",
    "resource": {
        "name": "",                              # Instance name (can be empty)
        "cloud_service_type": "Instance",        # Links to CloudServiceType.name
        "cloud_service_group": "EC2",            # Links to CloudServiceType.group
        "provider": "aws",
        "account": "565199754239",               # Account ID column
        "region_code": "ap-southeast-2a",
        "instance_type": "t2.micro",
        
        # THE "data" FIELD MAPS TO TABLE COLUMNS:
        "data": {
            "compute": {
                "instance_state": "RUNNING",     # → Instance State column
                "instance_type": "t2.micro",     # → Instance Type column
                "az": "ap-southeast-2a",         # → Availability Zone column
            },
            "hardware": {
                "core": 1,                       # → Core column
                "memory": 1,                     # → Memory column (GB)
            },
            "os": {
                "os_distro": "ubuntu",           # → OS column
            },
            "primary_ip_address": "172.31.7.198", # → Primary IP column
        },
        "reference": {
            "resource_id": "i-0abc123...",
            "external_link": "https://console.aws.amazon.com/ec2/..."
        }
    }
}
```

---

## 3. How Fields Map to UI

```
┌──────────────────────────────────────────────────────────────────────────┐
│ CloudServiceType.metadata.view.table.options.fields                      │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  {"key": "data.compute.instance_state", "name": "Instance State"}        │
│       │                                        │                         │
│       ▼                                        ▼                         │
│  CloudService.data.compute.instance_state  Column Header                 │
│       │                                                                  │
│       ▼                                                                  │
│   "RUNNING"  ──────────────────────────────▶  ● RUNNING (green dot)      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Visual Mapping to Your Screenshots

### Image 1 - Overview Page
```
CloudServiceType:
├── provider: "aws"           →  "AWS" label
├── group: "EC2"              →  "EC2" card title  
├── name: "Instance"          →  "Instance 1" (1 = count of CloudServices)
├── name: "Volume"            →  "Volume 1"
└── tags.spaceone:icon        →  EC2 icon
```

### Image 2 - Detail Table
```
CloudServiceType.metadata.view.table.options.fields:
┌─────────────────────────────────────────────────────────────────────────┐
│ Name │ Instance State │ Instance Type │ Core │ Memory │ AZ │ OS   │ ... │
├─────────────────────────────────────────────────────────────────────────┤
│      │  ● RUNNING     │  t2.micro     │  1   │   1    │ ap-│ubuntu│ ... │
└─────────────────────────────────────────────────────────────────────────┘
         ↑                    ↑            ↑       ↑
         │                    │            │       │
CloudService.data:
├── compute.instance_state: "RUNNING"
├── compute.instance_type: "t2.micro"  
├── hardware.core: 1
├── hardware.memory: 1
├── compute.az: "ap-southeast-2a"
└── os.os_distro: "ubuntu"
```

---

## 5. Complete Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AWS Plugin    │     │  Inventory Svc  │     │   Console UI    │
│                 │     │                 │     │                 │
│ yield           │────▶│ Store in        │────▶│ Render cards    │
│ CloudServiceType│     │ MongoDB         │     │ from metadata   │
│                 │     │                 │     │                 │
│ yield           │────▶│ Store in        │────▶│ Render table    │
│ CloudService    │     │ MongoDB         │     │ from data       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## For Your Mock Azure Plugin

To get similar display for your mock Azure VMs, ensure your `CloudServiceType` includes proper metadata:

```python
def _make_vm_cloud_service_type(self) -> dict:
    return {
        "name": "VirtualMachine",
        "group": "Compute",
        "provider": "azure",
        "is_primary": True,
        "metadata": {
            "view": {
                "table": {
                    "layout": {
                        "options": {
                            "fields": [
                                {"key": "data.power_state", "name": "Power State",
                                 "type": "enum",
                                 "options": {
                                     "running": {"type": "state", "options": {"icon": {"color": "green"}}},
                                     "stopped": {"type": "state", "options": {"icon": {"color": "red"}}}
                                 }},
                                {"key": "data.vm_size", "name": "VM Size"},
                                {"key": "data.os_type", "name": "OS"},
                                {"key": "data.private_ip", "name": "Private IP"},
                                {"key": "region_code", "name": "Region"},
                            ]
                        }
                    }
                }
            }
        }
    }
```
