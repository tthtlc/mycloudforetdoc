
Below is a **minimal, mock-only Nutanix VM inventory collector** that is **Cloudforet-correct**, **API-free**, and **UI-safe**.

This is the **Nutanix equivalent** of the Azure mock VM you just approved, adapted to how **Nutanix** resources are normally modeled.

No Prism.
No credentials.
No SDK.
No REST calls.

Just **one fake Nutanix VM** with **correct metadata**, so you can validate the **Inventory → UI → Continue button** pipeline.

---

# 0️⃣ Why Nutanix needs special care (important)

Unlike AWS/Azure, Nutanix:

* Has **no native “region”**
* Uses **clusters** as the primary topology
* VM identity is **UUID-based**
* Console links go to **Prism Central / Prism Element**

So:

* We **map cluster → RegionCode**
* We **model entity as Compute/VirtualMachine**
* We **use Nutanix-style fields (vCPUs, memory, power_state)**

---

# 1️⃣ Minimal directory layout

```
plugin-nutanix-mock-vm/
├── main.go
├── go.mod
├── Dockerfile
└── src/
    ├── collector/
    │   └── collector.go
    └── schema/
        └── vm_type.go
```

---

# 2️⃣ go.mod

```go
module plugin-nutanix-mock-vm

go 1.21

require (
    github.com/cloudforet-io/plugin-sdk-go v1.5.6
)
```

---

# 3️⃣ CloudServiceType (this drives the UI)

📁 `src/schema/vm_type.go`

```go
package schema

import "github.com/cloudforet-io/plugin-sdk-go/core/inventory"

func VMCloudServiceType() *inventory.CloudServiceType {
    return &inventory.CloudServiceType{
        Name:        "VirtualMachine",
        Provider:    "nutanix",
        Group:       "Compute",
        ServiceCode: "Nutanix.AHV/virtualMachines",

        IsPrimary: true,
        IsMajor:   true,

        Labels: []string{
            "Compute",
            "Nutanix",
            "AHV",
            "VM",
        },

        Tags: map[string]string{
            "mock": "true",
            "hypervisor": "ahv",
        },

        Metadata: inventory.Metadata{
            View: inventory.View{
                Tabs: []inventory.Tab{
                    {
                        Name: "Instance",
                        Items: []inventory.Item{
                            {Key: "data.name", Name: "VM Name"},
                            {Key: "data.power_state", Name: "Power State"},
                            {Key: "data.vcpus", Name: "vCPUs"},
                            {Key: "data.memory_mb", Name: "Memory (MB)"},
                            {Key: "data.cluster", Name: "Cluster"},
                        },
                    },
                },
            },
        },
    }
}
```

🔴 If `Metadata.View` is missing → Cloudforet UI silently fails.

---

# 4️⃣ Collector (ONE fake Nutanix VM)

📁 `src/collector/collector.go`

```go
package collector

import (
    "time"

    "github.com/cloudforet-io/plugin-sdk-go/core/inventory"
    "plugin-nutanix-mock-vm/src/schema"
)

func Collect() ([]*inventory.CloudService, []*inventory.CloudServiceType, error) {

    cloudServiceType := schema.VMCloudServiceType()

    vm := &inventory.CloudService{
        Name:     "mock-nutanix-vm-01",
        Provider: "nutanix",
        Group:    "Compute",
        Type:     "VirtualMachine",

        // Nutanix has no region → map cluster name
        RegionCode: "cluster-a",

        Data: map[string]interface{}{
            "name":         "mock-nutanix-vm-01",
            "power_state":  "ON",
            "vcpus":        4,
            "memory_mb":    8192,
            "cluster":      "cluster-a",
            "hypervisor":   "AHV",
        },

        Reference: inventory.Reference{
            ResourceID: "00000000-aaaa-bbbb-cccc-111111111111",
            ExternalLink: "https://prism.local:9440/console/#/vm/00000000-aaaa-bbbb-cccc-111111111111",
        },

        CreatedAt: time.Now(),
    }

    return []*inventory.CloudService{vm}, []*inventory.CloudServiceType{cloudServiceType}, nil
}
```

### Why this passes Cloudforet validation

| Requirement                                  | Satisfied          |
| -------------------------------------------- | ------------------ |
| `CloudServiceType.Name == CloudService.Type` | ✅                  |
| `Provider + Group`                           | ✅                  |
| `RegionCode` present                         | ✅ (cluster-mapped) |
| `Data` non-empty                             | ✅                  |
| `Reference` present                          | ✅                  |
| Metadata schema                              | ✅                  |

---

# 5️⃣ main.go (plugin entrypoint)

📁 `main.go`

```go
package main

import (
    "github.com/cloudforet-io/plugin-sdk-go/core"
    "plugin-nutanix-mock-vm/src/collector"
)

func main() {
    core.Run(&core.RunOptions{
        Collector: collector.Collect,
    })
}
```

---

# 6️⃣ Dockerfile

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .

RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o plugin

FROM alpine:3.19
COPY --from=builder /app/plugin /plugin
ENTRYPOINT ["/plugin"]
```

---

# 7️⃣ Build

```bash
docker build -t nutanix-mock-vm:latest .
```

---

# 8️⃣ Register plugin in Cloudforet

```yaml
# plugin.yaml
name: Nutanix Mock VM Collector
image: nutanix-mock-vm:latest
provider: nutanix
capability:
  supported_schema:
    - inventory.CloudService
    - inventory.CloudServiceType
```

```bash
spacectl exec register repository.Plugin -f plugin.yaml
```

---

# 9️⃣ Expected Cloudforet UI result

* ✅ “Continue” button ENABLED
* ✅ 1 VM shown under Inventory
* ✅ Metadata tab renders cleanly
* ✅ Prism console link clickable
* ✅ No secret / credential required

---

# 🔟 Why this is the **correct Nutanix baseline**

This mirrors **real Nutanix collectors** but removes noise:

```
Real Nutanix plugin
├── Prism auth
├── v3/v4 API pagination
├── entity mapping
└── inventory normalization
```

```
This mock
├── inventory normalization ✅
└── metadata correctness ✅
```

Anything that fails **after this works** is:

* API
* Auth
* Pagination
* Rate limiting
* Field mismatch

—not Cloudforet.

---

## Next logical steps (choose one)

1️⃣ Convert this to **Nutanix v4 real API**
2️⃣ Add **multiple fake clusters**
3️⃣ Add **fake disks / NICs**
4️⃣ Compare with **cloudforet-io/plugin-nutanix-inventory** internals
5️⃣ Trace **server-side validation** in Cloudforet inventory service

Say the number — I’ll go straight there.

