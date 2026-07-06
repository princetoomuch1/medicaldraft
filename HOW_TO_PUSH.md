# Push All Projects to GitHub

## Plan
| Folder | Repo | Visibility |
|---|---|---|
| Draft X Trades Old | draft-x-trades-old | PRIVATE |
| Draft X Trading | draftXtrading (exists) | PRIVATE |
| Job Drafts | job-drafts | PRIVATE |
| Medical Draft | medical-draft | PRIVATE |
| Project Draft Portfolio | project-draft-portfolio | PRIVATE |
| gst-invoice-extractor | gst-invoice-extractor | PUBLIC |

Only `gst-invoice-extractor` is public — it has README, Makefile, backend+frontend, looks complete. Rest stay private. Both trading folders private as requested.

## Steps

1. Create a GitHub Personal Access Token
   - Go to https://github.com/settings/tokens
   - Click **Generate new token (classic)**
   - Scope: check **repo** (full control)
   - Generate, copy the token

2. Open PowerShell in this folder
   - Right-click `Draft Projects` folder in File Explorer → **Open in Terminal**
   - Or `cd "C:\Users\artde\OneDrive\Desktop\Draft Projects"`

3. Allow script (one-time)
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

4. Run
   ```powershell
   .\push_all_to_github.ps1
   ```
   Paste token at the prompt (input is hidden). Script does the rest.

## Safety
- `.gitignore` written/updated in each project before commit. Blocks `.env`, `*.key`, `*.pem`, `node_modules`, `__pycache__`, `.venv`, etc.
- Token used only for the session, scrubbed from git remote after push.

## After
Visit https://github.com/princetoomuch1?tab=repositories to verify.
