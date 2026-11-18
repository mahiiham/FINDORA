# Which AI API does Findora use? — None (and how to add one)

**No external AI API is used.** There are no API keys, no network calls to any AI company, and no AI libraries
other than the two below. Everything runs on your own computer:

* `scikit-learn` — TF-IDF + cosine similarity for the description text (classic machine learning, not an LLM)
* `Pillow` — a 64-bit "difference hash" (dHash) fingerprint of each photo, compared with Hamming distance
* plain Python (`difflib`) for category/location/colour/brand, plus a date-distance rule

The scores are real and are used for matching (`app/matching/service.py`), but they are *algorithms*, not a chat/LLM
service. That is deliberate: it is free, fast, private and explainable.

## When an AI API would help
* understanding **synonyms** ("mobile" = "phone", "bag" = "backpack") and typos;
* **describing photos** ("red backpack with a blue keychain") so two different photos of the same thing match;
* writing a short **explanation** for the admin ("same brand, model and cracked corner → likely the same phone").

## How to add one (optional "AI re-ranker" for borderline pairs)
Use the API only for pairs that are *close* to the threshold (for example 70–80 %), so cost stays tiny.

1. `pip install anthropic` and set the key in your environment (never commit it):
   `set ANTHROPIC_API_KEY=...` (Windows) / `export ANTHROPIC_API_KEY=...` (macOS/Linux). Add `AI_RERANK=1` to `.env` to switch it on.
2. Create `app/matching/llm_rerank.py`:
```python
import json, os
import anthropic

_client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY
MODEL = os.getenv('AI_MODEL', 'claude-haiku-5-5')

def _public(item):                        # ONLY public fields - never the private verification detail
    return {'type': item.item_type, 'title': item.title, 'description': item.description, 'category': item.category.name,
            'colour': item.color, 'brand': item.brand, 'model': item.model, 'features': item.distinguishing_features,
            'place': item.location.name, 'date': str(item.date_event)}

def llm_pair_score(lost, found):
    """Return (0..1 score, short reason) or None if the API is unavailable."""
    prompt = ('Two lost-and-found reports from a college campus. Decide how likely they describe the SAME object. '
              'Reply with JSON only: {"score": 0.0-1.0, "reason": "one short sentence"}.\n'
              f'LOST: {json.dumps(_public(lost))}\nFOUND: {json.dumps(_public(found))}')
    try:
        msg = _client.messages.create(model=MODEL, max_tokens=150, messages=[{'role': 'user', 'content': prompt}])
        data = json.loads(msg.content[0].text)
        return max(0.0, min(1.0, float(data['score']))), str(data['reason'])[:160]
    except Exception:
        return None                       # any failure -> keep the normal local score
```
3. In `refresh_matches_for_item` (service.py), right after `score,parts,reasons=score_pair(lost,found)`:
```python
if os.getenv('AI_RERANK') == '1' and threshold - 0.10 <= score < threshold:
    from app.matching.llm_rerank import llm_pair_score
    r = llm_pair_score(lost, found)
    if r:
        score = round(0.7 * score + 0.3 * r[0], 4); reasons.append('AI assistant: ' + r[1])
```
   The pair is then logged exactly like today (score, threshold, passed), so the admin can still justify the result.
4. Privacy checklist: send only public report fields; tell users in the privacy page that borderline reports are
   compared by an external AI service; keep the key in the environment; wrap calls in `try/except` (as above) so the app
   never breaks when the API is down.

## Offline alternative (no API, still "semantic")
Replace TF-IDF with sentence embeddings from `sentence-transformers` (model `all-MiniLM-L6-v2`, ~80 MB, runs on CPU):
`model.encode([text_a, text_b])` then cosine similarity. It understands synonyms without sending data anywhere.

## Free external APIs you can use (and the 80 % threshold)
The text signal is the weakest part of the score, because TF-IDF only matches *identical words*. These options improve it:

| Option | Good for | Cost / privacy (check the provider's current terms) |
|---|---|---|
| **Local sentence embeddings** (`sentence-transformers` or `fastembed`, model `all-MiniLM-L6-v2`) | Synonyms and typos, no data leaves your PC | Free, private. Needs numpy/onnx — use Python 3.11–3.13 |
| **Hugging Face Inference API** (free token) | The same embedding models, hosted | Free tier with rate limits; text is sent to a third party |
| **Google Gemini API** (AI Studio free tier) | Text embeddings **and** photo description ("red backpack, blue keychain") | Free tier with rate limits; read the terms on how free-tier data may be used |
| **Cohere** (trial key) | Embeddings | Trial / non-commercial limits |
| **Claude API** | Best explanations and photo understanding | Paid |

**Recommended:** local embeddings (free and private) for the description signal; replace `text_cosine()` in `app/utils/textsim.py`, nothing else changes.

**About raising the threshold to 80 %.** It is now the default (`MATCH_THRESHOLD=0.80`). It gives fewer, more reliable matches but also misses real ones:
in the sample data three genuine pairs score 82–89 % (shown as matches) while the Samsung phone pair scores 76 % and the glasses pair 66 % (kept in the admin *Rejected* list).
Raising the threshold does not make the AI better — better signals do. If real users report "it should have matched", either lower `MATCH_THRESHOLD`
(for example 0.65) or add embeddings so true pairs reach 80 %. The admin match log always shows the score, the threshold and the gap.
