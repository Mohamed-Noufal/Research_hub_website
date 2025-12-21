# Phase 6: AI Writing Tools
## AI Detection & Paraphrasing for Academic Integrity

**Timeline:** Week 10-11 (~30 hours)  
**Priority:** MEDIUM - Advanced features  
**Impact:** Academic integrity, writing improvement

---

## 🎯 **Phase 6 Objectives**

1. AI writing detection (detect AI-generated content)
2. Academic paraphrasing tool
3. Citation preservation
4. Writing improvement suggestions

---

## 🤖 **Task 6.1: AI Detection Service** (8 hours)

```python
# backend/app/services/ai_detection_service.py
class AIDetectionService:
    """Detect AI-generated content in academic text"""
    
    async def detect_ai_content(self, text: str) -> Dict:
        """
        Detect AI-generated content
        
        Returns:
            {
                "is_ai_generated": bool,
                "ai_probability": float (0-1),
                "confidence": str,
                "recommendation": str
            }
        """
```

**API Options:**
- **GPTZero** (Recommended): $10/month for 150,000 words
- **Copyleaks**: $9.99/month for 100 pages
- **Originality.AI**: $0.01 per 100 words

**Cost:** ~$0.00007 per word

---

## ✍️ **Task 6.2: Paraphrasing Service** (10 hours)

```python
# backend/app/services/paraphrasing_service.py
class ParaphrasingService:
    """Paraphrase academic text while preserving meaning"""
    
    async def paraphrase_text(
        self,
        text: str,
        style: str = "academic",
        preserve_citations: bool = True
    ) -> Dict:
        """
        Paraphrase text while maintaining academic integrity
        
        Returns:
            {
                "original": str,
                "paraphrased": str,
                "similarity_score": float,
                "preserved_citations": List
            }
        """
```

**Features:**
- Multiple styles (academic, simple, technical)
- Preserves citations automatically
- Maintains semantic similarity (>85%)
- Highlights changes

**Cost:** ~$0.0003 per paragraph (GPT-5 nano)

---

## 🌐 **Task 6.3: API Endpoints** (4 hours)

```python
# backend/app/api/v1/ai_tools.py
@router.post("/ai-tools/detect")
@limiter.limit("10/hour")
async def detect_ai_content(text: str):
    """Detect AI-generated content in text"""

@router.post("/ai-tools/paraphrase")
@limiter.limit("20/hour")
async def paraphrase_text(
    text: str,
    style: str = "academic",
    preserve_citations: bool = True
):
    """Paraphrase text while preserving meaning"""
```

---

## 🎨 **Task 6.4: Frontend Components** (8 hours)

```typescript
// frontend/src/components/AIDetector.tsx
export function AIDetector() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);
  
  return (
    <div className="ai-detector">
      <h3>AI Content Detector</h3>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste text to analyze..."
      />
      <button onClick={handleDetect}>Detect AI Content</button>
      
      {result && (
        <div className="result">
          <div className="ai-probability">
            {(result.ai_probability * 100).toFixed(1)}%
          </div>
          <p>{result.recommendation}</p>
        </div>
      )}
    </div>
  );
}

// frontend/src/components/Paraphraser.tsx
export function Paraphraser() {
  return (
    <div className="paraphraser">
      <h3>Academic Paraphraser</h3>
      <select value={style}>
        <option value="academic">Academic</option>
        <option value="simple">Simple</option>
        <option value="technical">Technical</option>
      </select>
      <textarea placeholder="Paste text to paraphrase..." />
      <button onClick={handleParaphrase}>Paraphrase</button>
    </div>
  );
}
```

---

## ✅ **Success Criteria**

- [ ] AI detection accuracy >85%
- [ ] Paraphrasing maintains meaning (similarity >0.85)
- [ ] Citations preserved correctly
- [ ] Cost < $0.01 per use
- [ ] Rate limiting works

**Total Time:** ~30 hours  
**Total Cost:** $10-50/month (API costs)
