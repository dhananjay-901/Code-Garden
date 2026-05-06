#include <bits/stdc++.h>
using namespace std;

unordered_map<string, unordered_map<string, double>> index; // word -> (doc -> tf)
unordered_map<string, string> contents; // doc -> content
int totalDocs = 0;

// Normalize words (LOWERCASE + remove punctuation)
string normalize(const string &word) {
    string clean;
    for (char c : word) {
        if (isalnum(c)) {
            clean += tolower(c);
        }
    }
    return clean;
}

//Load files
void loadFiles(const vector<string> &files) {
    for (auto &f : files) {
        cout << "Loading: " << f << endl;

        ifstream in(f);
        if (!in) {
            cerr << "Error opening: " << f << endl;
            continue;
        }

        stringstream buffer;
        buffer << in.rdbuf();
        contents[f] = buffer.str();
    }

    totalDocs = contents.size();

    if (totalDocs == 0) {
        cerr << "No documents loaded. Check paths.\n";
        exit(1);
    }
}

// Build TF index
void buildIndex() {
    for (auto &[doc, text] : contents) {
        unordered_map<string, int> freq;
        stringstream ss(text);
        string word;
        int totalWords = 0;

        while (ss >> word) {
            word = normalize(word);
            if (word.empty()) continue;

            freq[word]++;
            totalWords++;
        }

        for (auto &[w, count] : freq) {
            double tf = (double)count / totalWords;
            index[w][doc] = tf;
        }
    }

    cout << "Index built. Unique words: " << index.size() << endl;
}

//Search function (TF-IDF)
void search(const string &query) {
    unordered_map<string, double> scores;

    stringstream ss(query);
    string term;

    while (ss >> term) {
        term = normalize(term);
        if (term.empty()) continue;

        if (index.find(term) == index.end()) continue;

        int df = index[term].size();
        double idf = log((double)(totalDocs + 1) / (df + 1)) + 1;

        for (auto &[doc, tf] : index[term]) {
            scores[doc] += tf * idf;
        }
    }

    if (scores.empty()) {
        cout << "No results found.\n";
        return;
    }

    // Sort results
    vector<pair<string, double>> results(scores.begin(), scores.end());
    sort(results.begin(), results.end(),
         [](auto &a, auto &b) {
             return a.second > b.second;
         });

    cout << "\nResults:\n";
    for (auto &[doc, score] : results) {
        cout << doc << " (score: " << score << ")\n";
    }
}

int main() {
    vector<string> files = {
        "E:/Codes/C++/project/engine/docs/file1.txt",
        "E:/Codes/C++/project/engine/docs/file2.txt",
        "E:/Codes/C++/project/engine/docs/file3.txt"
    };

    loadFiles(files);
    buildIndex();

    cout << "\nEnter search query: ";
    string query;
    getline(cin, query);

    search(query);

    return 0;
}