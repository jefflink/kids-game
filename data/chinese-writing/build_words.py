#!/usr/bin/env python3
"""
build_words.py
==============
Generates chinese-words.json from word-list.json + character-database.json.
That JSON is loaded by hanzi-engine.html at runtime.

QUICK START
-----------
  # Default: HSK 1-4 (good for children's spelling games)
  python3 build_words.py

  # HSK 1-6 (full exam vocabulary)
  python3 build_words.py --section hsk1 hsk2 hsk3 hsk4 hsk5 hsk6

  # Thematic set for young children
  python3 build_words.py --section hsk1 hsk2 thematic_numbers thematic_colors thematic_animals thematic_body

  # Full dictionary (all 9500+ chars)
  python3 build_words.py --all

  # Preview without writing
  python3 build_words.py --stats

  # Add characters not yet in character-database.json
  python3 build_words.py --fetch-new

AVAILABLE SECTIONS  (in word-list.json)
----------------------------------------
  hsk1..hsk6          Official HSK exam levels
  thematic_numbers    Numbers 零–亿
  thematic_colors     Colors
  thematic_body       Body parts
  thematic_nature     Nature & elements
  thematic_animals    Animals
  thematic_food       Food
  thematic_family     Family members
  thematic_school     School objects
  thematic_time       Time words
  thematic_places     Places
  extra_common        Non-HSK, up to 12 strokes  (~5200)
  extra_rare          Non-HSK, 13+ strokes       (~3700)

OUTPUT SIZE GUIDE
-----------------
  hsk1+2          ~110 chars   ~50KB    beginner / young children
  hsk1–4          ~350 chars   ~160KB   primary school
  hsk1–6          ~700 chars   ~320KB   full exam prep
  hsk1–6+common  ~5900 chars  ~2.7MB   comprehensive
  --all           ~9500 chars  ~4.4MB   full dictionary
"""

import json, sys, os, math, subprocess

WORD_LIST_FILE  = 'word-list.json'
CHAR_DB_FILE    = 'character-database.json'
OUTPUT_FILE     = 'chinese-words.json'
SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SECTIONS = ['hsk1','hsk2','hsk3','hsk4']

# ── Geometry (must match hanzi-engine.html exactly) ───────────────────────────
TAU = math.pi * 2
def _na(a): a=a%TAU; return a if a>=0 else a+TAU
def _ad(a,b): d=abs(_na(a)-_na(b)); return d if d<=math.pi else TAU-d

def _resample(pts, n=32):
    pts=[(float(p[0]),float(p[1])) for p in pts]
    if len(pts)<2: return pts
    tot=sum(math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]) for i in range(1,len(pts)))
    if tot==0: return [pts[0]]*n
    step=tot/(n-1); out=[pts[0]]; acc=0; prev=pts[0]
    for i in range(1,len(pts)):
        d=math.hypot(pts[i][0]-prev[0],pts[i][1]-prev[1])
        while acc+d>=step and len(out)<n:
            t=(step-acc)/d if d>0 else 0
            p=(prev[0]+t*(pts[i][0]-prev[0]),prev[1]+t*(pts[i][1]-prev[1]))
            out.append(p); prev=p; d=math.hypot(pts[i][0]-prev[0],pts[i][1]-prev[1]); acc=0
        acc+=d; prev=pts[i]
    while len(out)<n: out.append(pts[-1])
    return out[:n]

def _nbb(strokes):
    strokes=[[(float(p[0]),float(p[1])) for p in s] for s in strokes]
    ap=[p for s in strokes for p in s]
    xs=[p[0] for p in ap]; ys=[p[1] for p in ap]
    x0,y0=min(xs),min(ys); sc=max(max(xs)-x0,max(ys)-y0) or 1
    return [[(( p[0]-x0)/sc,(p[1]-y0)/sc) for p in s] for s in strokes]

_ST=math.pi*0.20; _CU=math.pi*0.55
def _split(pts):
    r=_resample(pts,32)
    if len(r)<3: return [r]
    dirs=[math.atan2(r[i+1][1]-r[i][1],r[i+1][0]-r[i][0]) for i in range(len(r)-1)]
    sp=[0]; cu=0.0
    for i in range(1,len(dirs)):
        s=_ad(dirs[i],dirs[i-1]); cu+=s
        if s>_ST or cu>_CU: sp.append(i); cu=0.0
    sp.append(len(r)-1)
    segs=[]
    for i in range(len(sp)-1):
        seg=r[sp[i]:sp[i+1]+1]
        if len(seg)>=2: segs.append(seg)
    return segs if segs else [r]

def _sd(pts):
    a=pts[0]; b=pts[-1]
    return [round(_na(math.atan2(b[1]-a[1],b[0]-a[0])),4),
            round(math.hypot(b[0]-a[0],b[1]-a[1]),4),
            round(sum(p[0] for p in pts)/len(pts),4),
            round(sum(p[1] for p in pts)/len(pts),4)]

def analyze_strokes(raw_medians):
    norm=_nbb(raw_medians)
    return [[_sd(s) for s in _split(st)] for st in norm]

# ── Fetch from hanzi-writer-data ──────────────────────────────────────────────
def fetch_from_npm(chars):
    script=f"""
const chars={json.dumps(chars,ensure_ascii=False)};
const out={{}};
chars.forEach(c=>{{
  try{{const d=require('hanzi-writer-data/'+c);
    out[c]=d.medians.map(s=>s.map(([x,y])=>[Math.round(x*100/1024),Math.round((900-y)*100/1024)]));
  }}catch(e){{out[c]=null;}}
}});
console.log(JSON.stringify(out));
"""
    try:
        r=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=120,cwd=SCRIPT_DIR)
        if r.returncode!=0: print(f'  node error: {r.stderr[:200]}'); return {}
        return json.loads(r.stdout)
    except FileNotFoundError:
        print('  ERROR: node not found. Install Node.js.'); return {}
    except subprocess.TimeoutExpired:
        print('  ERROR: node timed out.'); return {}

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args=sys.argv[1:]
    fetch_new  ='--fetch-new' in args
    stats_only ='--stats'     in args
    include_all='--all'       in args

    sections=None
    if '--section' in args:
        idx=args.index('--section')
        sections=[]
        for a in args[idx+1:]:
            if a.startswith('--'): break
            sections.append(a)
        if not sections:
            print('ERROR: --section needs names, e.g. --section hsk1 hsk2')
            sys.exit(1)
    elif not include_all:
        sections=DEFAULT_SECTIONS

    os.chdir(SCRIPT_DIR)

    if not os.path.exists(WORD_LIST_FILE):
        print(f'ERROR: {WORD_LIST_FILE} not found'); sys.exit(1)
    if not os.path.exists(CHAR_DB_FILE):
        print(f'ERROR: {CHAR_DB_FILE} not found'); sys.exit(1)

    word_list=json.load(open(WORD_LIST_FILE,encoding='utf-8'))
    char_db  =json.load(open(CHAR_DB_FILE,  encoding='utf-8'))

    available=[k for k in word_list if not k.startswith('_')]
    if sections is None:
        sections=available  # --all

    invalid=[s for s in sections if s not in available]
    if invalid:
        print(f'ERROR: Unknown sections: {invalid}')
        print(f'Available: {available}')
        sys.exit(1)

    # Collect chars, deduplicating, preserving section order
    seen=set(); selected=[]
    for sec in sections:
        for e in word_list.get(sec,[]):
            char=e.get('char','').strip()
            if char and char not in seen:
                seen.add(char)
                selected.append({'char':char,'pinyin':e.get('pinyin','?'),
                                 'meaning':e.get('meaning',char),'section':sec})

    sec_label='+'.join(sections) if len(sections)<=5 else f'{len(sections)} sections'
    print(f'Sections : {sec_label}')
    print(f'Selected : {len(selected)} unique characters')

    # Handle missing chars
    missing=[e for e in selected if e['char'] not in char_db]
    if missing:
        chars_str=''.join(e['char'] for e in missing[:20])+('...' if len(missing)>20 else '')
        print(f'Missing from DB: {len(missing)} chars: {chars_str}')
        if fetch_new:
            print('Fetching stroke data from hanzi-writer-data...')
            raw=fetch_from_npm([e['char'] for e in missing])
            added=0
            for e in missing:
                m=raw.get(e['char'])
                if m:
                    char_db[e['char']]={'pinyin':e['pinyin'],'meaning':e['meaning'],
                                        'hsk':0,'strokes':len(m),'ss':analyze_strokes(m)}
                    added+=1
                else:
                    print(f'  ✗ {e["char"]} — not found in hanzi-writer-data')
            if added:
                with open(CHAR_DB_FILE,'w',encoding='utf-8') as f:
                    json.dump(char_db,f,ensure_ascii=False,indent=2)
                print(f'Added {added} chars to {CHAR_DB_FILE}')
        else:
            print('  Use --fetch-new to add them automatically.')
        selected=[e for e in selected if e['char'] in char_db]

    if stats_only:
        total_segs=sum(sum(len(s) for s in char_db[e['char']]['ss']) for e in selected)
        raw_size=len(json.dumps([char_db[e['char']] for e in selected],ensure_ascii=False))
        print(f'\nStats:')
        print(f'  Characters            : {len(selected):,}')
        print(f'  Total substroke segs  : {total_segs:,}')
        print(f'  Estimated output size : {raw_size//1024}KB')
        return

    # Build output
    output=[]
    for e in selected:
        db_e=char_db[e['char']]
        py=e['pinyin'] if e['pinyin'] not in ('?','') else db_e['pinyin']
        mn=e['meaning'] if e['meaning'] not in (e['char'],'') else db_e['meaning']
        output.append({'char':e['char'],'py':py,'mn':mn,
                       'hsk':db_e['hsk'],'sc':db_e['strokes'],'ss':db_e['ss']})

    with open(OUTPUT_FILE,'w',encoding='utf-8') as f:
        json.dump(output,f,ensure_ascii=False,separators=(',',':'))

    size_kb=os.path.getsize(OUTPUT_FILE)//1024
    print(f'\nWrote {OUTPUT_FILE}')
    print(f'  {len(output)} characters, {size_kb}KB')

    by_sec={}
    for e,o in zip(selected,output):
        by_sec.setdefault(e['section'],0); by_sec[e['section']]+=1
    for sec in sections:
        if sec in by_sec:
            print(f'  {sec}: {by_sec[sec]}')

    print(f'\nDone. Reload hanzi-engine.html to apply.')

if __name__=='__main__':
    main()
