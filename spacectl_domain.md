
To list **all domains in Cloudforet using `spacectl`**, you are querying the **Identity service** for the resource **`identity.Domain`**.

Below is the **exact, low-level, end-to-end explanation**, including **CLI**, **gRPC**, and **source-code mapping**, aligned with how Cloudforet actually works internally.

---

## 1️⃣ Prerequisites (important)

### You must:

1. Be authenticated as a **SYSTEM / ROOT user**
2. Have a valid **JWT access token**
3. Have `spacectl` configured to talk to the **identity service**

Check:

```bash
spacectl configure
```

Confirm token exists:

```bash
cat ~/.spacectl/config.yaml
```

You should see:

```yaml
endpoint: grpc://identity:50051
token: eyJhbGciOi...
```

---

## 2️⃣ List all domains (spacectl)

### ✅ Correct command

```bash
spacectl exec list identity.Domain
```

### Example output (trimmed)

```yaml
results:
- domain_id: domain-abc123
  name: Root Domain
  state: ENABLED
  created_at: "2024-01-12T03:21:44Z"
- domain_id: domain-xyz456
  name: Dev Domain
  state: ENABLED
```

### Optional: show as table

```bash
spacectl exec list identity.Domain -o table
```

---

## 3️⃣ Filter fields (jq)

To show only domain IDs and names:

```bash
spacectl exec list identity.Domain -o json \
| jq '.results[] | {domain_id, name, state}'
```

---

## 4️⃣ Why this works (internal mapping)

### spacectl command maps to:

```
spaceone.api.identity.v2.Domain.List
```

### gRPC service

```
identity:50051
```

### Proto definition

📁 **cloudforet/api**

```
proto/spaceone/api/identity/v2/domain.proto
```

```proto
service Domain {
  rpc List (Query) returns (DomainsInfo);
}
```

---

## 5️⃣ Raw gRPC equivalent (grpcurl)

If you want to bypass spacectl:

```bash
grpcurl -plaintext \
  -H "Authorization: Bearer $TOKEN" \
  identity:50051 \
  spaceone.api.identity.v2.Domain/List
```

With query object:

```bash
grpcurl -plaintext \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": {}}' \
  identity:50051 \
  spaceone.api.identity.v2.Domain/List
```

---

## 6️⃣ Where domains are stored (database)

Cloudforet stores domains in **MongoDB**.

### Collection

```
identity_domain
```

### Example document

```json
{
  "domain_id": "domain-abc123",
  "name": "Root Domain",
  "state": "ENABLED",
  "created_at": ISODate("2024-01-12T03:21:44Z")
}
```

---

## 7️⃣ Which pod handles this request?

| Layer       | Component                   |
| ----------- | --------------------------- |
| CLI         | spacectl                    |
| gRPC server | **identity pod**            |
| Service     | `Domain.List()`             |
| DB          | MongoDB (`identity_domain`) |

Pod name:

```bash
kubectl get pods -n cloudforet | grep identity
```

---

## 8️⃣ Common errors & fixes

### ❌ `ERROR_AUTHENTICATE_FAILURE`

Cause:

* Missing or invalid token

Fix:

```bash
spacectl login
```

---

### ❌ Empty results

Cause:

* Logged into a **non-system scope**

Fix:

* Login as root system user
* Domains are **system-level objects**

---

## 9️⃣ Verify permissions (important)

Domains require **SYSTEM role**.

Check roles:

```bash
spacectl exec list identity.Role
```

Check role bindings:

```bash
spacectl exec list identity.RoleBinding
```

---

## 🔟 Summary (one-liner)

```bash
spacectl exec list identity.Domain
```

This:

```
spacectl
 → identity.Domain.List (gRPC)
   → identity service
     → MongoDB identity_domain
       → returns domain list
```

---

If you want next:

* ✅ **Create / delete domains**
* ✅ **Switch domain context**
* ✅ **Map domain → projects → service accounts**
* ✅ **Explain domain_id propagation across all Cloudforet services**

Just tell me.

