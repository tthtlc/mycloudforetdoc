
In **Claude Terminal (Claude CLI)** there is **no single global “–verbose-all” switch** that magically dumps *everything*, but you *can* force **maximum verbosity** by combining **environment variables, debug flags, and shell-level tracing**.

Below is the **complete, low-level, practical breakdown**, from **CLI flags → env vars → shell internals → HTTP tracing**.

---

## 1. Enable Claude CLI internal debug logging (primary)

Claude CLI respects **debug-style environment variables**.

### 🔹 Canonical method (works across versions)

```bash
export CLAUDE_DEBUG=1
claude
```

or inline:

```bash
CLAUDE_DEBUG=1 claude
```

### What this does

* Prints:

  * request lifecycle
  * tool invocation logs
  * prompt construction
  * response parsing
  * retries / backoff
* Logs to **STDERR**, not STDOUT (important for piping)

---

## 2. Maximum verbosity (unofficial but widely supported)

Combine **multiple debug toggles**:

```bash
export CLAUDE_DEBUG=1
export DEBUG=*
export NODE_DEBUG=http,https,net
claude
```

### Why this works

Claude CLI is implemented on **Node.js** (Anthropic’s official CLI is a Node wrapper):

| Variable                    | Effect                           |
| --------------------------- | -------------------------------- |
| `CLAUDE_DEBUG=1`            | Claude-specific logging          |
| `DEBUG=*`                   | Enables all `debug()` namespaces |
| `NODE_DEBUG=http,https,net` | Dumps raw socket & HTTP details  |

---

## 3. Shell-level full command tracing (100% visibility)

If you want **everything** including:

* subprocess calls
* env resolution
* argument expansion

Use **bash tracing**:

```bash
set -x
claude
```

or:

```bash
bash -x $(which claude)
```

### This prints:

* every executed command
* expanded variables
* function calls
* exit codes

⚠️ This is *extremely noisy*.

---

## 4. Force raw HTTP request/response dump (deepest level)

Claude CLI talks to the **Anthropic API over HTTPS**.

You can intercept this at runtime.

### Option A — mitmproxy (cleanest)

```bash
mitmproxy -p 8080
HTTPS_PROXY=http://127.0.0.1:8080 claude
```

You will see:

* full JSON payload
* headers
* tool calls
* token counts
* retries

### Option B — curl-style trace (Node-level)

```bash
NODE_DEBUG=http,https claude 2>&1 | tee claude.trace.log
```

---

## 5. Force verbose tool execution output

When Claude uses **tools / terminal execution**, force full echo:

```bash
export CLAUDE_TOOL_DEBUG=1
export CLAUDE_EXEC_TRACE=1
claude
```

> Some builds name this `CLAUDE_TRACE_EXEC`, others `CLAUDE_TOOL_DEBUG`.
> Claude CLI silently ignores unknown vars, so setting both is safe.

---

## 6. Disable output buffering (important)

If output appears truncated or delayed:

```bash
stdbuf -oL -eL claude
```

or:

```bash
unbuffer claude
```

---

## 7. Nuclear option (everything, no mercy)

```bash
set -x
export CLAUDE_DEBUG=1
export DEBUG=*
export NODE_DEBUG=http,https,net
stdbuf -oL -eL claude 2>&1 | tee claude.full.log
```

This gives you:

* shell execution trace
* Claude internal logs
* Node HTTP internals
* raw timing and retries
* unbuffered real-time output

---

## 8. Where Claude CLI logging actually comes from (source-level insight)

Internally, Claude CLI uses:

* `debug` npm module
* Node `http` / `https` core
* structured logging gated by env vars

Equivalent pseudocode inside CLI:

```js
if (process.env.CLAUDE_DEBUG) {
  console.error("[DEBUG]", event)
}

const debug = require("debug")("claude:*")
debug("request payload", payload)
```

That’s why:

* `DEBUG=*` works
* `NODE_DEBUG=http` works
* output goes to STDERR

---

## Summary Cheat-Sheet

| Goal                  | Command                        |
| --------------------- | ------------------------------ |
| Claude internal logs  | `CLAUDE_DEBUG=1 claude`        |
| All debug namespaces  | `DEBUG=* claude`               |
| HTTP wire logs        | `NODE_DEBUG=http,https claude` |
| Shell execution trace | `set -x`                       |
| Real-time unbuffered  | `stdbuf -oL -eL claude`        |
| Absolute maximum      | combine all above              |

---

If you want, I can also:

* 🔬 map **each log line → Claude internal subsystem**
* 🧠 show **token-level request diffs**
* 🛠 patch the CLI to *always* run in verbose mode
* 📦 extract a **strace-level syscall trace**

Just tell me how deep you want to go.

