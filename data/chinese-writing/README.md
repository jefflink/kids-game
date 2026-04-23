**File roles:**

| File | Role | Edit? |
|---|---|---|
| `hanzi-engine.html` | The app — loads `chinese-words.json` at startup | Rarely |
| `chinese-words.json` | Engine-ready recognition data — auto-generated | Never manually |
| `character-database.json` | Master DB of all 701 chars with stroke data | Never manually |
| `word-list.json` | Human-readable list of selected words by HSK level | ✅ Edit this |
| `build_words.py` | Regenerates `chinese-words.json` from the above two | Rarely |

**To add a new word** (e.g. 橙, 紫):
```bash
# 1. Add to word-list.json under the right HSK level:
#    {"char": "橙", "pinyin": "chéng", "meaning": "orange color"}

# 2. Run:
python3 build_words.py

# 3. Commit and push — done.
```

**To add a brand-new character not yet in the DB:**
```bash
python3 build_words.py --fetch-new
# Automatically pulls stroke data from hanzi-writer-data and adds to character-database.json
```

**Bonus features in `build_words.py`:**
- `--hsk 1 2` — generate a lighter `chinese-words.json` with only HSK1+2 for a beginner game
- `--stats` — preview file size and character count without writing anything
- `hanzi-engine.html` now shows a ⏳ loading overlay until the JSON arrives, and a 😢 error if the file is missing
