import Foundation

enum SnippetStoreError: LocalizedError {
    case invalidBaseURL(String)
    case invalidResponse
    case httpStatus(Int)
    case decodeFailed

    var errorDescription: String? {
        switch self {
        case .invalidBaseURL(let value):
            return "Invalid API URL: \(value)"
        case .invalidResponse:
            return "Received an invalid response from the API."
        case .httpStatus(let status):
            return "API request failed with status \(status)."
        case .decodeFailed:
            return "Could not decode snippet payload."
        }
    }
}

enum SnippetStore {
    static func currentBaseURLString() -> String {
        let defaults = SharedConfig.defaults
        return defaults.string(forKey: SharedConfig.apiBaseURLKey) ?? SharedConfig.defaultAPIBaseURL
    }

    static func setBaseURLString(_ value: String) {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        let defaults = SharedConfig.defaults
        defaults.set(trimmed.isEmpty ? SharedConfig.defaultAPIBaseURL : trimmed, forKey: SharedConfig.apiBaseURLKey)
    }

    static func fetchLatestSnippet(from baseURLString: String? = nil, session: URLSession = .shared) async throws -> SnippetPayload {
        let configured = (baseURLString?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false)
            ? baseURLString!
            : currentBaseURLString()

        guard let baseURL = URL(string: configured) else {
            throw SnippetStoreError.invalidBaseURL(configured)
        }

        let endpoint = baseURL
            .appendingPathComponent("api")
            .appendingPathComponent("snippet")

        var request = URLRequest(url: endpoint)
        request.timeoutInterval = 12

        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw SnippetStoreError.invalidResponse
        }
        guard (200 ... 299).contains(httpResponse.statusCode) else {
            throw SnippetStoreError.httpStatus(httpResponse.statusCode)
        }

        do {
            let payload = try JSONDecoder().decode(SnippetPayload.self, from: data)
            saveCachedSnippet(payload)
            return payload
        } catch {
            throw SnippetStoreError.decodeFailed
        }
    }

    static func loadCachedSnippet() -> SnippetPayload? {
        let defaults = SharedConfig.defaults
        guard let data = defaults.data(forKey: SharedConfig.cachedSnippetKey) else {
            return nil
        }
        return try? JSONDecoder().decode(SnippetPayload.self, from: data)
    }

    static func saveCachedSnippet(_ payload: SnippetPayload) {
        guard let encoded = try? JSONEncoder().encode(payload) else {
            return
        }
        let defaults = SharedConfig.defaults
        defaults.set(encoded, forKey: SharedConfig.cachedSnippetKey)
    }
}
