
Below is a **deep, Cloudforet-specific, Kubernetes-level explanation** of how **load balancing works in Cloudforet**, starting from the **UI request path**, down to **Kubernetes Services, controllers, and source-code-level responsibilities**.

---

## 1. High-level view: what “load balancer” means in Cloudforet

Cloudforet itself **does not implement a custom load balancer** in application code.
Instead, it **relies entirely on Kubernetes networking primitives**, plus **Ingress controllers**.

So when we say *“Cloudforet load balancer”*, we are really talking about **three layers**:

1. **Ingress Controller** (Traefik or NGINX)
2. **Kubernetes Service abstraction** (ClusterIP / NodePort / LoadBalancer)
3. **Cloud provider / bare-metal LB implementation** (MetalLB, cloud LB, or K3s service-LB)

---

## 2. Default Cloudforet networking stack (what you usually deploy)

Most Cloudforet Helm installs look like this:

```
[ Browser ]
     |
     |  HTTPS (443)
     v
[ Ingress Controller ]
     |
     |  Service routing
     v
[ Console / Console-API / Identity / Inventory / ... ]
```

### Components involved

| Layer          | Component                 |
| -------------- | ------------------------- |
| External entry | DNS (console.example.com) |
| L7 routing     | **Ingress Controller**    |
| L4 routing     | **Kubernetes Service**    |
| Internal comms | gRPC over ClusterIP       |
| Data           | MongoDB, Redis            |

---

## 3. Ingress Controller (primary “load balancer”)

### Cloudforet officially supports

* **Traefik** (default in many examples, especially K3s)
* **NGINX Ingress Controller** (common in production)

> ⚠️ Cloudforet does **not care** which ingress you use — it only requires standard Kubernetes ingress semantics.

---

### 3.1 Traefik (most common in K3s / local clusters)

K3s ships with **Traefik preinstalled**.

#### Architecture

```
Internet
   |
[ Traefik LoadBalancer Service ]
   |
[ Traefik Pods ]
   |
[ Ingress Rules ]
   |
[ cloudforet-console Service ]
```

#### Typical Traefik service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: traefik
  namespace: kube-system
spec:
  type: LoadBalancer
```

In **K3s**, this LoadBalancer is implemented via:

```
svclb-traefik-xxxxx (DaemonSet)
```

These pods bind host ports directly.

---

### 3.2 NGINX Ingress (production clusters)

```
Internet
   |
[ Cloud LB / MetalLB ]
   |
[ nginx-ingress-controller ]
   |
[ ingress rules ]
```

Used when:

* Running on AWS / GCP / Azure
* Using MetalLB on bare metal

---

## 4. Kubernetes Service types used by Cloudforet

Cloudforet services **never expose themselves directly**.

### 4.1 Internal services (ALL gRPC)

All backend services use:

```yaml
spec:
  type: ClusterIP
```

Examples:

| Service       | Port  |
| ------------- | ----- |
| identity      | 50051 |
| inventory     | 50051 |
| repository    | 50051 |
| secret        | 50051 |
| cost-analysis | 50051 |

These are **NOT externally reachable**.

---

### 4.2 UI & API services

| Service     | Purpose             |
| ----------- | ------------------- |
| console     | React frontend      |
| console-api | REST ↔ gRPC gateway |

These are still **ClusterIP**, but exposed via ingress.

---

## 5. Request flow (browser → inventory → plugin)

Let’s trace a **Server inventory page load** end-to-end.

```
1. Browser
   |
2. https://console.example.com
   |
3. Ingress Controller (Traefik/NGINX)
   |
4. console (React UI)
   |
5. console-api (REST)
   |
6. inventory (gRPC)
   |
7. MongoDB
```

---

## 6. Load balancing behavior (actual mechanics)

### 6.1 Layer 7 (Ingress)

Ingress controller performs:

* Host-based routing
* Path-based routing
* TLS termination
* HTTP load balancing

Example:

```yaml
rules:
- host: console.example.com
  http:
    paths:
    - path: /
      backend:
        service:
          name: console
```

Ingress controller load-balances **across multiple console pods**.

---

### 6.2 Layer 4 (Kubernetes Service)

Each backend Service:

```yaml
spec:
  selector:
    app: inventory
```

Kube-proxy does:

* iptables / IPVS
* Round-robin across pods
* Session-agnostic (stateless)

---

## 7. gRPC load balancing (important detail)

Cloudforet backend communication is **gRPC**.

Key point:

> Cloudforet does **not** use gRPC client-side load balancing.

Instead:

* gRPC client resolves `inventory:50051`
* Kubernetes Service VIP resolves to pod IPs
* kube-proxy distributes traffic

So load balancing is **Kubernetes-native**, not application-level.

---

## 8. Plugin execution is NOT load balanced via ingress

This is a critical distinction.

### Plugin lifecycle

```
Scheduler
  |
Worker Pod
  |
Plugin Pod (on-demand)
```

* Plugin pods are **not behind Services**
* They are executed **directly by worker**
* Communication is **point-to-point gRPC**
* No load balancer involved

This is intentional for:

* Deterministic execution
* Security isolation
* Job traceability

---

## 9. Load balancer implementations by environment

### 9.1 K3s / local lab

| Component   | Implementation |
| ----------- | -------------- |
| LB          | K3s service-lb |
| Ingress     | Traefik        |
| External IP | Node IP        |

---

### 9.2 Bare metal production

| Component | Implementation |
| --------- | -------------- |
| LB        | MetalLB        |
| Ingress   | NGINX          |
| TLS       | cert-manager   |

---

### 9.3 Cloud providers

| Cloud | LB        |
| ----- | --------- |
| AWS   | ALB / NLB |
| GCP   | GCLB      |
| Azure | Azure LB  |

Ingress controller Service becomes:

```yaml
type: LoadBalancer
```

Cloud provider provisions the LB automatically.

---

## 10. Where this is configured in Cloudforet Helm charts

### Key charts

```
charts/
 ├─ traefik/
 ├─ nginx-ingress/
 ├─ console/
 ├─ console-api/
```

Ingress manifests live in:

```
charts/console/templates/ingress.yaml
charts/console-api/templates/ingress.yaml
```

Ingress annotations differ per controller.

---

## 11. Cloudforet code does NOT implement load balancing

Important clarification:

* No round-robin logic in Python/Go code
* No HAProxy / Envoy inside Cloudforet
* No service mesh requirement

All balancing is delegated to Kubernetes.

This is **by design** to:

* Keep services stateless
* Simplify scaling
* Avoid double load balancing

---

## 12. Scaling behavior (what happens when you scale pods)

Example:

```bash
kubectl scale deployment inventory --replicas=5
```

Immediately:

* Service updates endpoints
* kube-proxy updates rules
* Traffic load is distributed

No Cloudforet restart required.

---

## 13. Summary (mental model)

```
Cloudforet does NOT "have a load balancer"

Cloudforet RUNS ON Kubernetes
Kubernetes PROVIDES the load balancer
Ingress CONTROLLERS expose Cloudforet
```

Or visually:

```
[ Kubernetes Networking ]
        ↓
[ Ingress Controller ]
        ↓
[ Service (ClusterIP) ]
        ↓
[ Cloudforet Pods ]
```

---

If you want next, I can:

* Map **exact YAML files** from Cloudforet repo
* Show **Traefik vs NGINX ingress annotations**
* Explain **TLS, cert-manager, and SAN pitfalls**
* Trace **kubectl port-forward vs ingress traffic**
* Design **HA production LB architecture for Cloudforet**

Just tell me which layer you want to go deeper into.

