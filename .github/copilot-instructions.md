# Copilot instructions for `ha-victron-mqtt`

This is a Home Assistant custom integration that wraps the `victron_mqtt` library.

## Workflow — things NOT to do

- **Never commit or push before the user reviews.** Do not run `git commit`, `git push`,
  create tags, or open PRs unless the user has explicitly reviewed the change and asked you to.
  Make the edits and stop so they can review.
- **Do not skip verification checks** (`--no-verify`, `commit skip checks`, etc.) unless the
  user explicitly asks for it.
- **Do not perform hard-to-reverse git actions** (force-push, `reset --hard`, amending pushed
  commits, deleting branches/tags) without explicit confirmation.

## Vendored `victron_mqtt` library

- Code under `custom_components/victron_mqtt/_vendor/` is a **vendored copy** of the upstream
  `victron_mqtt` repo. **Do not make functional changes here.**
- Fixes and features for that library belong in the **source `victron_mqtt` repository**, then
  get re-vendored/synced into this repo (typically via an "Update victron_mqtt to X" commit).
- Only touch integration code **outside** `_vendor/` to adapt to the library.
- (A scoped rule in `.github/instructions/vendored-victron-mqtt.instructions.md` enforces this
  when editing files under `_vendor/`.)

## Tests

- **Tests only run on Linux or in the devcontainer**, where the Home Assistant dependencies can
  be installed. **When working from Windows, skip running the tests** — the HA dependencies
  cannot be installed there. Do not attempt to run the suite on Windows.
- **Do not reintroduce snapshot tests.** Snapshots were intentionally removed because they keep
  breaking with Home Assistant core changes. Prefer behavior-based tests.
- On Linux/devcontainer, run the test suite and make sure it passes before declaring work done,
  but still do not commit without review.

## Versioning & releases

- The integration version lives in `custom_components/victron_mqtt/manifest.json` and follows a
  calendar pattern (`YYYY.M.P`, e.g. `2026.7.3`).
- Version bumps are a **separate, user-initiated step** ("Bump version to ...") — do not bump the
  version as part of unrelated changes unless asked.

## Deployment

- Deploying to a live Home Assistant instance is done via the provided VS Code tasks
  ("Deploy to Home Assistant to container" / "...to test environment", which `scp` the
  `custom_components/victron_mqtt/` folder). Do not invent alternative deploy mechanisms.
