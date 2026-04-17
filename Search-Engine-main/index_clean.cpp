#include <bits/stdc++.h>
using namespace std;

class SearchEngine {
private:
    unordered_map<string, unordered_map<string, int>> indexMap;
    unordered_map<string, string> fileContents;
    unordered_set<string> stopWords = {
        "the","is","and","a","an","of","to","in","on","for"
    };
    int totalDocs = 0;

    // ---------------- TOKENIZE ----------------
    vector<string> tokenize(const string& text) {
        vector<string> words;
        string word;

        for (char c : text) {
            if (isalpha(c)) {
                word += tolower(c);
            } else {
                if (!word.empty()) {
                    if (!stopWords.count(word))
                        words.push_back(word);
                    word.clear();
                }
            }
        }

        if (!word.empty() && !stopWords.count(word))
            words.push_back(word);

        return words;
    }

    // ---------------- FILE READER ----------------
    string readFile(const string& filename) {
        ifstream file(filename);
        stringstream buffer;
        buffer << file.rdbuf();
        return buffer.str();
    }

    // ---------------- INDEX ONE FILE ----------------
    void indexDocument(const string& filename, const string& content) {
        auto words = tokenize(content);
        for (auto& word : words) {
            indexMap[word][filename]++;
        }
    }

    // ---------------- SNIPPET ----------------
    string getSnippet(const string& content, const string& query) {
        string lowerContent = content;
        transform(lowerContent.begin(), lowerContent.end(), lowerContent.begin(), ::tolower);

        vector<string> words = tokenize(query);

        size_t pos = string::npos;
        for (auto& w : words) {
            pos = lowerContent.find(w);
            if (pos != string::npos) break;
        }

        if (pos == string::npos) return "No preview available";

        int start = max(0, (int)pos - 20);
        int end = min((int)content.size(), (int)pos + 40);

        string snippet = content.substr(start, end - start);

        // highlight all words
        for (auto& w : words) {
            size_t p = snippet.find(w);
            if (p != string::npos) {
                snippet.replace(p, w.length(), "[" + w + "]");
            }
        }

        return "..." + snippet + "...";
    }

public:
    // ---------------- BUILD INDEX ----------------
    void indexFiles(const vector<string>& files) {
        totalDocs = files.size();

        for (const string& file : files) {
            string content = readFile(file);
            fileContents[file] = content;
            indexDocument(file, content);
        }
    }

    // ---------------- SEARCH ----------------
    vector<pair<string, double>> search(const string& query) {
        unordered_map<string, double> scores;
        auto queryWords = tokenize(query);

        for (const string& word : queryWords) {
            if (indexMap.count(word)) {
                int df = indexMap[word].size();
                double idf = log((double)(totalDocs + 1) / (df + 1)) + 1;

                for (auto& [file, tf] : indexMap[word]) {
                    scores[file] += tf * idf;
                }
            }
        }

        vector<pair<string, double>> results(scores.begin(), scores.end());

        sort(results.begin(), results.end(),
             [](auto& a, auto& b) { return a.second > b.second; });

        return results;
    }

    // ---------------- DISPLAY ----------------
    void displayResults(const vector<pair<string, double>>& results, const string& query) {
        if (results.empty()) {
            cout << "No results found.\n";
            return;
        }

        cout << "\nResults:\n";

        for (auto& [file, score] : results) {
            cout << file << " (score: " << score << ")\n";
            cout << "→ " << getSnippet(fileContents[file], query) << "\n\n";
        }
    }
};


// ---------------- MAIN ----------------
int main() {
    SearchEngine engine;

    vector<string> files = {
        "docs/file1.txt",
        "docs/file2.txt",
        "docs/file3.txt"
    };

    engine.indexFiles(files);

    cout << "Mini Search Engine (OOP)\n";

    while (true) {
        cout << "\nSearch (type 'exit' to quit): ";
        string query;
        getline(cin, query);

        if (query == "exit") break;

        auto results = engine.search(query);
        engine.displayResults(results, query);
    }

    return 0;
}
