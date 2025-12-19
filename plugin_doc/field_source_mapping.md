# AWS EC2 Plugin - Exact Field Source Mapping

This document traces each field visible in the Cloudforet UI (preview1.webp and preview2.webp) back to its exact source in the plugin code.

---

## Preview 1: Cloud Service Overview Page

### Field Mapping for "AWS EC2" Card

| UI Element | Value Displayed | Source File | Source Line | Code Reference |
|------------|-----------------|-------------|-------------|----------------|
| **Provider Badge** | "AWS" | `server.py` | 43 | `provider = StringType(default='aws')` |
| **Service Group** | "EC2" | `server.py` | 45 | `cloud_service_group = StringType(default='EC2')` |
| **Service Type** | "Instance" | `server.py` | 44 | `cloud_service_type = StringType(default='Instance')` |
| **Icon** | EC2 Icon | `collector_manager.py` | 229 | `'spaceone:icon': 'https://spaceone-custom-assets.s3.ap-northeast-2.amazonaws.com/console-assets/icons/aws-ec2.svg'` |
| **Count "1"** | "Instance 1" | N/A | N/A | Count of Server resources returned by collector |

---

## Preview 2: Instance Detail Table

### Table Column Definitions

The table columns are defined in the metadata manager. Here's the exact mapping:

| UI Column Header | Data Displayed | Metadata Definition | Data Collection | AWS API Source |
|------------------|----------------|---------------------|-----------------|----------------|
| **Name** | (empty) | N/A - Uses `server.name` | `ec2_instance_manager.py:221-226` | `Tags[Key='Name']` from `describe_instances()` |
| **Instance State** | RUNNING (green dot) | `metadata_manager.py:31-36` | `ec2_instance_manager.py:160` | `State.Name` from `describe_instances()` |
| **Instance Type** | t2.micro | `metadata_manager.py:38` | `ec2_instance_manager.py:161` | `InstanceType` from `describe_instances()` |
| **Core** | 1 | `metadata_manager.py:39` | `ec2_instance_manager.py:149` | `VCpuInfo.DefaultVCpus` from `describe_instance_types()` |
| **Memory** | 1 | `metadata_manager.py:40` | `ec2_instance_manager.py:150` | `MemoryInfo.SizeInMiB` from `describe_instance_types()` |
| **Availability Zone** | ap-southeast-2a | `metadata_manager.py:53` | `ec2_instance_manager.py:159` | `Placement.AvailabilityZone` from `describe_instances()` |
| **OS** | ubuntu | `metadata_manager.py:63` | `ec2_instance_manager.py:102, 237-253` | Extracted from AMI `Name` via `describe_images()` |
| **Primary IP** | 172.31.7.198 | `metadata_manager.py:70` | `collector_manager.py:136` | `PrivateIpAddress` from `describe_instances()` |
| **Account ID** | 565199754239 | `metadata_manager.py:213` | `collector_manager.py:107, 159` | `OwnerId` from `describe_instances()` response |
| **Provider** | AWS | `metadata_manager.py:241` | `server.py:43` | Static default value |
| **Region** | Asia Pacific | N/A | `ec2_instance_manager.py:96` | Collection parameter `region_name` |

---

## Detailed Field Tracing

### 1. Instance State (RUNNING with green indicator)

**UI Display:** Green circle with "RUNNING" text

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Lines: 31-36

EnumDyField.data_source('Instance State', 'data.compute.instance_state', default_state={
    'safe': ['RUNNING'],
    'warning': ['PENDING', 'REBOOTING', 'SHUTTING-DOWN', 'STOPPING', 'STARTING',
                'PROVISIONING', 'STAGING', 'DEALLOCATING', 'REPAIRING'],
    'alert': ['STOPPED', 'DEALLOCATED', 'SUSPENDED'],
    'disable': ['TERMINATED']
})
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Line: 160

'instance_state': instance.get('State', {}).get('Name').upper()
```

**AWS API Call:**
```python
# File: src/spaceone/inventory/connector/ec2_connector.py
# Lines: 95-109

def list_instances(self, **query):
    ec2_instances = []
    query = self._generate_query(is_paginate=True, **query)
    query.update({'Filters': [{'Name': 'instance-state-name',
                               'Values': ['pending', 'running', 'shutting-down', 'stopping', 'stopped']}]
                  })
    paginator = self.ec2_client.get_paginator('describe_instances')
    response_iterator = paginator.paginate(**query)
    # Returns: instance['State']['Name'] = 'running'
```

**Data Model:**
```python
# File: src/spaceone/inventory/model/compute.py
# Line: 12

instance_state = StringType(choices=('PENDING', 'RUNNING', 'SHUTTING-DOWN', 'TERMINATED', 'STOPPING', 'STOPPED'))
```

---

### 2. Instance Type (t2.micro)

**UI Display:** "t2.micro"

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 38

TextDyField.data_source('Instance Type', 'data.compute.instance_type')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Line: 161

'instance_type': instance.get('InstanceType', '')
```

**AWS API:**
- Source: `ec2_connector.py:95-109` → `describe_instances()` → `instance['InstanceType']`

**Data Model:**
```python
# File: src/spaceone/inventory/model/compute.py
# Line: 13

instance_type = StringType()
```

---

### 3. Core (1)

**UI Display:** "1"

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 39

TextDyField.data_source('Core', 'data.hardware.core')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Lines: 143-153

def get_hardware_data(self, instance, itypes):
    hardware_data = {}
    itype = self.match_instance_type(instance.get('InstanceType'), itypes)

    if itype is not None:
        hardware_data = {
            'core': itype.get('VCpuInfo', {}).get('DefaultVCpus', 0),
            'memory': round(float((itype.get('MemoryInfo', {}).get('SizeInMiB', 0))/1024), 2)
        }

    return Hardware(hardware_data, strict=False)
```

**AWS API Call:**
```python
# File: src/spaceone/inventory/connector/ec2_connector.py
# Lines: 111-120

def list_instance_types(self, **query):
    instance_types = []
    query = self._generate_query(is_paginate=True, **query)
    paginator = self.ec2_client.get_paginator('describe_instance_types')
    response_iterator = paginator.paginate(**query)

    for data in response_iterator:
        instance_types.extend(data.get('InstanceTypes', []))

    return instance_types
    # Returns: itype['VCpuInfo']['DefaultVCpus'] = 1 (for t2.micro)
```

**Called from:**
```python
# File: src/spaceone/inventory/manager/collector_manager.py
# Line: 72

itypes = ec2_connector.list_instance_types()
```

**Data Model:**
```python
# File: src/spaceone/inventory/model/hardware.py
# Line: 6

core = IntType(default=0)
```

---

### 4. Memory (1)

**UI Display:** "1" (GB)

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 40

TextDyField.data_source('Memory', 'data.hardware.memory')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Line: 150

'memory': round(float((itype.get('MemoryInfo', {}).get('SizeInMiB', 0))/1024), 2)
# For t2.micro: 1024 MiB / 1024 = 1.0 GB
```

**AWS API:**
- Source: `ec2_connector.py:111-120` → `describe_instance_types()` → `itype['MemoryInfo']['SizeInMiB']`
- Conversion: MiB to GB by dividing by 1024

**Data Model:**
```python
# File: src/spaceone/inventory/model/hardware.py
# Line: 7

memory = FloatType(default=0.0)
```

---

### 5. Availability Zone (ap-southeast-2a)

**UI Display:** "ap-southeast-2a"

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 53

TextDyField.data_source('Availability Zone', 'data.compute.az')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Line: 159

'az': instance.get('Placement', {}).get('AvailabilityZone', '')
```

**AWS API:**
- Source: `ec2_connector.py:95-109` → `describe_instances()` → `instance['Placement']['AvailabilityZone']`

**Data Model:**
```python
# File: src/spaceone/inventory/model/compute.py
# Line: 11

az = StringType()
```

---

### 6. OS (ubuntu)

**UI Display:** "ubuntu"

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 63

TextDyField.data_source('OS', 'data.os.os_distro')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Lines: 100-108, 194-198, 237-273

def get_os_data(self, image, os_type, os_details):
    os_data = {
        'os_distro': self.get_os_distro(image.get('Name', ''), os_type),
        'os_arch': image.get('Architecture', ''),
        'os_type': os_type,
        'details': os_details
    }
    return OS(os_data, strict=False)

def get_os_distro(self, image_name, os_type):
    if image_name == '':
        return os_type.lower()
    else:
        return self.extract_os_distro(image_name, os_type)

@staticmethod
def extract_os_distro(image_name, os_type):
    if os_type == 'LINUX':
        os_map = {
            'suse': 'suse',
            'rhel': 'redhat',
            'cetnos': 'centos',
            'fedora': 'fedora',
            'ubuntu': 'ubuntu',  # ← Matches "ubuntu" in image name
            'debian': 'debia',
            'amazon': 'amazonlinux',
            'amzn': 'amazonlinux'
        }

        image_name.lower()
        for key in os_map:
            if key in image_name:
                return os_map[key]  # Returns 'ubuntu'

        return 'linux'
```

**AWS API:**
```python
# File: src/spaceone/inventory/connector/ec2_connector.py
# Lines: 236-239

def list_images(self, **query):
    query = self._generate_query(is_paginate=False, **query)
    response = self.ec2_client.describe_images(**query)
    return response.get('Images', [])
    # Returns: image['Name'] containing 'ubuntu'
```

**Called from:**
```python
# File: src/spaceone/inventory/manager/collector_manager.py
# Line: 75

images = ec2_connector.list_images(ImageIds=self.get_image_ids(instances))
```

**Data Model:**
```python
# File: src/spaceone/inventory/model/os.py
# Line: 6

os_distro = StringType()
```

---

### 7. Primary IP (172.31.7.198)

**UI Display:** "172.31.7.198"

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 70

TextDyField.data_source('Primary IP', 'data.primary_ip_address')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/collector_manager.py
# Lines: 107, 136

instance_ip = instance.get('PrivateIpAddress')
# ...later...
server_data['data'].update({
    'primary_ip_address': instance_ip,
    # ...
})
```

**AWS API:**
- Source: `ec2_connector.py:95-109` → `describe_instances()` → `instance['PrivateIpAddress']`

**Data Model:**
```python
# File: src/spaceone/inventory/model/server.py
# Line: 27

primary_ip_address = StringType(default='')
```

---

### 8. Account ID (565199754239)

**UI Display:** "565199754239"

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 213

TextDyField.data_source('Account ID', 'account')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/collector_manager.py
# Lines: 57, 107, 159

instances, account_id = ec2_connector.list_instances(**instance_filter)
# ...
for reservation in data.get('Reservations', []):
    if account_id == '':
        account_id = reservation.get('OwnerId')  # ← Account ID extracted here
# ...
server_data['account'] = account_id
```

**AWS API:**
```python
# File: src/spaceone/inventory/connector/ec2_connector.py
# Lines: 104-109

for data in response_iterator:
    for reservation in data.get('Reservations', []):
        if account_id == '':
            account_id = reservation.get('OwnerId')  # From describe_instances() response
        ec2_instances.extend(reservation.get('Instances', []))
return ec2_instances, account_id
```

**Data Model:**
```python
# File: src/spaceone/inventory/model/server.py
# Line: 38

account = StringType()
```

---

### 9. Provider (AWS)

**UI Display:** Orange "AWS" badge

**Metadata Definition:**
```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Line: 241

SearchField.set(name='Provider', key='provider', reference='identity.Provider')
```

**Data Collection:**
```python
# File: src/spaceone/inventory/model/server.py
# Line: 43

provider = StringType(default='aws')  # Static default value
```

---

### 10. Region Code (Asia Pacific region)

**UI Display:** Region name (e.g., "ap-southeast-2")

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Lines: 93-98

def get_server_dic(self, instance):
    server_data = {
        'name': self.generate_name(instance),
        'region_code': self.params['region_name'],  # ← From collection parameters
    }
    return server_data
```

**Set in:**
```python
# File: src/spaceone/inventory/manager/collector_manager.py
# Lines: 130

server_data.update({
    'region_code': region_name,  # From params.get("region_name", '')
    # ...
})
```

**Data Model:**
```python
# File: src/spaceone/inventory/model/server.py
# Line: 34

region_code = StringType()
```

---

### 11. Name Field (Empty in screenshot)

**UI Display:** (blank)

**Data Collection:**
```python
# File: src/spaceone/inventory/manager/ec2/ec2_instance_manager.py
# Lines: 221-226

@staticmethod
def generate_name(resource):
    for resource_tag in resource.get('Tags', []):
        if resource_tag['Key'] == "Name":
            return resource_tag["Value"]  # Returns Name tag value or empty string

    return ''  # ← Returns empty if no Name tag exists
```

**AWS API:**
- Source: `ec2_connector.py:95-109` → `describe_instances()` → `instance['Tags']` array

**Data Model:**
```python
# File: src/spaceone/inventory/model/server.py
# Line: 33

name = StringType(default='')
```

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS EC2 API Calls                             │
│  (ec2_connector.py)                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ • describe_instances()        → Instance details, state, type, IPs  │
│ • describe_instance_types()   → Hardware specs (vCPU, memory)       │
│ • describe_images()           → AMI info for OS detection            │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Data Transformation Layer                         │
│  (ec2_instance_manager.py)                                          │
├─────────────────────────────────────────────────────────────────────┤
│ • get_server_info()           → Orchestrates data collection        │
│ • get_compute_data()          → instance_state, instance_type, az   │
│ • get_hardware_data()         → core, memory                         │
│ • get_os_data()               → os_distro, os_type                   │
│ • extract_os_distro()         → Parse AMI name for OS               │
│ • generate_name()             → Extract Name from tags               │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Data Model Validation                             │
│  (compute.py, hardware.py, os.py, server.py)                        │
├─────────────────────────────────────────────────────────────────────┤
│ • Server           → Main resource model                             │
│ • ServerData       → Nested data structure                           │
│ • Compute          → instance_state, instance_type, az              │
│ • Hardware         → core, memory                                    │
│ • OS               → os_distro, os_type, os_arch                    │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Metadata Layer (UI Mapping)                       │
│  (metadata_manager.py)                                              │
├─────────────────────────────────────────────────────────────────────┤
│ • get_cloud_service_type_metadata()                                 │
│   - EnumDyField for Instance State (with color mapping)            │
│   - TextDyField for Instance Type, Core, Memory, AZ, OS, etc.      │
│ • SearchField definitions for filtering                             │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Cloudforet UI Display                          │
│  (Console Frontend)                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Table with columns:                                                  │
│ • Name           → server.name                                       │
│ • Instance State → data.compute.instance_state (with green dot)     │
│ • Instance Type  → data.compute.instance_type                        │
│ • Core          → data.hardware.core                                 │
│ • Memory        → data.hardware.memory                               │
│ • AZ            → data.compute.az                                    │
│ • OS            → data.os.os_distro                                  │
│ • Primary IP    → data.primary_ip_address                            │
│ • Account ID    → account                                            │
│ • Provider      → provider (AWS badge)                               │
│ • Region        → region_code                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Files Reference

### 1. Connector Layer
- **File:** `src/spaceone/inventory/connector/ec2_connector.py`
- **Purpose:** AWS API calls using boto3
- **Key Methods:**
  - `list_instances()` - Lines 95-109
  - `list_instance_types()` - Lines 111-120
  - `list_images()` - Lines 236-239

### 2. Manager Layer
- **File:** `src/spaceone/inventory/manager/ec2/ec2_instance_manager.py`
- **Purpose:** Data transformation and business logic
- **Key Methods:**
  - `get_server_info()` - Lines 16-91
  - `get_compute_data()` - Lines 155-169
  - `get_hardware_data()` - Lines 143-153
  - `get_os_data()` - Lines 100-108
  - `extract_os_distro()` - Lines 237-273
  - `generate_name()` - Lines 221-226

### 3. Collector Manager
- **File:** `src/spaceone/inventory/manager/collector_manager.py`
- **Purpose:** Orchestrates collection process
- **Key Methods:**
  - `list_instances()` - Lines 42-183

### 4. Data Models
- **Files:**
  - `src/spaceone/inventory/model/server.py` - Main Server model
  - `src/spaceone/inventory/model/compute.py` - Compute data model
  - `src/spaceone/inventory/model/hardware.py` - Hardware data model
  - `src/spaceone/inventory/model/os.py` - OS data model

### 5. Metadata Layer
- **File:** `src/spaceone/inventory/manager/metadata/metadata_manager.py`
- **Purpose:** UI field definitions and display configuration
- **Key Methods:**
  - `get_cloud_service_type_metadata()` - Lines 28-257

---

## Color Coding for Instance State

The green indicator for "RUNNING" state is defined in:

```python
# File: src/spaceone/inventory/manager/metadata/metadata_manager.py
# Lines: 31-36

EnumDyField.data_source('Instance State', 'data.compute.instance_state', default_state={
    'safe': ['RUNNING'],           # ← Green dot (color: green.500)
    'warning': ['PENDING', ...],   # ← Yellow dot
    'alert': ['STOPPED', ...],     # ← Red dot
    'disable': ['TERMINATED']      # ← Gray dot with gray text
})
```

The color mapping logic is in:
```python
# File: src/spaceone/inventory/model/metadata/metadata_dynamic_field.py
# Lines: 299-313

for _key in _default_state:
    for _state in _default_state[_key]:
        _state_options = {'icon': {'color': 'gray.400'}}

        if _key == 'safe':
            _state_options = {'icon': {'color': 'green.500'}}  # ← RUNNING gets green
        elif _key == 'warning':
            _state_options = {'icon': {'color': 'yellow.500'}}
        elif _key == 'alert':
            _state_options = {'text_color': 'red.500', 'icon': {'color': 'red.500'}}
```
