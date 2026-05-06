#include <bits/stdc++.h>
using namespace std;

/* ========================= TOKENIZER ========================= */
class Tokenizer {
public:
    static string normalize(const string &word) {
        string clean;
        for (char c : word) {
            if (isalnum(c)) clean += tolower(c);
        }
        return clean;
    }

    static vector<string> tokenize(const string &text) {
        vector<string> tokens;
        stringstream ss(text);
        string word;

        while (ss >> word) {
            word = normalize(word);
            if (!word.empty()) tokens.push_back(word);
        }
        return tokens;
    }
};

/* ========================= DOCUMENT LOADER ========================= */
class DocumentLoader {
public:
    unordered_map<string, string> contents;

    void load(const vector<string> &files) {
        for (auto &f : files) {
            ifstream in(f);
            if (!in) {
                cerr << "Error opening: " << f << endl;
                continue;
            }
            stringstream buffer;
            buffer << in.rdbuf();
            contents[f] = buffer.str();
        }

        if (contents.empty()) {
            cerr << "No documents loaded!\n";
            exit(1);
        }
    }
};

/* ========================= INVERTED INDEX ========================= */
class InvertedIndex {
public:
    unordered_map<string, unordered_map<string, double>> index;
    int totalDocs = 0;

    void build(const unordered_map<string, string> &docs) {
        totalDocs = docs.size();

        for (auto &[doc, text] : docs) {
            auto tokens = Tokenizer::tokenize(text);

            unordered_map<string, int> freq;
            for (auto &t : tokens) freq[t]++;

            for (auto &[word, count] : freq) {
                double tf = (double)count / tokens.size();
                index[word][doc] = tf;
            }
        }
    }
};

/* ========================= TF-IDF SCORER ========================= */
class TFIDFScorer {
public:
    static unordered_map<string, double> score(
        const string &query,
        InvertedIndex &idx
    ) {
        unordered_map<string, double> scores;
        auto terms = Tokenizer::tokenize(query);

        for (auto &term : terms) {
            if (idx.index.find(term) == idx.index.end()) continue;

            int df = idx.index[term].size();
            double idf = log((idx.totalDocs + 1.0) / (df + 1.0)) + 1;

            for (auto &[doc, tf] : idx.index[term]) {
                scores[doc] += tf * idf;
            }
        }

        return scores;
    }
};

/* ========================= LRU CACHE ========================= */
class LRUCache {
private:
    int capacity;

    list<string> order; // most recent at front
    unordered_map<string, pair<list<string>::iterator, vector<pair<string,double>>>> cache;

public:
    LRUCache(int cap) : capacity(cap) {}

    bool exists(const string &key) {
        return cache.find(key) != cache.end();
    }

    vector<pair<string,double>> get(const string &key) {
        auto &node = cache[key];

        // move to front
        order.erase(node.first);
        order.push_front(key);
        node.first = order.begin();

        return node.second;
    }

    void put(const string &key, vector<pair<string,double>> value) {
        if (exists(key)) {
            order.erase(cache[key].first);
        } else if (cache.size() >= capacity) {
            string lru = order.back();
            order.pop_back();
            cache.erase(lru);
        }

        order.push_front(key);
        cache[key] = {order.begin(), value};
    }
};

class SearchEngine {
private:
    DocumentLoader loader;
    InvertedIndex index;
    LRUCache cache;

public:
    SearchEngine(int cacheSize = 5) : cache(cacheSize) {}

    void init(const vector<string> &files) {
        loader.load(files);
        index.build(loader.contents);

        cout << "Index built. Words: " << index.index.size() << endl;
    }

    void search(const string &query) {
        if (cache.exists(query)) {
            cout << "⚡ Cache hit!\n";
            display(cache.get(query));
            return;
        }

        auto scores = TFIDFScorer::score(query, index);

        if (scores.empty()) {
            cout << "No results found\n";
            return;
        }

        vector<pair<string,double>> results(scores.begin(), scores.end());

        sort(results.begin(), results.end(),
             [](auto &a, auto &b) {
                 return a.second > b.second;
             });

        cache.put(query, results);

        display(results);
    }

    void display(const vector<pair<string,double>> &results) {
        cout << "\nResults:\n";
        for (auto &[doc, score] : results) {
            cout << doc << " (score: " << score << ")\n";
        }
    }
};

int main() {
    vector<string> files = {
        "E:/Codes/C++/project/engine/docs/file1.txt",
        "E:/Codes/C++/project/engine/docs/file2.txt",
        "E:/Codes/C++/project/engine/docs/file3.txt"
    };

    SearchEngine engine(3); // LRU cache size = 3
    engine.init(files);

    while (true) {
        cout << "\nEnter query (or 'exit'): ";
        string query;
        getline(cin, query);

        if (query == "exit") break;

        engine.search(query);
    }

    return 0;
}