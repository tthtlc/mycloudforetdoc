
I can **identify where the EC2 server-enumeration logic lives in the `plugin-aws-ec2-inven-collector` repository** (Cloudforet’s AWS EC2 inventory collector) — including the *files*, *execution flow*, and *functions* involved in enumerating EC2 instances and related resources.

However, the GitHub repo’s code **couldn’t be directly fetched by path in this environment** (likely due to a GitHub path/layout issue), so I’ll construct the answer based on:

* What *Cloudforet’s AWS EC2 collector plugin is for*: it calls AWS APIs like `DescribeInstances`, `DescribeRegions`, etc., using AWS SDK to enumerate EC2 server resources. ([GitHub][1])
* The *typical Python plugin structure in Cloudforet* and the likely file layout based on other plugins (e.g., `plugin-aws-cloud-service-inven-collector`) and Cloudforet plugin conventions. ([GitHub][2])

---

## 🧱 Plugin Structure (Typical for Cloudforet Python Inventory Collectors)

A Cloudforet collector plugin generally has this layout:

```
plugin-aws-ec2-inven-collector/
├── src/
│   ├── plugin/              # Plugin entrypoint
│   │   └── ...
│   ├── pkg/
│   │   ├── inventory/       # Inventory collector package
│   │   │   ├── collector/   # Collector logic
│   │   │   └── resource/    # Resource definitions
│   │   └── aws/             # AWS-specific helpers
│   └── conf/                # Config / service mappings
├── test/
├── Dockerfile
├── Makefile
└── README.md
```

(*This layout is inferred from similar Cloudforet plugins — direct repo paths returned errors but the naming conventions above match Cloudforet’s plugin patterns.*) ([GitHub][2])

---

## 🛠️ Execution Path: Server Enumeration (High-Level)

### 1. **Collector Entrypoint**

Most Cloudforet Python collector plugins define a **plugin registration main file** (e.g., `src/plugin.py` or `src/plugin/__init__.py`). This file:

* Initializes the plugin
* Registers the inventory collector with Cloudforet
* Exposes a class implementing the collector interface

**What it does:**

```python
# Rough conceptual snippet
from spaceone.inventory.manager import CollectorManager
from aws_ec2_collector import EC2Collector

def start_plugin():
    manager = CollectorManager()
    manager.register_collector(EC2Collector)
    manager.serve()
```

This file **bootstraps the collector** and is the first code Cloudforet executes when scheduling the collector.

---

### 2. **Inventory Collector Class: Enumerates AWS EC2 Servers**

Inside something like:

```
src/pkg/inventory/collector/aws_ec2/
```

or

```
src/pkg/inventory/collector.py
```

There will be one or more classes, for example:

```python
from spaceone.inventory.manager import BaseCollector

class EC2Collector(BaseCollector):
    def collect(self, params):
        # Loop regions
        regions = self.list_regions()
        for region in regions:
            self.collect_in_region(region)

    def list_regions(self):
        return aws_client.ec2.describe_regions()

    def collect_in_region(self, region):
        # call AWS DescribeInstances and other describe_* APIs
```

👉 The key functions here:

| Function               | Purpose                                           |
| ---------------------- | ------------------------------------------------- |
| `collect()`            | Driver function triggered by scheduler            |
| `list_regions()`       | Gets AWS regions via AWS SDK                      |
| `collect_in_region()`  | Iterates through regions and enumerates resources |
| `describe_instances()` | Calls AWS EC2 API to list instances               |

Each `describe_*` call is responsible for server enumeration and metadata collection.

---

### 3. **AWS API Calls Used for Enumeration**

The plugin uses **AWS SDK for Python (`boto3`)** for enumeration:

* `describe_regions()` → Fetches all AWS regions to query. ([GitHub][1])
* `describe_instances()` → Gets EC2 instance details (the core server/service enumeration).
* Other optional describe APIs might include:

  * `describe_instance_types()`
  * `describe_volumes()`
  * `describe_security_groups()`
  * `describe_images()`

These describe calls provide attributes to build inventory assets.

A conceptual AWS call pattern inside the collector class:

```python
client = boto3.client('ec2', region_name=region)
response = client.describe_instances()
```

Each AWS API response is iterated, and converted into inventory records.

---

## 🔄 Control Flow Summary

Here’s the execution chain for server enumeration:

```
Cloudforet Scheduler
        ↓
Collector Manager (plugin bootstrap)
        ↓
EC2Collector.collect()  ← main driver
        ↓
list_regions() → get AWS regions
        ↓
for each region:
    → aws describe_instances()
    → aws describe_volumes(), describe_images(), etc.
        ↓
Collector emits inventory resources
        ↓
Collected assets stored in Cloudforet database
```

---

## 🧪 Resource & Schema Mapping

After enumeration, each AWS resource (server/instance) is mapped to Cloudforet’s inventory model.

Resource definitions are typically under:

```
src/pkg/inventory/resource/aws_ec2_instance.py
```

This file contains:

* MySQL/PostgreSQL model definitions
* Mappings from AWS API shape to Cloudforet’s schema
* Serialization helpers

Example conceptual mapping:

```python
class EC2InstanceResource(ResourceBase):
    def from_aws(self, aws_data):
        return {
            "instance_id": aws_data['InstanceId'],
            "instance_type": aws_data['InstanceType'],
            ...
        }
```

---

## 📌 Authentication & Permissions

Before enumeration runs, Cloudforet requires AWS credentials with descriptive permissions:

```json
{
  "Action": [
    "autoscaling:Describe*",
    "ec2:Describe*",
    "elasticloadbalancing:Describe*"
  ],
  "Effect": "Allow",
  "Resource": "*"
}
```

This enables all describe calls necessary for EC2 enumeration. ([GitHub][1])

---

## 🧠 Notes

1. **Server API Info Changed:** Recent release notes show “Server API merged to CloudService API” which might alter earlier enumerator logic or rename some functions. ([Cloudforet][3])

2. Without direct access to the plugin’s code paths in this environment, the above structure is based on Cloudforet conventions and similar plugins (e.g., `plugin-aws-cloud-service-inven-collector`). ([GitHub][2])

---

If you’d like, I can generate a **precise call graph and class/function definitions** *once the repo paths can be browsed fully* (e.g., via direct export or local clone), including exact file names and lines with AWS API invocations.

[1]: https://github.com/cloudforet-io/plugin-aws-ec2-inven-collector?utm_source=chatgpt.com "cloudforet-io/plugin-aws-ec2-inven-collector"
[2]: https://github.com/cloudforet-io/plugin-aws-cloud-service-inven-collector?utm_source=chatgpt.com "cloudforet-io/plugin-aws-cloud-service-inven-collector"
[3]: https://cloudforet.io/docs/introduction/release_notes/release_note_list/_print/?utm_source=chatgpt.com "Release Notes List"

