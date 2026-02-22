import SwiftUI
import WidgetKit

struct NoteWidgetEntry: TimelineEntry {
    let date: Date
    let snippet: SnippetPayload
    let errorMessage: String?
}

struct NoteTimelineProvider: TimelineProvider {
    func placeholder(in context: Context) -> NoteWidgetEntry {
        NoteWidgetEntry(date: Date(), snippet: .placeholder, errorMessage: nil)
    }

    func getSnapshot(in context: Context, completion: @escaping (NoteWidgetEntry) -> Void) {
        let snippet = SnippetStore.loadCachedSnippet() ?? .placeholder
        completion(NoteWidgetEntry(date: Date(), snippet: snippet, errorMessage: nil))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<NoteWidgetEntry>) -> Void) {
        Task {
            let refreshDate = Date().addingTimeInterval(30 * 60)
            do {
                let snippet = try await SnippetStore.fetchLatestSnippet()
                let entry = NoteWidgetEntry(date: Date(), snippet: snippet, errorMessage: nil)
                completion(Timeline(entries: [entry], policy: .after(refreshDate)))
            } catch {
                let fallback = SnippetStore.loadCachedSnippet() ?? .placeholder
                let entry = NoteWidgetEntry(
                    date: Date(),
                    snippet: fallback,
                    errorMessage: error.localizedDescription
                )
                completion(Timeline(entries: [entry], policy: .after(refreshDate)))
            }
        }
    }
}

struct NoteOfTheDayWidgetEntryView: View {
    let entry: NoteWidgetEntry
    @Environment(\.widgetFamily) private var family

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(entry.snippet.title)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundStyle(.secondary)

            Text(entry.snippet.text)
                .font(family == .systemSmall ? .footnote : .body)
                .lineLimit(family == .systemSmall ? 5 : 8)

            if !entry.snippet.continuation.isEmpty {
                Text(entry.snippet.continuation)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            Spacer(minLength: 0)

            Text(entry.snippet.sourceFile)
                .font(.caption2)
                .foregroundStyle(.secondary)

            if let errorMessage = entry.errorMessage {
                Text(errorMessage)
                    .font(.caption2)
                    .foregroundStyle(.orange)
                    .lineLimit(1)
            }
        }
        .padding(12)
        .containerBackground(.fill.tertiary, for: .widget)
    }
}

struct NoteOfTheDayWidget: Widget {
    let kind = "NoteOfTheDayWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: NoteTimelineProvider()) { entry in
            NoteOfTheDayWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("Note of the Day")
        .description("Shows a random snippet from your notes API.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

@main
struct NoteOfTheDayWidgetBundle: WidgetBundle {
    var body: some Widget {
        NoteOfTheDayWidget()
    }
}
