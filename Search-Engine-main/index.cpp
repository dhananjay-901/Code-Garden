#include <bits/stdc++.h>
using namespace std;

int totalDocs = 0;

// word -> (file -> frequency)
unordered_map<string, unordered_map<string, int>> indexMap;

// stop words
unordered_set<string> stopWords = {"the", "is", "and", "a",  "an",
                                   "of",  "to", "in",  "on", "for"};

// ---------------- FILE READING ----------------
string readFile(const string &filename) {
  ifstream file(filename);

  if (!file) {
    cout << "Error opening file: " << filename << endl;
    return "";
  }

  stringstream buffer;
  buffer << file.rdbuf();
  return buffer.str();
}

// ---------------- TOKENIZATION ----------------
vector<string> tokenize(const string &text) {
  vector<string> words;
  string word;

  for (char c : text) {
    if (isalpha(c)) {
      word += tolower(c);
    } else {
      if (!word.empty()) {
        if (!stopWords.count(word)) {
          words.push_back(word);
        }
        word.clear();
      }
    }
  }

  if (!word.empty() && !stopWords.count(word)) {
    words.push_back(word);
  }

  return words;
}

// ---------------- INDEXING ----------------
void indexDocument(const string &filename, const string &content) {
  vector<string> words = tokenize(content);

  for (const string &word : words) {
    indexMap[word][filename]++;
  }
}

// ---------------- SEARCH ----------------
vector<pair<string, double>> search(const string &query) {
  unordered_map<string, double> scores;

  vector<string> queryWords = tokenize(query);

  for (const string &word : queryWords) {
    if (indexMap.count(word)) {

      int df = indexMap[word].size(); // number of docs containing word
      double idf = log((double)totalDocs / df);

      for (auto &[file, tf] : indexMap[word]) {
        scores[file] += tf * idf; // 🔥 TF-IDF
      }
    }
  }

  vector<pair<string, double>> results(scores.begin(), scores.end());

  sort(results.begin(), results.end(),
       [](auto &a, auto &b) { return a.second > b.second; });

  return results;
}

// ---------------- MAIN ----------------
int main() {
  cout << "Mini Search Engine (with Stop Words)\n";
  vector<string> files = {"docs/file1.txt", "docs/file2.txt", "docs/file3.txt"};

  totalDocs = files.size();
  for (const string &file : files) {
    string content = readFile(file);
    indexDocument(file, content);
  }

  cout << "Indexing complete.\n";

  while (true) {
    cout << "\nSearch (type 'exit' to quit): ";
    string query;
    getline(cin, query);

    if (query == "exit")
      break;

    vector<pair<string, double>> results = search(query);

    if (results.empty()) {
      cout << "No results found.\n";
      continue;
    }

    cout << "\nResults:\n";
    for (auto &[file, score] : results) {
      cout << file << " (score: " << score << ")\n";
    }
  }

  return 0;
}

//the output for apple is
// ocs/file1.txt (score: 0.81093)
//docs/file3.txt (score: 0.405465)
// because the formula for term frequence inverse document frequency (tf-idf) the math is TF * log(N / DF) tf - is term frequency and n is total number of docs and df is the number of times apple appears in documents
