# AI Use Case Version & Override Tracker (POC)

A mini **AI intake governance** tool that lets users:

- Create and edit AI use case records
- Track **full version history**
- Log **metadata overrides** (framework tags, capability groups)
- Comment and collaborate between **submitters** and **admins**

Designed as a standalone POC that can later be **plugged into the OPS AI Intake Tool** (with Entra/Easy Auth and a real database).

---

## ▶️ Live Demo

Once deployed to Streamlit Cloud, add your link here:

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-STREAMLIT-APP-URL)

> 🔒 **Note:** This public demo uses **mock users** and a local SQLite database with **fake sample data only**.  
> No OPS production data, secrets, or internal systems are exposed.

---

## 🧠 Concept

In a typical AI intake process, people submit AI use cases which then go through:

1. Authoring (drafts, edits)
2. Review (architects/admins refine metadata & governance tags)
3. Governance (audit trail, override history, approvals)

This POC focuses on the **governance + auditability** side:

- Every change to a use case creates a **new version**.
- Admins can override auto-generated **AI metadata** (framework tags, capability groups).
- Overrides are tracked separately from the original AI output.
- Comments allow **submitters** and **admins** to discuss changes.

Think of it as a lightweight, Streamlit-based mini “versioned form + review workspace”.

---

## ✨ Features

### 🔐 Roles (mocked for the POC)

- **View Only**
  - Can view records and history
- **User (Submitter)**
  - Can create records
  - Can edit **their own** records
  - Can see comments on their records
- **Admin (OPS Admin / Architect)**
  - Can edit **any** record
  - Can override metadata
  - Can comment on any record
  - Can edit/delete their own comments

> In the real AI Intake Tool, these roles would be driven by **Entra ID / Easy Auth**  
> instead of a dropdown.

---

### 📂 Records & Versions

- Create AI use cases with:
  - Title  
  - Business problem  
  - Description  
  - AI metadata:
    - Framework tags (comma-separated)
    - Capability groups (comma-separated)

- Every edit creates a **`RecordVersion`** entry:
  - `edit` → normal content change  
  - `override` → admin metadata override  
  - All versions are viewable in the **History** tab

---

### 🕒 Version History & Comparison

History page (for a selected record) has:

- **Timeline** tab  
  - List of all versions  
  - Version number, type (`edit` / `override`), author, timestamp

- **Inspect** tab  
  - View a single version’s:
    - Business problem  
    - Description  
    - AI metadata (JSON view)

- **Compare Versions** tab  
  - Pick two versions and see:
    - Changes to **business_problem**  
    - Changes to **description**  
    - Changes to `ai_metadata.framework_tags`  
    - Changes to `ai_metadata.capability_groups`

---

### 🧾 Metadata Overrides (Audit Trail)

When an **Admin** updates the AI metadata:

- The new version is tagged as **`override`**.
- Each changed field (e.g., `ai_metadata.framework_tags`) creates an **OverrideEvent** with:
  - Field path
  - Original value
  - New value
  - Who made the change
  - When it happened (Toronto time)

The **Override History** tab shows a table of all override events for that record.

---

### 💬 Comments

On the **Edit + Comments** tab:

- Threaded comments per record:
  - Each comment shows:
    - Author name
    - Role (USER / ADMIN)
    - Timestamp (Toronto)
    - Text

- Permissions:
  - **Admin**: can comment on any record; can edit/delete their own comments.
  - **User**: can comment on records they can see; can edit/delete their own comments.
  - **Viewer**: read-only; cannot add or modify comments.

This creates a lightweight **review conversation** between submitter and reviewer.

---

## 🧱 Tech Stack

- **Frontend / App Framework:** [Streamlit](https://streamlit.io/)
- **Language:** Python 3.11+
- **Storage:** Local SQLite database (`data/change_tracker.db`)
- **Architecture:**
  - `core/models.py` – dataclasses for `Record`, `RecordVersion`, `Comment`, `OverrideEvent`, `User`
  - `core/repository.py` – simple repository layer for DB CRUD
  - `core/roles.py` – role helper functions
  - `core/auth.py` – mock users for demo
  - `core/styles.py` – dark theme + layout helpers (headers, cards)
  - `app.py` – Streamlit pages: My Records, Editor, History

---

## 📁 Project Structure

```text
.
├─ app.py                     # Streamlit entrypoint
├─ core/
│  ├─ __init__.py
│  ├─ auth.py                 # mock users
│  ├─ models.py               # dataclasses for Records, Versions, Comments, Overrides, Users
│  ├─ repository.py           # SQLite reads/writes & init
│  ├─ roles.py                # role checking helpers
│  └─ styles.py               # dark theme + custom CSS + page header helper
├─ data/
│  └─ change_tracker.db       # local SQLite DB (ignored in Git)
├─ .streamlit/
│  └─ config.toml             # Streamlit config (optional)
├─ requirements.txt
└─ README.md
