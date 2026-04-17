#include <bits/stdc++.h>
using namespace std;
struct Config {
    vector<string> files;
    int topK = 5;
    string indexFile = "index.db";
    int cacheSize = 5;
};
template<typename K, typename V>
class LRUCache {
    int cap;
    list<pair<K,V>> dll;
    unordered_map<K, typename list<pair<K,V>>::iterator> mp;

public:
    LRUCache(int c) : cap(c) {}

    bool exists(const K& key) {
        return mp.count(key);
    }

    V get(const K& key) {
        auto it = mp[key];
        dll.splice(dll.begin(), dll, it);
        return it->second;
    }

    void put(const K& key, const V& val) {
        if (mp.count(key)) {
            dll.erase(mp[key]);
            mp.erase(key);
        }

        dll.push_front({key, val});
        mp[key] = dll.begin();

        if ((int)mp.size() > cap) {
            auto last = dll.back();
            mp.erase(last.first);
            dll.pop_back();
        }
    }
};
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
                if (!word.empty() && !stopWords.count(word))
                    words.push_back(word);
                word.clear();
            }
        }
        if (!word.empty() && !stopWords.count(word))
            words.push_back(word);

        return words;
    }
};
class DocumentStore {
    unordered_map<string,string> contents;

public:
    void load(const vector<string>& files) {
        for (auto& f : files) {
            ifstream in(f);
            if (!in) {
                cerr << "Error opening: " << f << endl;
                continue;
            }
            stringstream ss;
            ss << in.rdbuf();
            contents[f] = ss.str();
        }
    }

    const auto& getAll() const { return contents; }
    const string& get(const string& f) const { return contents.at(f); }
    int size() const { return contents.size(); }
};
class Indexer {
    unordered_map<string, unordered_map<string,int>> indexMap;

public:
    void build(const DocumentStore& store, Tokenizer& tok) {
        for (auto& [file, content] : store.getAll()) {
            for (auto& w : tok.tokenize(content)) {
                indexMap[w][file]++;
            }
        }
    }

    void save(const string& fname) {
        ofstream out(fname);
        for (auto& [w, mp] : indexMap) {
            out << w;
            for (auto& [f, c] : mp)
                out << " " << f << ":" << c;
            out << "\n";
        }
    }

    void load(const string& fname) {
        ifstream in(fname);
        if (!in) return;

        string line;
        while (getline(in, line)) {
            stringstream ss(line);
            string word; ss >> word;

            string pair;
            while (ss >> pair) {
                int pos = pair.find(":");
                string f = pair.substr(0,pos);
                int c = stoi(pair.substr(pos+1));
                indexMap[word][f] = c;
            }
        }
    }

    const auto& get() const { return indexMap; }
};
class Ranker {
public:
    unordered_map<string,double> score(
    const string& q,
    const unordered_map<string, unordered_map<string,int>>& index,
    Tokenizer& tok,
    int totalDocs
    ) {
        unordered_map<string,double> scores;
        auto words = tok.tokenize(q);

        for (auto& w : words) {
            if (!index.count(w)) continue;

            int df = index.at(w).size();
            double idf = log((double)(totalDocs+1)/(df+1)) + 1;

            for (auto& [f, tf] : index.at(w)) {
                scores[f] += tf * idf;
            }
        }
        return scores;
    }

    vector<pair<string,double>> topK(unordered_map<string,double>& scores, int k) {
        priority_queue<pair<double,string>> pq;

        for (auto& [f,s] : scores)
            pq.push({s,f});

        vector<pair<string,double>> res;
        while (!pq.empty() && k--) {
            res.push_back({pq.top().second, pq.top().first});
            pq.pop();
        }
        return res;
    }
};

class Snippet {
public:
    string generate(const string& content, const string& q, Tokenizer& tok) {
        string lower = content;
        transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

        auto words = tok.tokenize(q);

        size_t pos = string::npos;
        for (auto& w : words) {
            pos = lower.find(w);
            if (pos != string::npos) break;
        }

        if (pos == string::npos) return "No preview";

        int start = max(0, (int)pos - 20);
        int end = min((int)content.size(), (int)pos + 40);

        string snip = content.substr(start, end - start);

        for (auto& w : words) {
            size_t p = snip.find(w);
            if (p != string::npos)
                snip.replace(p, w.length(), "[" + w + "]");
        }

        return "..." + snip + "...";
    }
};
class SearchEngine {
    Config cfg;
    DocumentStore store;
    Tokenizer tok;
    Indexer indexer;
    Ranker ranker;
    Snippet snippet;
    LRUCache<string, vector<pair<string,double>>> cache;

public:
    SearchEngine(Config c) : cfg(c), cache(c.cacheSize) {}

    void init() {
        store.load(cfg.files);

        ifstream test(cfg.indexFile);
        if (test.good()) indexer.load(cfg.indexFile);
        else {
            indexer.build(store, tok);
            indexer.save(cfg.indexFile);
        }
    }

    void query(const string& q) {
        if (cache.exists(q)) {
            cout << "[CACHE HIT]\n";
            auto results = cache.get(q);
            display(results, q);
            return;
        }

        auto scores = ranker.score(q, indexer.get(), tok, store.size());
        auto results = ranker.topK(scores, cfg.topK);

        cache.put(q, results);
        display(results, q);
    }

private:
    void display(const vector<pair<string,double>>& results, const string& q) {
        if (results.empty()) {
            cout << "No results found.\n";
            return;
        }

        cout << "\nResults:\n";
        for (auto& [f,s] : results) {
            cout << f << " (score: " << s << ")\n";
            cout << "→ " << snippet.generate(store.get(f), q, tok) << "\n\n";
        }
    }
};
int main() {
    Config cfg;
    cfg.files = {
        "docs/file1.txt",
        "docs/file2.txt",
        "docs/file3.txt"
    };
    cfg.topK = 3;
    cfg.cacheSize = 5;

    SearchEngine engine(cfg);
    engine.init();

    while (true) {
        cout << "\nSearch (type 'exit'): ";
        string q;
        getline(cin, q);

        if (q == "exit") break;

        engine.query(q);
    }
}
