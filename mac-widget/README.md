# mac-widget

This directory contains a macOS app + widget scaffold for `note-of-the-day`.

The project is split into:

- `Sources/Shared`: shared payload model, storage, and API client.
- `Sources/App`: host macOS SwiftUI app (set API URL and trigger refresh).
- `Sources/Widget`: WidgetKit extension shown on desktop / Notification Center.
- `project.yml`: source-of-truth config used by XcodeGen to create the Xcode project.

## What this scaffold does

- Calls `GET /api/snippet` (same payload as your web frontend).
- Caches the latest snippet in shared App Group storage.
- Lets the host app force-refresh widget timelines.
- Lets the widget self-refresh on a timeline (about every 30 minutes).

## Prerequisites

1. Install Xcode from the Mac App Store.
2. Open Xcode once and accept license/components setup.
3. Make sure Command Line Tools are selected:
   - Xcode -> Settings -> Locations -> Command Line Tools.
4. Install XcodeGen:
   - `brew install xcodegen`
5. Make sure your backend API is runnable locally (default expected URL is `http://127.0.0.1:8000`).

## 1) Generate the Xcode project

From this folder:

```bash
cd /Users/james/Projects/Personal/code/note-of-the-day/mac-widget
xcodegen generate
```

This creates `NoteOfTheDayMac.xcodeproj`.

Important: if you edit `project.yml`, run `xcodegen generate` again to sync changes into the `.xcodeproj`.

## 2) Open project and understand targets

Open `NoteOfTheDayMac.xcodeproj` in Xcode. You will see two targets:

- `NoteOfTheDayMac`: the host desktop app.
- `NoteOfTheDayWidgetExtension`: the widget extension.

The app and widget must both build successfully; they share code in `Sources/Shared`.

## 3) Configure bundle IDs

In `project.yml`, replace example bundle IDs with your own unique IDs:

- `com.example.NoteOfTheDayMac`
- `com.example.NoteOfTheDayMac.WidgetExtension`

Then regenerate:

```bash
xcodegen generate
```

Rule of thumb:

- Use reverse-DNS style IDs you control (`com.yourname.noteoftheday`).
- App and extension IDs must be unique.

## 4) Configure App Group (required for shared data)

Choose one App Group ID (must start with `group.`), for example:

- `group.com.yourname.noteoftheday`

Use this exact value in all three files:

- `Sources/Shared/SharedConfig.swift` (`appGroupID`)
- `Sources/App/NoteOfTheDayMac.entitlements`
- `Sources/Widget/NoteOfTheDayWidgetExtension.entitlements`

If these values differ, the widget and app will not share cached snippet data.

## 5) Configure signing and capabilities in Xcode

For **each target** (`NoteOfTheDayMac` and `NoteOfTheDayWidgetExtension`):

1. Select target -> `Signing & Capabilities`.
2. Choose your Team (Apple ID / Developer team).
3. Ensure `Automatically manage signing` is enabled (recommended while setting up).
4. Confirm capabilities:
   - `App Sandbox` enabled.
   - `App Groups` enabled with the exact App Group ID from step 4.
   - Network client enabled in entitlements (already present in scaffold).

If Xcode shows capability/signing warnings, resolve those before running.

## 6) Run backend and verify API first

In your project root (not `mac-widget`), run backend:

```bash
cd /Users/james/Projects/Personal/code/note-of-the-day
.venv/bin/python -m uvicorn server.app:app --reload --port 8000
```

Quick check:

```bash
curl http://127.0.0.1:8000/api/snippet
```

If this fails, fix backend first; widget depends on this endpoint.

## 7) Build and run the host app

1. Back in Xcode, select scheme `NoteOfTheDayMac`.
2. Press Run.
3. In the app window:
   - Set API URL (default is `http://127.0.0.1:8000`).
   - Click `Save URL`.
   - Click `Refresh Snippet`.

You should see status updates and cached snippet content in the app UI.

## 8) Add widget to macOS desktop/home screen

1. On macOS desktop, open widget gallery (`Edit Widgets`).
2. Find `Note of the Day`.
3. Add the widget (small/medium/large).
4. The widget should display cached content immediately and continue refreshing.

If needed, open the host app and click `Refresh Snippet` to force a fresh payload.

## Troubleshooting

- Widget shows placeholder only:
  - Confirm backend is running and `/api/snippet` returns JSON.
  - Confirm App Group ID matches across shared config + both entitlements + Xcode capability.
- Build fails with signing/provisioning errors:
  - Recheck Team selection and unique bundle IDs.
  - Keep automatic signing enabled until stable.
- Widget does not update after refresh:
  - Confirm host app successfully fetched data.
  - Check that `WidgetCenter.shared.reloadAllTimelines()` was reached (status message updates in app).
- HTTP blocked errors:
  - Localhost exceptions are preconfigured in plist files.
  - For remote endpoints, prefer HTTPS and tighten ATS rules.

## Development notes

- ATS currently allows insecure local HTTP for `localhost` and `127.0.0.1`.
- For production, use HTTPS and remove broad local exceptions where possible.
- `project.yml` is the canonical project config; avoid manual drift in the generated `.xcodeproj`.
