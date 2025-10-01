from typing import Tuple
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    _vader = None
    def _ensure_vader():
        global _vader
        if _vader is None:
            try:
                nltk.data.find("sentiment/vader_lexicon.zip")
            except LookupError:
                nltk.download("vader_lexicon")
            _vader = SentimentIntensityAnalyzer()
        return _vader
    def sentiment_score(text: str) -> float:
        sia = _ensure_vader()
        return float(sia.polarity_scores(text or "").get("compound", 0.0))
except Exception:
    # Fallback naive sentiment (very rough) if nltk unavailable
    POS = set(["good","great","nice","love","helpful","effective","calm","sleep"])
    NEG = set(["bad","worse","awful","hate","side-effect","nausea","dizzy","pain"])
    def sentiment_score(text: str) -> float:
        tokens = (text or "").lower().split()
        score = 0
        for t in tokens:
            if t in POS: score += 1
            if t in NEG: score -= 1
        return max(-1.0, min(1.0, score/10.0))
