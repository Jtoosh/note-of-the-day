import Foundation

struct SnippetPayload: Codable, Hashable {
    let title: String
    let sourceFile: String
    let breadcrumbs: [String]
    let breadcrumbsText: String
    let text: String
    let continuation: String
    let previousContext: String

    enum CodingKeys: String, CodingKey {
        case title
        case sourceFile = "source_file"
        case breadcrumbs
        case breadcrumbsText = "breadcrumbs_text"
        case text
        case continuation
        case previousContext = "previous_context"
    }
}

extension SnippetPayload {
    static let placeholder = SnippetPayload(
        title: "Note of the Day",
        sourceFile: "example.md",
        breadcrumbs: ["Journal", "Ideas"],
        breadcrumbsText: "Journal > Ideas",
        text: "Set your API URL in the NoteOfTheDayMac app, then refresh to load a live snippet.",
        continuation: "",
        previousContext: ""
    )
}
