# mac-widget

This directory contains a macOS widget architecture for `note-of-the-day`.

It is structured as:

- `Sources/Shared`: payload model + shared storage/network layer.
- `Sources/App`: a small SwiftUI host app for widget settings and manual refresh.
- `Sources/Widget`: WidgetKit extension that renders the desktop/home screen widget.
- `project.yml`: XcodeGen definition to generate the Xcode project.

## What this scaffold does

- Reads your existing API payload from `GET /api/snippet`.
- Shares configuration and cached snippet data through an App Group container.
- Refreshes widget timelines when the host app fetches a new snippet.
- Lets the widget self-refresh on a timeline (~every 30 minutes).

## Setup

1. Install [XcodeGen](https://github.com/yonaskolb/XcodeGen) if needed.
2. From this directory, generate the project:
   - `xcodegen generate`
3. Open `NoteOfTheDayMac.xcodeproj` in Xcode.
4. Replace bundle IDs in `project.yml` with your own IDs.
5. Update App Group ID in all three places so they match:
   - `Sources/Shared/SharedConfig.swift`
   - `Sources/App/NoteOfTheDayMac.entitlements`
   - `Sources/Widget/NoteOfTheDayWidgetExtension.entitlements`
6. In Xcode Signing & Capabilities, ensure:
   - App Sandbox is enabled (host app + widget extension).
   - App Groups includes your shared group.
7. Build and run the host app once, set backend URL (default is `http://127.0.0.1:8000`), then add the widget from macOS widget gallery.

## Notes

- The scaffold allows insecure local HTTP (`localhost`/`127.0.0.1`) for development.
- If you deploy your API remotely, prefer HTTPS and tighten ATS settings in both plist files.
