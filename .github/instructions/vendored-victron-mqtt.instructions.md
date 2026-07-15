---
applyTo: "custom_components/victron_mqtt/_vendor/**"
---

# Vendored `victron_mqtt` library — do NOT edit here

The code under `custom_components/victron_mqtt/_vendor/` is a **vendored copy** of the
upstream `victron_mqtt` library. It is imported/synced into this repository, not authored here.

## Rules

- Do **NOT** make functional changes, bug fixes, or feature additions to any file under
  `custom_components/victron_mqtt/_vendor/`.
- Any change to the vendored library must be made in the **source `victron_mqtt` repository**,
  then re-vendored/synced into this repo.
- If a problem appears to originate in the vendored code, do not patch it here. Instead:
  1. Point out that the fix belongs in the upstream `victron_mqtt` repo.
  2. Describe the change that would be needed upstream.
  3. Only touch files **outside** `_vendor/` (the Home Assistant integration code) to work
     around or adapt to the vendored library if strictly necessary.
- The only acceptable edits inside `_vendor/` are automated re-sync/vendoring updates that
  replace the directory with a newer upstream snapshot — not hand edits.
