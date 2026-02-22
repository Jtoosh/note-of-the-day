import SwiftUI
import WidgetKit

struct ContentView: View {
    @State private var apiBaseURL = SnippetStore.currentBaseURLString()
    @State private var cachedSnippet = SnippetStore.loadCachedSnippet()
    @State private var statusMessage = "Configure backend URL and refresh to feed the widget."
    @State private var isRefreshing = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Note of the Day Widget")
                .font(.title2)
                .fontWeight(.semibold)

            VStack(alignment: .leading, spacing: 8) {
                Text("Backend API URL")
                    .font(.headline)

                TextField("http://127.0.0.1:8000", text: $apiBaseURL)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit(saveURL)

                Text("Expected endpoint: /api/snippet")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 10) {
                Button("Save URL", action: saveURL)
                Button(isRefreshing ? "Refreshing..." : "Refresh Snippet") {
                    refreshSnippet()
                }
                .disabled(isRefreshing)
            }

            Text(statusMessage)
                .font(.callout)
                .foregroundStyle(.secondary)

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("Cached snippet used by widget")
                    .font(.headline)

                if let snippet = cachedSnippet {
                    Text(snippet.title)
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Text(snippet.text)
                        .lineLimit(5)
                    Text(snippet.sourceFile)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    Text("No cached snippet yet.")
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()
        }
        .padding(24)
    }

    private func saveURL() {
        SnippetStore.setBaseURLString(apiBaseURL)
        apiBaseURL = SnippetStore.currentBaseURLString()
        statusMessage = "Saved API URL."
    }

    private func refreshSnippet() {
        saveURL()
        isRefreshing = true
        statusMessage = "Fetching snippet..."

        Task {
            do {
                let snippet = try await SnippetStore.fetchLatestSnippet(from: apiBaseURL)
                await MainActor.run {
                    cachedSnippet = snippet
                    statusMessage = "Updated at \(Self.timestampFormatter.string(from: Date()))."
                    isRefreshing = false
                }
                WidgetCenter.shared.reloadAllTimelines()
            } catch {
                await MainActor.run {
                    statusMessage = error.localizedDescription
                    isRefreshing = false
                }
            }
        }
    }
}

private extension ContentView {
    static let timestampFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }()
}
