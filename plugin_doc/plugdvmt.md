
Below is a **surgical, code-level guide** to modify **`plugin-azure-inven-collector`** so that **only ONE Azure service is collected**, and that service has **proper Cloudforet metadata (CloudServiceType, labels, tags, region, reference)**.

I’ll assume you want to keep **Azure Virtual Machines** as the single service (the same pattern applies to any other service).

---

## 0. Mental model (important before touching code)

In **Cloudforet inventory plugins**, *collection is split into two layers*:

1. **Collector execution flow**

   * `main.go` → `collector.Collect()` → per-service collectors
2. **Inventory modeling**

   * `CloudServiceType` (schema + metadata)
   * `CloudService` (actual resource instances)

If **either layer is incomplete**, UI breaks:

* “Continue” button greyed out
* No resources visible
* Metadata panel empty

---

## 1. Identify where ALL services are collected

In `plugin-azure-inven-collector`, services are usually wired in **one central place**.

### Locate the service registry

Search for something like:

```bash
grep -R "collectors" -n src
grep -R "Collect(" -n src
```

You’ll typically find a file similar to:

```
src/collector/collector.go
```

### Typical pattern (simplified)

```go
func (c *Collector) Collect(params map[string]interface{}) ([]*inventory.CloudService, error) {
    services := []*inventory.CloudService{}

    services = append(services, compute.CollectVMs(...)...)
    services = append(services, network.CollectVNets(...)...)
    services = append(services, storage.CollectStorageAccounts(...)...)
    services = append(services, database.CollectSQL(...)...)

    return services, nil
}
```

---

## 2. Remove ALL services except ONE (VM example)

### Edit collector entrypoint

**File**

```
src/collector/collector.go
```

### BEFORE

```go
services = append(services, compute.CollectVMs(ctx, clients)...)
services = append(services, network.CollectVNets(ctx, clients)...)
services = append(services, storage.CollectStorageAccounts(ctx, clients)...)
services = append(services, database.CollectSQLServers(ctx, clients)...)
```

### AFTER (keep ONLY VMs)

```go
services = append(services, compute.CollectVMs(ctx, clients)...)
```

✅ At this point:

* Only Azure VMs are collected
* All other services are **completely disabled**

---

## 3. Remove unused imports (mandatory)

Go **will not compile** if imports remain.

### Fix imports

```go
import (
    "plugin-azure-inven-collector/src/collector/compute"
)
```

Remove:

* `network`
* `storage`
* `database`
* any Azure SDK clients not used

---

## 4. Ensure CloudServiceType metadata EXISTS (critical)

Cloudforet UI **requires CloudServiceType** metadata.

### Locate CloudServiceType definitions

Usually in:

```
src/collector/compute/cloud_service_type.go
```

or

```
src/schema/cloud_service_type.go
```

### Correct CloudServiceType for Azure VM

```go
func GetCloudServiceType() *inventory.CloudServiceType {
    return &inventory.CloudServiceType{
        Name:            "VirtualMachine",
        Provider:        "azure",
        Group:           "Compute",
        ServiceCode:     "Microsoft.Compute/virtualMachines",
        IsPrimary:       true,
        IsMajor:         true,
        Labels: []string{
            "Compute",
            "VirtualMachine",
            "Azure",
        },
        Tags: map[string]string{
            "resource_type": "VM",
            "cloud":         "Azure",
        },
        Metadata: inventory.Metadata{
            View: inventory.View{
                Tabs: []inventory.Tab{
                    {
                        Name: "Instance",
                        Items: []inventory.Item{
                            {Key: "data.hardware_profile.vm_size", Name: "VM Size"},
                            {Key: "data.location", Name: "Region"},
                            {Key: "data.provisioning_state", Name: "State"},
                        },
                    },
                },
            },
        },
    }
}
```

🔥 **If Metadata.View is missing → UI breaks**

---

## 5. Register ONLY this CloudServiceType

Look for where service types are registered.

### Typical file

```
src/collector/collector.go
```

or

```
src/main.go
```

### BEFORE

```go
cloudServiceTypes := []*inventory.CloudServiceType{
    compute.GetCloudServiceType(),
    network.GetCloudServiceType(),
    storage.GetCloudServiceType(),
}
```

### AFTER

```go
cloudServiceTypes := []*inventory.CloudServiceType{
    compute.GetCloudServiceType(),
}
```

---

## 6. Validate CloudService object is correct

Inside `CollectVMs()` ensure each resource includes:

```go
cloudService := &inventory.CloudService{
    Name:      vm.Name,
    Provider:  "azure",
    Group:     "Compute",
    Type:      "VirtualMachine",
    RegionCode: vm.Location,
    Data: map[string]interface{}{
        "location": vm.Location,
        "hardware_profile": map[string]interface{}{
            "vm_size": vm.HardwareProfile.VMSize,
        },
        "provisioning_state": *vm.ProvisioningState,
    },
    Reference: inventory.Reference{
        ResourceID: *vm.ID,
        ExternalLink: fmt.Sprintf(
            "https://portal.azure.com/#resource%s",
            *vm.ID,
        ),
    },
}
```

### MUST-HAVE fields

| Field      | Required |
| ---------- | -------- |
| Provider   | ✅        |
| Group      | ✅        |
| Type       | ✅        |
| RegionCode | ✅        |
| Data       | ✅        |
| Reference  | ✅        |

---

## 7. Delete unused CloudServiceType files (optional but clean)

You may safely remove:

```
src/collector/network/
src/collector/storage/
src/collector/database/
```

As long as they’re no longer imported.

---

## 8. Rebuild & test locally

```bash
docker build -t azure-vm-only-collector .
```

Register plugin again in Cloudforet:

```bash
spacectl exec register repository.Plugin -f plugin.yaml
```

Then test collection:

```bash
spacectl exec collect inventory.Collector -f collect.yaml
```

---

## 9. Why this works (root cause explanation)

Cloudforet inventory **expects a 1:1 mapping**:

```
CloudServiceType.Type  == CloudService.Type
```

If you:

* Remove a collector
* But keep its CloudServiceType → UI mismatch
* Keep collector but remove metadata → UI renders nothing

This approach **fully prunes the execution graph**, not just hides services.

---

## 10. Want a minimal “Hello-World Azure Collector”?

If you want, I can:

* Reduce this to **~300 lines total**
* Strip Azure SDK usage
* Return a **single fake VM**
* Perfect for debugging Collector ↔ Inventory flow

Just tell me:
👉 *real Azure VM* or *mock VM only*

