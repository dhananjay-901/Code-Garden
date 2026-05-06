This document will be defining my thought process and working through and mistakes i made will building this project. 

This project is result of being high on rasputin and 8 glasses of coffee at 4 am. 
I had this crazy idea during one of my late night coding sessions to build something simple as a word finder through a file, Sounds Simple Right? But you are dead wrong here mister. This one simple idea was the reason i am afraid to even use find tool in microsoft word. this project nuclear bomb my brain and pushed my brain to its last limit. well if people ask me that if i used AI, Yes i did not entirely because i am not a copy paste coder. i give it a prompt and later have to refract it and study it line by line so i don't sit dumb in interview after high end employee asks me hey what does line 144 do? 

The basic understanding about your program is most important. Without any further ado let's jump into the my progress and how everything went. Well i will be pasting my personal notes and some frustrated cursing below. Thanks for support and do star me for next updates!. 

[Next lines are going to purely coding and frustration don't mind it. Humor ends here.]

#### search.cpp - 17/4/2026 - Most regretful day 
A tiny, no-nonsense, stop-word-aware search engine I built because I got tired of over-engineered solutions that take 3 weeks to set up.

##### Why This Exists
After fighting with Elasticsearch, Lucene, and 47 dependencies that broke on every OS update, I said **"screw it"** and wrote this in one frustrated night. 

##### Features
- Super simple inverted index using `unordered_map`
- Basic stop words removal (because "the", "is", "and" are the real enemies)
- TF scoring (no fancy PageRank, I'm not Google)
- Tokenization that doesn't cry when it sees punctuation

##### The Reality of Coding
1. Me at 2 AM:
2. "This should be simple"
3. *spends 40 minutes debugging why file paths are wrong*
4. "I hate computers"

#### index.cpp - 19/4/26 - 2 days after that dreadful day 
I took my simple search engine and tried to "make it better"... 

**Famous last words.** After **13 painful breaks**, random segfaults, floating point tantrums, and questioning my life choices at 3 AM, I finally upgraded it with **TF-IDF** scoring.

##### What’s New (and what almost killed me)
- Upgraded from basic term frequency → **Proper TF-IDF**
- Added Inverse Document Frequency (`log(N / DF)`)
- Now returns meaningful relevance scores instead of raw counts
- Still hates stop words with passion

##### The Struggle Was Real
// Me during development:
1. "Just add IDF, how hard can it be?"
2. *code breaks*
3. "Why is score NaN??"
4. *13th rebuild*
5. "I should have stayed with the simple version..."

#### index_high.cpp - 22/4/26 (its high because i was high on coffee and lack of sleep. because i am better when on lack of sleep)
I told myself "just one more feature"...

After **countless crashes**, duplicate indexing bugs, lowercase nightmares, and another round of existential crisis, I finally added **snippets** to the search results.

Yes. I made it *actually useful*.

##### What’s New (and what broke me)
- **TF-IDF** scoring (kept from previous suffering)
- Full document content storage
- Smart **snippet preview** — shows context around your search term
- `getSnippet()` function that almost made me throw my laptop

##### The "me" experience
// Me at 4 AM:
1. "Adding snippets should be easy"
2. *code breaks 8 times*
3. "WHY IS IT SHOWING GARBAGE?!"
4. *fixes 47 off-by-one errors*
5. "Never again."

#### index_high_v1.cpp (built on same night as index_high because i was in seventh cloud after previous build and thought to upgrade it same night biggest mistake)
I said “okay this is the final version”... and then added **multi-word search + highlighting**.

After fixing **yet another** dozen bugs, broken snippets, and highlight logic that kept eating my strings, I present to you the most "polished" version yet.

##### What’s New (The Painful Upgrades)
- Better **multi-word query** support
- Improved snippet generation (now searches for any query word)
- **Highlighting** — matching words wrapped in `[brackets]`
- Still rocking solid TF-IDF scoring
- Stop words handled like the pests they are

##### my development experience
// 6:17 AM monologue:
1. "Multi-word should be easy"
2. *snippet shows garbage*
3. "Why is it highlighting the wrong word?!"
4. *fixes highlighting 9 times*
5. "I regret everything... but it looks cool now."
