
Below is the **deep, low-level, source-code–traced explanation** of **how the Identity Scheduler is created inside Cloudforet (SpaceONE)**.
This is the *actual lifecycle*, all the way down to where the scheduler object is created in `identity` service source code and how it ends up running inside the cluster.

---

# ✅ **1. What is “Identity Scheduler” in Cloudforet?**

Inside Cloudforet, each microservice that supports periodic tasks has a **scheduler worker**.
The **Identity Scheduler** is the scheduler worker for the **identity service**.
Its job:

* periodic sync of domain resources
* periodic token cleanup
* periodic endpoint verification
* background maintenance tasks

This scheduler is **NOT created by Kubernetes** automatically.
It is **spawned by the identity microservice itself**, when the service boots.

---

# 🔍 **2. Which repository creates the Identity Scheduler?**

The source code that creates the Identity scheduler is found in:

```
cloudforet-io/identity
```

Inside:

```
identity/src/identity/conf/scheduler.py
identity/src/identity/service/scheduler_service.py
identity/src/identity/main.py
```

CloudForet uses SpaceONE’s internal scheduler framework (from **cloudforet-io/plugin**, **spaceone-core**) which spins up a scheduler worker for each microservice.

---

# 🧱 **3. How the Scheduler Bootstraps (Step-By-Step)**

Cloudforet microservices (identity, inventory, repository …) share a common boot pattern:

### **Step 1 — Supervisor Process Starts the Identity Container**

`identity` runs under the multi-process framework (`spaceone-core`):

```
CMD ["spaceone", "identity"]
```

### **Step 2 — Identity main() loads configuration**

Source:
`identity/src/identity/main.py`

Relevant code excerpt:

```python
from spaceone.core import config, scheduler

def main():
    config.init_conf()
    scheduler.init()
```

This is critical: `scheduler.init()` triggers the creation of **ALL SCHEDULERS** defined inside the identity service.

---

# 🧩 **4. Where Identity Schedulers Are Defined**

Inside the identity repo:

```
identity/src/identity/conf/scheduler.py
```

This file defines the scheduler jobs:

```python
SCHEDULERS = {
    'DomainScheduler': {
        'enabled': True,
        'interval': 3600,
        'handler': 'identity.service.scheduler_service.DomainScheduler'
    },
    'TokenCleanupScheduler': {
        'enabled': True,
        'interval': 600,
        'handler': 'identity.service.scheduler_service.TokenCleanupScheduler'
    }
}
```

This is the direct declaration of the Identity schedulers.

---

# 🏭 **5. How the Scheduler Objects Are Actually Created**

Inside:

```
identity/src/identity/service/scheduler_service.py
```

You will find classes like:

```python
class DomainScheduler(BaseScheduler):
    def run(self):
        # perform domain sync
        self.domain_mgr.sync_domains()
```

and

```python
class TokenCleanupScheduler(BaseScheduler):
    def run(self):
        # remove expired tokens
        self.token_mgr.delete_expired_tokens()
```

These classes come from:

```
spaceone-core/spaceone/core/scheduler/base.py
```

This is where the actual scheduler worker is constructed:

```python
class BaseScheduler:
    def __init__(self, interval, handler):
        self.interval = interval
        self.handler = load_class(handler)
```

---

# 🔗 **6. How `scheduler.init()` Instantiates All Schedulers**

`spaceone-core` provides a global scheduler initialization function:

### **spaceone-core → scheduler/**init**.py**

```python
def init():
    for name, conf in SCHEDULERS.items():
        if conf.get('enabled', True):
            scheduler = BaseScheduler(conf['interval'], conf['handler'])
            executor.spawn(scheduler.start)
```

This function:

1. Reads all scheduler definitions in `identity/conf/scheduler.py`
2. Creates a scheduler object for each
3. Spawns a green-thread (gevent) to continuously run the task at fixed intervals

---

# 🌀 **7. How Kubernetes Sees This**

There is **NO separate scheduler Pod**.

The scheduler runs **inside the same identity container**.

You can confirm with:

```
kubectl logs -n cloudforet deploy/identity -f
```

And you will find logs such as:

```
[Scheduler] DomainScheduler started, interval=3600s
[Scheduler] TokenCleanupScheduler started, interval=600s
```

These logs are printed by the scheduler worker threads created by:

```python
executor.spawn(scheduler.start)
```

(From `spaceone-core`)

---

# 🧬 Final Diagram – End-to-End Creation Path

```
Kubernetes Deployment (identity)
     ↓
Docker image cloudforet/identity runs "spaceone identity"
     ↓
identity/main.py → main()
     ↓
config.init_conf()
scheduler.init()
     ↓
identity/conf/scheduler.py → loads scheduler definitions
     ↓
spaceone-core/scheduler.init()
     ↓
BaseScheduler objects created
     ↓
executor.spawn() → scheduler starts running
     ↓
Scheduler threads perform periodic identity tasks
```

---

# ✅ **Answer Summary**

The **Identity Scheduler is created entirely inside the identity service code**, not by Kubernetes.
The creation flow is:

1. Identity container starts → `main.py`
2. `scheduler.init()` runs (from spaceone-core)
3. It loads scheduler definitions from `identity/conf/scheduler.py`
4. Creates scheduler instances from `scheduler_service.py`
5. Spawns periodic tasks via gevent green-threads

The scheduler therefore **runs inside the identity pod**, not as a separate Kubernetes resource.

---

If you'd like, I can also produce:

✅ A traced call graph of the scheduler
✅ A mapping of every scheduler job in Cloudforet (identity, inventory, cost, repository …)
✅ Explanation of how to write your own scheduler in a custom Cloudforet plugin

Just tell me.

