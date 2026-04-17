class Tokenizer {
private:
    unordered_set<string> stopWords = {
        "the","is","and","a","an","of","to","in","on","for"
    };

public:
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
};

class DocumentStore {
private:
    unordered_map<string, string> files;

public:
    void loadFiles(const vector<string>& filenames) {
        for (const string& file : filenames) {
            ifstream f(file);
            stringstream buffer;
            buffer << f.rdbuf();
            files[file] = buffer.str();
        }
    }

    const unordered_map<string, string>& getAll() const {
        return files;
    }

    const string& getContent(const string& file) const {
        return files.at(file);
    }

    int size() const {
        return files.size();
    }
};

class Indexer {
private:
    unordered_map<string, unordered_map<string, int>> indexMap;

public:
    void buildIndex(const DocumentStore& store, Tokenizer& tokenizer) {
        for (auto& [file, content] : store.getAll()) {
            auto words = tokenizer.tokenize(content);
            for (auto& word : words) {
                indexMap[word][file]++;
            }
        }
    }

    const auto& getIndex() const {
        return indexMap;
    }
};

class Ranker {
public:
    vector<pair<string, double>> rank(
        const string& query,
        const unordered_map<string, unordered_map<string, int>>& index,
        Tokenizer& tokenizer,
        int totalDocs
    ) {
        unordered_map<string, double> scores;
        auto words = tokenizer.tokenize(query);

        for (auto& word : words) {
            if (index.count(word)) {
                int df = index.at(word).size();
                double idf = log((double)(totalDocs + 1) / (df + 1)) + 1;

                for (auto& [file, tf] : index.at(word)) {
                    scores[file] += tf * idf;
                }
            }
        }

        vector<pair<string, double>> results(scores.begin(), scores.end());

        sort(results.begin(), results.end(),
             [](auto& a, auto& b) { return a.second > b.second; });

        return results;
    }
};

class SnippetGenerator {
public:
    string getSnippet(const string& content, const string& query, Tokenizer& tokenizer) {
        string lower = content;
        transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        auto words = tokenizer.tokenize(query);

        size_t pos = string::npos;
        for (auto& w : words) {
            pos = lower.find(w);
            if (pos != string::npos) break;
        }

        if (pos == string::npos) return "No preview available";

        int start = max(0, (int)pos - 20);
        int end = min((int)content.size(), (int)pos + 40);

        string snippet = content.substr(start, end - start);

        for (auto& w : words) {
            size_t p = snippet.find(w);
            if (p != string::npos) {
                snippet.replace(p, w.length(), "[" + w + "]");
            }
        }

        return "..." + snippet + "...";
    }
};

class SearchEngine {
private:
    DocumentStore store;
    Tokenizer tokenizer;
    Indexer indexer;
    Ranker ranker;
    SnippetGenerator snippetGen;

public:
    void init(const vector<string>& files) {
        store.loadFiles(files);
        indexer.buildIndex(store, tokenizer);
    }

    void query(const string& q) {
        auto results = ranker.rank(q, indexer.getIndex(), tokenizer, store.size());

        if (results.empty()) {
            cout << "No results found.\n";
            return;
        }

        for (auto& [file, score] : results) {
            cout << file << " (score: " << score << ")\n";
            cout << "→ " << snippetGen.getSnippet(store.getContent(file), q, tokenizer) << "\n\n";
        }
    }
};

int main() {
    SearchEngine engine;

    vector<string> files = {
        "docs/file1.txt",
        "docs/file2.txt",
        "docs/file3.txt"
    };

    engine.init(files);

    while (true) {
        cout << "\nSearch (type 'exit' to quit): ";
        string query;
        getline(cin, query);

        if (query == "exit") break;

        engine.query(query);
    }
}

