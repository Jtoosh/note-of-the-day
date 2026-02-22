import Foundation

enum SharedConfig {
    // Replace with your real App Group ID and keep this value in sync with both entitlements files.
    static let appGroupID = "group.com.example.noteoftheday"
    static let apiBaseURLKey = "api_base_url"
    static let cachedSnippetKey = "cached_snippet_payload"
    static let defaultAPIBaseURL = "http://127.0.0.1:8000"

    static var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupID) ?? .standard
    }
}
