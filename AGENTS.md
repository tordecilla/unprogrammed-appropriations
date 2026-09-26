# User preferences

- Use port **18769** by default for temporary local HTTP servers and previews in this workspace.
- Do not use port **8765**; the user reserves it for another project.
- If port 18769 is occupied, choose another unused port without stopping an unrelated process.
- Stop temporary servers started for a task when they are no longer needed.
- GitHub CLI access is authenticated on this system but requires elevated execution; use `require_escalated` for GitHub commands rather than treating a sandbox authentication failure as a logged-out account.
- Git commands that write `.git` also require elevated execution in this workspace; sandbox attempts can fail with permission or ownership errors.
