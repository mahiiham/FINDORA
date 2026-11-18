"""Text similarity for the AI matching engine (TF-IDF + cosine).

Uses scikit-learn when it is installed. When it is NOT installed (for example on a brand-new Python version that has
no pre-built scikit-learn/numpy wheels yet) an equivalent built-in implementation is used, so `pip install` never has
to compile anything. Both follow the same recipe: lower-case, split into words of 2+ letters, drop English stop words,
build 1- and 2-word terms, weight by smoothed TF-IDF over the two texts, L2-normalise and take the cosine."""
import math
import re
from collections import Counter

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ENGINE = 'scikit-learn'
except Exception:  # ImportError, or a broken/partial install
    ENGINE = 'built-in'

# Same list scikit-learn uses (ENGLISH_STOP_WORDS)
STOP_WORDS = frozenset((
    'a', 'about', 'above', 'across', 'after', 'afterwards', 'again', 'against', 'all', 'almost', 'alone',
    'along', 'already', 'also', 'although', 'always', 'am', 'among', 'amongst', 'amoungst', 'amount', 'an',
    'and', 'another', 'any', 'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'are', 'around', 'as',
    'at', 'back', 'be', 'became', 'because', 'become', 'becomes', 'becoming', 'been', 'before', 'beforehand',
    'behind', 'being', 'below', 'beside', 'besides', 'between', 'beyond', 'bill', 'both', 'bottom', 'but',
    'by', 'call', 'can', 'cannot', 'cant', 'co', 'con', 'could', 'couldnt', 'cry', 'de', 'describe', 'detail',
    'do', 'done', 'down', 'due', 'during', 'each', 'eg', 'eight', 'either', 'eleven', 'else', 'elsewhere',
    'empty', 'enough', 'etc', 'even', 'ever', 'every', 'everyone', 'everything', 'everywhere', 'except',
    'few', 'fifteen', 'fifty', 'fill', 'find', 'fire', 'first', 'five', 'for', 'former', 'formerly', 'forty',
    'found', 'four', 'from', 'front', 'full', 'further', 'get', 'give', 'go', 'had', 'has', 'hasnt', 'have',
    'he', 'hence', 'her', 'here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers', 'herself', 'him',
    'himself', 'his', 'how', 'however', 'hundred', 'i', 'ie', 'if', 'in', 'inc', 'indeed', 'interest', 'into',
    'is', 'it', 'its', 'itself', 'keep', 'last', 'latter', 'latterly', 'least', 'less', 'ltd', 'made', 'many',
    'may', 'me', 'meanwhile', 'might', 'mill', 'mine', 'more', 'moreover', 'most', 'mostly', 'move', 'much',
    'must', 'my', 'myself', 'name', 'namely', 'neither', 'never', 'nevertheless', 'next', 'nine', 'no',
    'nobody', 'none', 'noone', 'nor', 'not', 'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once',
    'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our', 'ours', 'ourselves', 'out', 'over',
    'own', 'part', 'per', 'perhaps', 'please', 'put', 'rather', 're', 'same', 'see', 'seem', 'seemed',
    'seeming', 'seems', 'serious', 'several', 'she', 'should', 'show', 'side', 'since', 'sincere', 'six',
    'sixty', 'so', 'some', 'somehow', 'someone', 'something', 'sometime', 'sometimes', 'somewhere', 'still',
    'such', 'system', 'take', 'ten', 'than', 'that', 'the', 'their', 'them', 'themselves', 'then', 'thence',
    'there', 'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these', 'they', 'thick', 'thin',
    'third', 'this', 'those', 'though', 'three', 'through', 'throughout', 'thru', 'thus', 'to', 'together',
    'too', 'top', 'toward', 'towards', 'twelve', 'twenty', 'two', 'un', 'under', 'until', 'up', 'upon', 'us',
    'very', 'via', 'was', 'we', 'well', 'were', 'what', 'whatever', 'when', 'whence', 'whenever', 'where',
    'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon', 'wherever', 'whether', 'which', 'while',
    'whither', 'who', 'whoever', 'whole', 'whom', 'whose', 'why', 'will', 'with', 'within', 'without',
    'would', 'yet', 'you', 'your', 'yours', 'yourself', 'yourselves',
))
_TOKEN = re.compile(r"(?u)\b\w\w+\b")


def _terms(text, ngram_range, use_stop):
    tokens = _TOKEN.findall((text or '').lower())
    if use_stop:
        tokens = [t for t in tokens if t not in STOP_WORDS]
    lo, hi = ngram_range
    terms = []
    for n in range(lo, hi + 1):
        if n == 1:
            terms.extend(tokens)
        else:
            terms.extend(' '.join(tokens[i:i + n]) for i in range(len(tokens) - n + 1))
    return Counter(terms)


def builtin_cosine(a, b, ngram_range=(1, 2), use_stop=True):
    """Pure-Python TF-IDF cosine of two texts (identical in result to the scikit-learn recipe above)."""
    ca, cb = _terms(a, ngram_range, use_stop), _terms(b, ngram_range, use_stop)
    vocab = set(ca) | set(cb)
    if not vocab:
        return 0.0
    idf = {t: math.log((1 + 2) / (1 + (t in ca) + (t in cb))) + 1 for t in vocab}   # smooth idf over 2 documents
    va = {t: c * idf[t] for t, c in ca.items()}
    vb = {t: c * idf[t] for t, c in cb.items()}
    na = math.sqrt(sum(v * v for v in va.values())); nb = math.sqrt(sum(v * v for v in vb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return sum(v * vb.get(t, 0.0) for t, v in va.items()) / (na * nb)


def text_cosine(a, b, ngram_range=(1, 2), use_stop=True):
    """TF-IDF cosine similarity (0..1) between two texts; 0.0 when either has no usable words."""
    if ENGINE == 'scikit-learn':
        try:
            x = TfidfVectorizer(ngram_range=ngram_range, stop_words='english' if use_stop else None).fit_transform([a or '', b or ''])
            return float(cosine_similarity(x[0:1], x[1:2])[0][0])
        except ValueError:
            return 0.0
    return builtin_cosine(a, b, ngram_range, use_stop)
