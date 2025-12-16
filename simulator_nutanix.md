
Here is the **revised, production-grade Cursor prompt**, updated so that **both the server AND the client must be written entirely in Go**.

Paste **everything below** directly into Cursor.

---

# ✅ **CURSOR PROMPT — Build Nutanix Prism V3 Gateway (Go Server + Go Client)**

**TITLE:** Build Nutanix Prism V3 API Gateway — Go Server + Go Client

---

# **OBJECTIVE**

Create a complete Go-based system consisting of:

1. **A Go server** that:

   * Accepts login credentials
   * Authenticates against Nutanix Prism V3 API (`/api/nutanix/v3/users/me`)
   * Issues a **JWT** token
   * Exposes simplified REST endpoints that internally call Prism V3 endpoints:

     * List VMs
     * List Images
     * List Networks
     * List Projects

2. **A Go client** that:

   * Calls the server's `/auth/login`
   * Stores and attaches the JWT
   * Calls `/vms` endpoint
   * Prints formatted output

All components must be built in **Go** with clean modular structure.

Reference API spec:
[https://www.nutanix.dev/api_reference/apis/prism_v3.html](https://www.nutanix.dev/api_reference/apis/prism_v3.html)

---

# ----------------------------------------------------------

# **1. SERVER REQUIREMENTS (Go)**

# ----------------------------------------------------------

## **1.1 Authentication Flow**

The server must expose:

### `POST /auth/login`

**Input:**

```json
{
  "endpoint": "10.10.10.1",
  "username": "admin",
  "password": "nutanix/4u"
}
```

**Server flow:**

1. Validate credentials by forwarding them to:

   ```
   POST https://<endpoint>:9440/api/nutanix/v3/users/me
   Authorization: Basic <base64(username:password)>
   ```

2. If Prism returns valid response:

   * Create a **JWT token** signed using HS256
   * Store user session (endpoint + credentials) in an in-memory map keyed by JWT subject

3. Return JWT + session ID.

---

## **1.2 Protected Resource Endpoints**

All the following endpoints must require JWT bearer authentication.

### `GET /vms`

→ Proxy to Prism V3:

```
POST https://<endpoint>:9440/api/nutanix/v3/vms/list
{
  "kind": "vm",
  "length": 200
}
```

### `GET /images`

→ `/api/nutanix/v3/images/list`

### `GET /networks`

→ `/api/nutanix/v3/subnets/list`

### `GET /projects`

→ `/api/nutanix/v3/projects/list`

---

## **1.3 Technical Specs**

* Language: **Go 1.22+**
* HTTP router: **chi**
* JWT: **golang-jwt/jwt/v5**
* Prism client:

  * `http.Client` with TLS configuration for insecure connections allowed via config
* Timeouts using `context.WithTimeout`
* Structured logging using `log/slog`
* Complete error handling (bad credentials, SSL error, timeout)

---

## **1.4 Project Layout**

Generate a clean modular structure:

```
/cmd/server/main.go
/internal/auth/jwt.go
/internal/nutanix/client.go
/internal/nutanix/models.go
/internal/handlers/auth.go
/internal/handlers/resources.go
/internal/middleware/jwt.go
```

---

# ----------------------------------------------------------

# **2. GO CLIENT REQUIREMENTS**

# ----------------------------------------------------------

Create a standalone Go client CLI program that interacts with the Go server.

### File:

```
/cmd/client/main.go
```

### Client behavior:

1. Prompt or accept flags:

   ```
   --server http://localhost:8080
   --endpoint 192.168.1.20
   --username admin
   --password nutanix/4u
   ```

2. Call:

   ```
   POST /auth/login
   ```

3. Extract JWT from response

4. Call:

   ```
   GET /vms
   Authorization: Bearer <jwt>
   ```

5. Decode JSON list of VMs and print a formatted table:

   * VM Name
   * UUID
   * Power State
   * Host (if available)

6. Add reusable Go module `internal/client/transport.go` if needed.

---

# ----------------------------------------------------------

# **3. CODE GENERATION REQUIREMENTS**

# ----------------------------------------------------------

Cursor must generate:

### For server:

* Full Go implementation for all handlers
* Nutanix Prism V3 API client wrapper
* JWT generation & validation
* Middleware enforcing auth

### For client:

* Full Go CLI program
* Automatic retries on server errors
* Pretty output formatting

---

# ----------------------------------------------------------

# **4. NON-FUNCTIONAL REQUIREMENTS**

# ----------------------------------------------------------

* Include comments referencing documented Prism V3 behaviors.

* Include detailed error messages that match Prism API failures.

* For Prism requests:

  * Always set `"kind": "<resource>"` fields correctly
  * Implement flexible pagination

* Provide:

  * README.md explaining usage
  * Examples:

```
go run cmd/server/main.go
go run cmd/client/main.go --server http://localhost:8080 --endpoint 10.10.10.2 --username admin --password secret
```

---

# ----------------------------------------------------------

# **5. DELIVERABLES Cursor must output**

# ----------------------------------------------------------

### **1. Full Go server code (compilable immediately)**

### **2. Full Go client code (compilable immediately)**

### **3. Example commands + README**

### **4. Documentation describing each package**

---

# ----------------------------------------------------------

# **BEGIN NOW — GENERATE FULL IMPLEMENTATION**

# ----------------------------------------------------------

**END OF PROMPT**

---

If you want, I can now generate the **actual server + client Go code** directly here as well.

