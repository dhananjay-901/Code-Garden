#include <bits/stdc++.h>
using namespace std;

// ---------------- CONFIG ----------------
struct Config {
    vector<string> files;
    int topK = 5;
    string indexFile = "index.db";
};

// ---------------- TOKENIZER ----------------
class Tokenizer {
    unordered_set<string> stopWords = {
        "the","is","and","a","an","of","to","in","on","for"
    };

public:
    vector<string> tokenize(const string& text) {
        vector<string> words;
        string word;

        for (char c : text) {
            if (isalpha(c)) word += tolower(c);
            else {
                if (!word.empty() && !stopWords.count(word)) {
                    words.push_back(word);
                }
                word.clear();
            }
        }
        if (!word.empty() && !stopWords.count(word)) words.push_back(word);

        return words;
    }
};

// ---------------- DOCUMENT STORE ----------------
class DocumentStore {
    unordered_map<string, string> contents;

public:
    void load(const vector<string>& files) {
        for (auto& file : files) {
            ifstream f(file);
            if (!f) {
                cerr << "Error opening: " << file << endl;
                continue;
            }
            stringstream buffer;
            buffer << f.rdbuf();
            contents[file] = buffer.str();
        }
    }

    const unordered_map<string, string>& getAll() const {
        return contents;
    }

    const string& get(const string& file) const {
        return contents.at(file);
    }

    int size() const {
        return contents.size();
    }
};

// ---------------- INDEXER ----------------
class Indexer {
    unordered_map<string, unordered_map<string, int>> indexMap;

public:
    void build(const DocumentStore& store, Tokenizer& tokenizer) {
        for (auto& [file, content] : store.getAll()) {
            auto words = tokenizer.tokenize(content);
            for (auto& w : words) {
                indexMap[w][file]++;
            }
        }
    }

    void save(const string& filename) {
        ofstream out(filename);
        for (auto& [word, mp] : indexMap) {
            out << word;
            for (auto& [file, cnt] : mp) {
                out << " " << file << ":" << cnt;
            }
            out << "\n";
        }
    }

    void load(const string& filename) {
        ifstream in(filename);
        if (!in) return;

        string line;
        while (getline(in, line)) {
            stringstream ss(line);
            string word;
            ss >> word;

            string pair;
            while (ss >> pair) {
                int pos = pair.find(":");
                string file = pair.substr(0, pos);
                int count = stoi(pair.substr(pos + 1));
                indexMap[word][file] = count;
            }
        }
    }

    const auto& get() const {
        return indexMap;
    }
};

// ---------------- RANKER ----------------
class Ranker {
public:
    unordered_map<string, double> score(
        const string& query,
        const unordered_map<string, unordered_map<string, int>>& index,
        Tokenizer& tokenizer,
        int totalDocs
    ) {
        unordered_map<string, double> scores;
        auto words = tokenizer.tokenize(query);

        for (auto& w : words) {
            if (!index.count(w)) continue;

            int df = index.at(w).size();
            double idf = log((double)(totalDocs + 1) / (df + 1)) + 1;

            for (auto& [file, tf] : index.at(w)) {
                scores[file] += tf * idf;
            }
        }
        return scores;
    }

    vector<pair<string, double>> topK(unordered_map<string, double>& scores, int k) {
        priority_queue<pair<double, string>> pq;

        for (auto& [file, score] : scores) {
            pq.push({score, file});
        }

        vector<pair<string, double>> res;
        while (!pq.empty() && k--) {
            res.push_back({pq.top().second, pq.top().first});
            pq.pop();
        }
        return res;
    }
};

// ---------------- SNIPPET ----------------
class Snippet {
public:
    string generate(const string& content, const string& query, Tokenizer& tokenizer) {
        string lower = content;
        transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        auto words = tokenizer.tokenize(query);

        size_t pos = string::npos;
        for (auto& w : words) {
            pos = lower.find(w);
            if (pos != string::npos) break;
        }

        if (pos == string::npos) return "No preview";

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

// ---------------- ENGINE ----------------
class SearchEngine {
    Config config;
    DocumentStore store;
    Tokenizer tokenizer;
    Indexer indexer;
    Ranker ranker;
    Snippet snippet;

public:
    void init(Config cfg) {
        config = cfg;

        store.load(config.files);

        ifstream test(config.indexFile);
        if (test.good()) {
            indexer.load(config.indexFile);
        } else {
            indexer.build(store, tokenizer);
            indexer.save(config.indexFile);
        }
    }

    void query(const string& q) {
        auto scores = ranker.score(q, indexer.get(), tokenizer, store.size());
        auto results = ranker.topK(scores, config.topK);

        if (results.empty()) {
            cout << "No results found.\n";
            return;
        }

        cout << "\nResults:\n";
        for (auto& [file, score] : results) {
            cout << file << " (score: " << score << ")\n";
            cout << "→ " << snippet.generate(store.get(file), q, tokenizer) << "\n\n";
        }
    }
};

// ---------------- MAIN ----------------
int main() {
    Config cfg;
    cfg.files = {
        "docs/file1.txt",
        "docs/file2.txt",
        "docs/file3.txt"
    };
    cfg.topK = 3;

    SearchEngine engine;
    engine.init(cfg);

    while (true) {
        cout << "\nSearch (type 'exit'): ";
        string q;
        getline(cin, q);

        if (q == "exit") break;

        engine.query(q);
    }
}