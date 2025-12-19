# Visual Field Trace - From AWS API to UI Display

This document provides a visual trace of how each field flows from the AWS API through the plugin code to the UI display.

---

## Field 1: Instance State (RUNNING with green dot)

```
AWS API Response
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: data['Reservations'][*]['Instances'][*]['State']['Name']
    Value: "running"

         │
         ▼

Data Extraction
├─ File: ec2_instance_manager.py:160
├─ Method: get_compute_data()
├─ Code: instance.get('State', {}).get('Name').upper()
└─ Transformed Value: "RUNNING"

         │
         ▼

Data Model
├─ File: compute.py:12
├─ Field: instance_state
└─ Type: StringType(choices=('PENDING', 'RUNNING', ...))
    Value: "RUNNING"

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:31-36
├─ Field Type: EnumDyField
├─ Display Name: 'Instance State'
├─ Data Path: 'data.compute.instance_state'
└─ Color Mapping:
    • 'safe': ['RUNNING'] → Green dot (color: green.500)
    • 'warning': ['PENDING', ...] → Yellow dot
    • 'alert': ['STOPPED', ...] → Red dot

         │
         ▼

Color Rendering
├─ File: metadata_dynamic_field.py:299-313
├─ Logic: EnumDyField.data_source() color mapping
└─ State Options for 'safe' (RUNNING):
    {'icon': {'color': 'green.500'}}

         │
         ▼

UI Display: ● RUNNING (green circle indicator)
```

---

## Field 2: Instance Type (t2.micro)

```
AWS API Response
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: data['Reservations'][*]['Instances'][*]['InstanceType']
    Value: "t2.micro"

         │
         ▼

Data Extraction
├─ File: ec2_instance_manager.py:161
├─ Method: get_compute_data()
├─ Code: instance.get('InstanceType', '')
└─ Value: "t2.micro"

         │
         ▼

Data Model
├─ File: compute.py:13
├─ Field: instance_type
└─ Type: StringType()
    Value: "t2.micro"

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:38
├─ Field Type: TextDyField
├─ Display Name: 'Instance Type'
└─ Data Path: 'data.compute.instance_type'

         │
         ▼

UI Display: t2.micro
```

---

## Field 3: Core Count (1)

```
AWS API Response (Step 1 - Get Instance Type Name)
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: instance['InstanceType']
    Value: "t2.micro"

         │
         ▼

AWS API Response (Step 2 - Get Hardware Specs)
├─ File: ec2_connector.py:111-120
├─ Method: list_instance_types()
├─ API: describe_instance_types(InstanceTypes=['t2.micro'])
└─ Response Path: data['InstanceTypes'][*]['VCpuInfo']['DefaultVCpus']
    Value: 1

         │
         ▼

Data Extraction
├─ File: ec2_instance_manager.py:143-153
├─ Method: get_hardware_data(instance, itypes)
├─ Code Line 145: itype = self.match_instance_type(instance.get('InstanceType'), itypes)
├─ Code Line 149: itype.get('VCpuInfo', {}).get('DefaultVCpus', 0)
└─ Value: 1

         │
         ▼

Data Model
├─ File: hardware.py:6
├─ Field: core
└─ Type: IntType(default=0)
    Value: 1

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:39
├─ Field Type: TextDyField
├─ Display Name: 'Core'
└─ Data Path: 'data.hardware.core'

         │
         ▼

UI Display: 1
```

---

## Field 4: Memory (1 GB)

```
AWS API Response (Step 1 - Get Instance Type Name)
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: instance['InstanceType']
    Value: "t2.micro"

         │
         ▼

AWS API Response (Step 2 - Get Memory Specs)
├─ File: ec2_connector.py:111-120
├─ Method: list_instance_types()
├─ API: describe_instance_types(InstanceTypes=['t2.micro'])
└─ Response Path: data['InstanceTypes'][*]['MemoryInfo']['SizeInMiB']
    Value: 1024 (MiB)

         │
         ▼

Data Extraction & Conversion
├─ File: ec2_instance_manager.py:150
├─ Method: get_hardware_data()
├─ Code: round(float((itype.get('MemoryInfo', {}).get('SizeInMiB', 0))/1024), 2)
├─ Calculation: 1024 MiB ÷ 1024 = 1.0 GB
└─ Value: 1.0

         │
         ▼

Data Model
├─ File: hardware.py:7
├─ Field: memory
└─ Type: FloatType(default=0.0)
    Value: 1.0

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:40
├─ Field Type: TextDyField
├─ Display Name: 'Memory'
└─ Data Path: 'data.hardware.memory'

         │
         ▼

UI Display: 1
```

---

## Field 5: Availability Zone (ap-southeast-2a)

```
AWS API Response
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: instance['Placement']['AvailabilityZone']
    Value: "ap-southeast-2a"

         │
         ▼

Data Extraction
├─ File: ec2_instance_manager.py:159
├─ Method: get_compute_data()
├─ Code: instance.get('Placement', {}).get('AvailabilityZone', '')
└─ Value: "ap-southeast-2a"

         │
         ▼

Data Model
├─ File: compute.py:11
├─ Field: az
└─ Type: StringType()
    Value: "ap-southeast-2a"

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:53
├─ Field Type: TextDyField
├─ Display Name: 'Availability Zone'
└─ Data Path: 'data.compute.az'

         │
         ▼

UI Display: ap-southeast-2a
```

---

## Field 6: OS Distribution (ubuntu)

```
AWS API Response (Step 1 - Get AMI ID)
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: instance['ImageId']
    Value: "ami-0abc1234..."

         │
         ▼

AWS API Response (Step 2 - Get AMI Details)
├─ File: ec2_connector.py:236-239
├─ Method: list_images(ImageIds=['ami-0abc1234...'])
├─ API: describe_images()
└─ Response Path: data['Images'][0]['Name']
    Value: "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20231201"

         │
         ▼

Image Matching
├─ File: ec2_instance_manager.py:201-206
├─ Method: match_image(image_id, images)
├─ Code: Finds matching image by ImageId
└─ Returns: image object with 'Name' field

         │
         ▼

OS Type Detection
├─ File: ec2_instance_manager.py:229-230
├─ Method: get_os_type(instance)
├─ Code: instance.get('Platform', 'LINUX').upper()
└─ Value: "LINUX" (default if not Windows)

         │
         ▼

OS Distribution Extraction
├─ File: ec2_instance_manager.py:237-253
├─ Method: extract_os_distro(image_name, os_type)
├─ Code:
│   os_map = {
│       'ubuntu': 'ubuntu',  # ← Matches here
│       'amazon': 'amazonlinux',
│       ...
│   }
│   for key in os_map:
│       if key in image_name:  # 'ubuntu' found in AMI name
│           return os_map[key]
└─ Value: "ubuntu"

         │
         ▼

Data Model
├─ File: os.py:6
├─ Field: os_distro
└─ Type: StringType()
    Value: "ubuntu"

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:63
├─ Field Type: TextDyField
├─ Display Name: 'OS'
└─ Data Path: 'data.os.os_distro'

         │
         ▼

UI Display: ubuntu
```

---

## Field 7: Primary IP (172.31.7.198)

```
AWS API Response
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: instance['PrivateIpAddress']
    Value: "172.31.7.198"

         │
         ▼

Data Collection
├─ File: collector_manager.py:107
├─ Code: instance_ip = instance.get('PrivateIpAddress')
└─ Value: "172.31.7.198"

         │
         ▼

Data Assignment
├─ File: collector_manager.py:136
├─ Code:
│   server_data['data'].update({
│       'primary_ip_address': instance_ip,
│       ...
│   })
└─ Value: "172.31.7.198"

         │
         ▼

Data Model
├─ File: server.py:27
├─ Field: primary_ip_address (in ServerData model)
└─ Type: StringType(default='')
    Value: "172.31.7.198"

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:70
├─ Field Type: TextDyField
├─ Display Name: 'Primary IP'
└─ Data Path: 'data.primary_ip_address'

         │
         ▼

UI Display: 172.31.7.198
```

---

## Field 8: Account ID (565199754239)

```
AWS API Response
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: data['Reservations'][*]['OwnerId']
    Value: "565199754239"

         │
         ▼

Account ID Extraction
├─ File: ec2_connector.py:104-109
├─ Code:
│   for reservation in data.get('Reservations', []):
│       if account_id == '':
│           account_id = reservation.get('OwnerId')
└─ Returns: instances, account_id

         │
         ▼

Account ID Assignment (Multiple Locations)
├─ Location 1: collector_manager.py:57
│   instances, account_id = ec2_connector.list_instances(**instance_filter)
│
├─ Location 2: collector_manager.py:158
│   server_data['data']['compute']['account'] = account_id
│
└─ Location 3: collector_manager.py:159
    server_data['account'] = account_id

         │
         ▼

Data Model
├─ File: server.py:38
├─ Field: account
└─ Type: StringType()
    Value: "565199754239"

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:213
├─ Field Type: TextDyField
├─ Display Name: 'Account ID'
└─ Data Path: 'account'

         │
         ▼

UI Display: 565199754239
```

---

## Field 9: Provider Badge (AWS)

```
Static Default Value
├─ File: server.py:43
├─ Field: provider
├─ Type: StringType(default='aws')
└─ Value: "aws"

         │
         ▼

Metadata Definition
├─ File: metadata_manager.py:241
├─ Field Type: SearchField
├─ Display Name: 'Provider'
├─ Data Path: 'provider'
└─ Reference: 'identity.Provider'

         │
         ▼

UI Display: AWS (Orange badge)
```

---

## Field 10: Name (Empty in screenshot)

```
AWS API Response
├─ File: ec2_connector.py:95-109
├─ Method: list_instances()
├─ API: describe_instances()
└─ Response Path: instance['Tags']
    Value: [] or [{"Key": "Name", "Value": "..."}]

         │
         ▼

Name Tag Extraction
├─ File: ec2_instance_manager.py:221-226
├─ Method: generate_name(resource)
├─ Code:
│   for resource_tag in resource.get('Tags', []):
│       if resource_tag['Key'] == "Name":
│           return resource_tag["Value"]
│   return ''  # ← Returns empty if no Name tag
└─ Value: "" (empty string in this case)

         │
         ▼

Data Model
├─ File: server.py:33
├─ Field: name
└─ Type: StringType(default='')
    Value: ""

         │
         ▼

UI Display: (blank/empty cell)
```

---

## Field 11: Region Code

```
Collection Parameters
├─ Source: Job parameters passed to collector
└─ Parameter: params['region_name']
    Value: "ap-southeast-2"

         │
         ▼

Server Data Creation
├─ File: ec2_instance_manager.py:96
├─ Method: get_server_dic()
├─ Code: 'region_code': self.params['region_name']
└─ Value: "ap-southeast-2"

         │
         ▼

Data Update
├─ File: collector_manager.py:130
├─ Code:
│   server_data.update({
│       'region_code': region_name,
│       ...
│   })
└─ Value: "ap-southeast-2"

         │
         ▼

Data Model
├─ File: server.py:34
├─ Field: region_code
└─ Type: StringType()
    Value: "ap-southeast-2"

         │
         ▼

UI Display: Asia Pacific (ap-southeast-2) → Shown as "Asia..." (truncated)
```

---

## Complete Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        AWS EC2 API                                │
│                     (boto3 SDK calls)                             │
└────────────┬─────────────────────────────────────────────────────┘
             │
             │ ec2_connector.py:
             │ • list_instances() → describe_instances()
             │ • list_instance_types() → describe_instance_types()
             │ • list_images() → describe_images()
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ec2_instance_manager.py                        │
│                  (Data Transformation Layer)                      │
├──────────────────────────────────────────────────────────────────┤
│ get_server_info()                                                │
│  ├─ get_compute_data()     → instance_state, instance_type, az   │
│  ├─ get_hardware_data()    → core, memory                        │
│  ├─ get_os_data()          → os_distro                           │
│  └─ generate_name()        → name from tags                      │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    collector_manager.py                           │
│                 (Collection Orchestration)                        │
├──────────────────────────────────────────────────────────────────┤
│ list_instances()                                                 │
│  • Calls EC2InstanceManager                                      │
│  • Enriches with VPC, subnet, disk, NIC data                     │
│  • Assigns account ID, region_code, primary_ip_address          │
│  • Adds metadata reference                                       │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Data Models                                 │
│          (compute.py, hardware.py, os.py, server.py)             │
├──────────────────────────────────────────────────────────────────┤
│ Server(                                                          │
│   name: "",                                                      │
│   region_code: "ap-southeast-2",                                │
│   account: "565199754239",                                       │
│   provider: "aws",                                               │
│   cloud_service_type: "Instance",                               │
│   cloud_service_group: "EC2",                                   │
│   data: ServerData(                                              │
│     compute: Compute(                                            │
│       instance_state: "RUNNING",                                 │
│       instance_type: "t2.micro",                                 │
│       az: "ap-southeast-2a"                                      │
│     ),                                                           │
│     hardware: Hardware(                                          │
│       core: 1,                                                   │
│       memory: 1.0                                                │
│     ),                                                           │
│     os: OS(                                                      │
│       os_distro: "ubuntu"                                        │
│     ),                                                           │
│     primary_ip_address: "172.31.7.198"                          │
│   )                                                              │
│ )                                                                │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    metadata_manager.py                            │
│                   (UI Field Definitions)                          │
├──────────────────────────────────────────────────────────────────┤
│ get_cloud_service_type_metadata()                                │
│  • EnumDyField('Instance State', 'data.compute.instance_state')  │
│  • TextDyField('Instance Type', 'data.compute.instance_type')    │
│  • TextDyField('Core', 'data.hardware.core')                     │
│  • TextDyField('Memory', 'data.hardware.memory')                 │
│  • TextDyField('Availability Zone', 'data.compute.az')           │
│  • TextDyField('OS', 'data.os.os_distro')                        │
│  • TextDyField('Primary IP', 'data.primary_ip_address')          │
│  • TextDyField('Account ID', 'account')                          │
└────────────┬─────────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Cloudforet Console UI                           │
│                     (Frontend Display)                            │
├──────────────────────────────────────────────────────────────────┤
│ ┌─────┬──────────────┬──────────┬──────┬────────┬──────────┐    │
│ │Name │Instance State│  Type    │ Core │ Memory │    AZ    │... │
│ ├─────┼──────────────┼──────────┼──────┼────────┼──────────┤    │
│ │     │ ● RUNNING    │ t2.micro │  1   │   1    │ap-sou... │... │
│ └─────┴──────────────┴──────────┴──────┴────────┴──────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Summary Table: Line Number References

| UI Field | Connector | Manager | Model | Metadata |
|----------|-----------|---------|-------|----------|
| Instance State | `ec2_connector.py:95-109` | `ec2_instance_manager.py:160` | `compute.py:12` | `metadata_manager.py:31-36` |
| Instance Type | `ec2_connector.py:95-109` | `ec2_instance_manager.py:161` | `compute.py:13` | `metadata_manager.py:38` |
| Core | `ec2_connector.py:111-120` | `ec2_instance_manager.py:149` | `hardware.py:6` | `metadata_manager.py:39` |
| Memory | `ec2_connector.py:111-120` | `ec2_instance_manager.py:150` | `hardware.py:7` | `metadata_manager.py:40` |
| Availability Zone | `ec2_connector.py:95-109` | `ec2_instance_manager.py:159` | `compute.py:11` | `metadata_manager.py:53` |
| OS Distribution | `ec2_connector.py:236-239` | `ec2_instance_manager.py:237-253` | `os.py:6` | `metadata_manager.py:63` |
| Primary IP | `ec2_connector.py:95-109` | `collector_manager.py:107,136` | `server.py:27` | `metadata_manager.py:70` |
| Account ID | `ec2_connector.py:107` | `collector_manager.py:159` | `server.py:38` | `metadata_manager.py:213` |
| Provider | N/A (static) | N/A | `server.py:43` | `metadata_manager.py:241` |
| Name | `ec2_connector.py:95-109` | `ec2_instance_manager.py:221-226` | `server.py:33` | N/A (default field) |
| Region Code | N/A (param) | `ec2_instance_manager.py:96` | `server.py:34` | N/A |
