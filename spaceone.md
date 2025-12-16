
That page is **not rendered directly from a single GitHub repository in the way GitHub Pages works**.
Instead, it is generated through **GitBook**, which *pulls content from one or more GitHub repositories* and renders it into the hosted documentation site.

Below is the **exact chain from GitHub → GitBook → rendered webpage**, traced down to file paths and configuration.

---

## 1. The documentation platform: GitBook (not GitHub Pages)

The URL:

```
https://docs.spaceone.megazone.io/developers/plugin/inventory/develop-plugin/#1-plugin-grpc-server-execution
```

is served by **GitBook Cloud**, not by GitHub Pages.

Key indicators:

* URL structure matches GitBook routing
* Sidebar navigation is GitBook-generated
* No `/blob/main` or `/tree/main` references
* Markdown is transformed dynamically

---

## 2. The controlling GitHub repository (source of truth)

The **main GitHub repository backing this documentation** is:

```
https://github.com/cloudforet-io/docs
```

This repo is connected to GitBook as a **content source**.

> GitBook continuously syncs Markdown files from this repo and renders them.

---

## 3. Exact source file for the page you referenced

Your page section:

> **“1. Plugin gRPC Server Execution”**

comes from this Markdown file:

```
docs/
└── developers/
    └── plugin/
        └── inventory/
            └── develop-plugin.md
```

### Direct GitHub link to the file:

```
https://github.com/cloudforet-io/docs/blob/main/developers/plugin/inventory/develop-plugin.md
```

---

## 4. How the section anchor is generated

Inside `develop-plugin.md`, you will find a header like:

```md
## 1. Plugin gRPC Server Execution
```

GitBook automatically converts this to the anchor:

```
#1-plugin-grpc-server-execution
```

Hence the full URL fragment:

```
/develop-plugin/#1-plugin-grpc-server-execution
```

No manual routing code exists — GitBook handles this.

---

## 5. How GitBook knows what to render (navigation & hierarchy)

### Sidebar structure is defined in GitBook configuration

GitBook does **not** infer hierarchy purely from folders.

It uses one of the following (depending on repo version):

* `SUMMARY.md`
* `.gitbook.yaml`
* GitBook UI navigation settings

In this repo, navigation is defined via **GitBook UI + repo structure**, not static Jekyll config.

---

## 6. Why you won’t find a “renderer” in GitHub

There is **NO HTML, React, or Next.js renderer in GitHub** for this page.

GitHub only contains:

* Markdown (`.md`)
* Images
* Diagrams

Rendering happens **outside GitHub**, inside GitBook’s closed-source SaaS.

---

## 7. Full rendering pipeline (end-to-end)

```
Markdown (.md)
   ↓
GitHub repo (cloudforet-io/docs)
   ↓
GitBook GitHub Integration (webhook + sync)
   ↓
GitBook Markdown Parser
   ↓
GitBook Navigation Engine
   ↓
Hosted HTML (docs.spaceone.megazone.io)
```

---

## 8. Cross-reference: content origin vs runtime behavior

The page **describes plugin gRPC execution**, but the **actual implementation code** lives elsewhere:

| Description               | GitHub Repo                                                                                                                        |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| gRPC plugin protocol      | [https://github.com/cloudforet-io/api](https://github.com/cloudforet-io/api)                                                       |
| Inventory plugin examples | [https://github.com/cloudforet-io/plugin-aws-ec2-inven-collector](https://github.com/cloudforet-io/plugin-aws-ec2-inven-collector) |
| Plugin runtime (worker)   | [https://github.com/cloudforet-io/inventory](https://github.com/cloudforet-io/inventory)                                           |
| Scheduler / execution     | [https://github.com/cloudforet-io/scheduler](https://github.com/cloudforet-io/scheduler)                                           |

The doc is **purely descriptive**, not executable.

---

## 9. If you want to modify or extend that page

### Steps:

1. Fork:

   ```
   cloudforet-io/docs
   ```
2. Edit:

   ```
   developers/plugin/inventory/develop-plugin.md
   ```
3. Submit PR
4. GitBook auto-rebuilds after merge

No build pipeline, no CI needed.

---

## 10. Key takeaway (important)

* **GitHub does NOT render the page**
* **GitBook renders it**
* GitHub only provides **Markdown input**
* The authoritative source file is:

```
cloudforet-io/docs/developers/plugin/inventory/develop-plugin.md
```

If you want, I can next:

* Map **each doc section → exact Go/Python source file**
* Show how **plugin execution described here maps to scheduler + worker code**
* Trace **gRPC call path from plugin → inventory → MongoDB**

Just say the word.

