# Convert Feature Test Strategy

**Purpose:** Document the testing approach for the `debussy convert` command, which transforms freeform plans into Debussy's structured format.

---

## Test Goals

The convert feature tests verify:

1. **Audit-First Validation** - Non-compliant plans fail audit before conversion
2. **Conversion Quality** - The converter produces structurally valid output
3. **Post-Conversion Compliance** - Converted plans pass audit
4. **Content Preservation** - Key information is not lost during conversion

## Test Fixtures

Sample plans in `tests/fixtures/sample_plans/` represent real-world freeform plans:

| Plan | Structure Style | Tech Stack | Key Characteristics |
|------|-----------------|------------|---------------------|
| `plan1_tasktracker_basic/` | `## Phase:` headers | Flask + React | Traditional phases, validation mentions |
| `plan2_tasktracker_agile/` | Numbered sprints (1., 2.) | Django + Vue.js | Agile terminology, sprint-based |
| `plan3_tasktracker_modular/` | "Module" terminology | Node.js + React | Module-based, 4 separate docs |

Each plan:
- Uses natural markdown (not Debussy template format)
- References `python-task-validator` for validation
- Has a master document + separate phase/sprint/module docs
- Represents a realistic project plan

## Test Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. AUDIT (should FAIL)                                     │
│     - Run debussy audit on freeform master plan             │
│     - Expect errors: MASTER_PARSE_ERROR, NO_PHASES, etc.    │
│     - Record pre-conversion compliance score                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CONVERT                                                 │
│     - Run debussy convert on freeform plan                  │
│     - Monitor iteration count (should be ≤ max_iterations)  │
│     - Verify files are created                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. AUDIT (should PASS)                                     │
│     - Run debussy audit on converted MASTER_PLAN.md         │
│     - Expect: passed=True, errors=0                         │
│     - Record post-conversion compliance score               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. CONTENT VERIFICATION                                    │
│     - Compare source vs converted content                   │
│     - Check for information loss                            │
│     - Validate semantic preservation                        │
└─────────────────────────────────────────────────────────────┘
```

## Compliance Metrics

The audit provides a compliance indicator:

```python
compliance_score = phases_valid / phases_found  # 0.0 to 1.0
```

For freeform plans, we expect:
- **Pre-conversion:** `compliance_score = 0.0` (parse errors, no valid phases)
- **Post-conversion:** `compliance_score = 1.0` (all phases valid)

---

## Quality Evaluation Metrics

Metrics organized from **easy to hard** implementation, allowing quick wins first.

### Tier 1: Easy Wins (Deterministic Checks)

These can be implemented immediately with simple string/regex matching.

| Metric | How to Check | Implementation |
|--------|--------------|----------------|
| **Phase Count** | Count phases in source vs output | Compare `len(source_phases)` vs `audit.summary.phases_found` |
| **Required Agents** | Check if `python-task-validator` (or others) appear | `"python-task-validator" in converted_content` |
| **Tech Stack Mentions** | Check if key technologies preserved | Extract keywords (Flask, React, etc.) and verify presence |
| **Gate Format** | Audit already validates gates exist | `audit.summary.gates_total > 0` per phase |
| **Filename Convention** | Check files match expected pattern | `re.match(r"phase-\d+\.md", filename)` |

```python
# Example: Phase count check
def test_phase_count_preserved():
    source_phases = count_phases_in_freeform(source_plan)  # regex for "### Phase:" etc.
    result = auditor.audit(converted_master)
    assert result.summary.phases_found == source_phases

# Example: Agent reference preserved
def test_required_agents_preserved():
    source_content = source_plan.read_text()
    converted_content = (output_dir / "MASTER_PLAN.md").read_text()

    if "python-task-validator" in source_content:
        # Should appear in at least one phase file
        phase_files = output_dir.glob("phase-*.md")
        assert any("python-task-validator" in f.read_text() for f in phase_files)
```

### Tier 2: Medium Difficulty (Keyword Extraction)

Extract and compare important terms/concepts.

| Metric | How to Check | Implementation |
|--------|--------------|----------------|
| **Technology Keywords** | Extract tech terms, compare sets | Use predefined tech vocabulary or NER |
| **Task Keywords** | Extract verbs/actions from tasks | Simple word extraction from `- [ ]` lines |
| **Risk Mentions** | Check if risks are carried over | Look for "risk", "mitigation" terms |

```python
# Example: Technology preservation
TECH_KEYWORDS = {"flask", "react", "postgresql", "jwt", "django", "vue", "node"}

def extract_tech_mentions(text: str) -> set[str]:
    text_lower = text.lower()
    return {kw for kw in TECH_KEYWORDS if kw in text_lower}

def test_tech_stack_preserved():
    source_tech = extract_tech_mentions(source_plan.read_text())
    converted_tech = extract_tech_mentions(converted_master.read_text())

    # All source tech should appear in converted
    missing = source_tech - converted_tech
    assert not missing, f"Tech stack lost: {missing}"
```

### Tier 3: Harder (Text Similarity Metrics)

Use NLP techniques for semantic comparison. These require additional dependencies.

#### Option A: Jaccard Similarity (No ML, just sets)

Simple set-based comparison. Good baseline, fast, no dependencies.

```python
def jaccard_similarity(text1: str, text2: str) -> float:
    """Word-level Jaccard similarity."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) if union else 0.0

# Usage
similarity = jaccard_similarity(source_content, converted_content)
assert similarity > 0.3  # At least 30% word overlap
```

**Pros:** No dependencies, fast, interpretable
**Cons:** Ignores word order, synonyms, context

#### Option B: TF-IDF + Cosine Similarity (sklearn)

Better than Jaccard, captures term importance.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def tfidf_similarity(text1: str, text2: str) -> float:
    """TF-IDF cosine similarity."""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

# Usage
similarity = tfidf_similarity(source_content, converted_content)
assert similarity > 0.5  # At least 50% similar
```

**Pros:** Standard ML approach, handles term frequency
**Cons:** Still bag-of-words, no semantics

#### Option C: Sentence Transformers (Semantic Similarity)

Uses BERT-based embeddings for true semantic comparison. Best quality, but heavier.

```python
# Requires: pip install sentence-transformers
from sentence_transformers import SentenceTransformer, util

def semantic_similarity(text1: str, text2: str, model_name: str = "all-MiniLM-L6-v2") -> float:
    """Semantic similarity using sentence embeddings."""
    model = SentenceTransformer(model_name)
    embeddings = model.encode([text1, text2])
    return util.cos_sim(embeddings[0], embeddings[1]).item()

# Usage
similarity = semantic_similarity(source_content, converted_content)
assert similarity > 0.7  # At least 70% semantically similar
```

**Pros:** Understands meaning, handles paraphrasing
**Cons:** Requires ~100MB model download, slower

#### Option D: ROUGE Score (Summarization Metric)

Measures n-gram overlap, commonly used for text summarization evaluation.

```python
# Requires: pip install rouge-score
from rouge_score import rouge_scorer

def rouge_similarity(reference: str, candidate: str) -> dict[str, float]:
    """ROUGE scores for text comparison."""
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return {
        'rouge1': scores['rouge1'].fmeasure,
        'rouge2': scores['rouge2'].fmeasure,
        'rougeL': scores['rougeL'].fmeasure,
    }

# Usage
scores = rouge_similarity(source_content, converted_content)
assert scores['rougeL'] > 0.4  # At least 40% longest common subsequence
```

**Pros:** Industry standard for summarization, captures structure
**Cons:** Word-level, not semantic

### Tier 4: Advanced (Hybrid Approach)

Combine multiple metrics for a comprehensive score.

```python
@dataclass
class ConversionQuality:
    """Comprehensive conversion quality metrics."""
    phase_count_match: bool
    agents_preserved: bool
    tech_stack_preserved: bool
    gates_valid: bool
    jaccard_similarity: float
    tfidf_similarity: float | None = None  # Optional
    semantic_similarity: float | None = None  # Optional

    @property
    def quick_score(self) -> float:
        """Quick quality score (0-1) using Tier 1-2 metrics."""
        checks = [
            self.phase_count_match,
            self.agents_preserved,
            self.tech_stack_preserved,
            self.gates_valid,
            self.jaccard_similarity > 0.3,
        ]
        return sum(checks) / len(checks)

    @property
    def full_score(self) -> float:
        """Full quality score including ML metrics."""
        base = self.quick_score * 0.5
        if self.tfidf_similarity:
            base += self.tfidf_similarity * 0.25
        if self.semantic_similarity:
            base += self.semantic_similarity * 0.25
        return base
```

---

## Recommended Implementation Order

1. **Phase 1: Quick Wins** (Tier 1)
   - Phase count validation
   - Agent reference checks
   - Filename pattern checks
   - Already have: audit passes

2. **Phase 2: Keyword Extraction** (Tier 2)
   - Tech stack preservation
   - Task keyword overlap
   - No new dependencies

3. **Phase 3: Basic Similarity** (Tier 3a-b)
   - Add Jaccard similarity (no deps)
   - Add TF-IDF if sklearn available

4. **Phase 4: Semantic Analysis** (Tier 3c-d, optional)
   - Add sentence-transformers for deep analysis
   - Add ROUGE for summarization-style metrics
   - Only if higher accuracy needed

---

## Test Cases

### 1. Pre-Conversion Audit Failure

**Goal:** Verify audit correctly identifies non-compliant plans.

```python
def test_freeform_plan_fails_audit():
    """Freeform plans should fail audit - they don't match template."""
    auditor = PlanAuditor()
    result = auditor.audit(sample_plans_dir / "plan1_tasktracker_basic" / "master_plan.md")

    assert not result.passed
    assert result.summary.errors > 0
```

### 2. Conversion Execution

**Goal:** Verify converter can process freeform plans.

```python
def test_convert_freeform_plan():
    """Converter should transform freeform plan to structured format."""
    converter = PlanConverter(auditor, templates_dir, max_iterations=3)
    result = converter.convert(source_plan, output_dir)

    assert result.files_created  # At least some files were created
    assert result.iterations <= 3  # Didn't exhaust retries
```

### 3. Post-Conversion Audit Pass

**Goal:** Verify converted plans pass audit.

```python
def test_converted_plan_passes_audit():
    """After conversion, the plan should pass audit."""
    result = auditor.audit(output_dir / "MASTER_PLAN.md")

    assert result.passed
    assert result.summary.errors == 0
```

### 4. Content Preservation

**Goal:** Verify key content is preserved.

```python
def test_content_preserved():
    """Critical content should survive conversion."""
    # Phase count
    assert result.summary.phases_found == expected_phases

    # Agent references
    assert "python-task-validator" in converted_content

    # Tech stack
    assert all(tech in converted_content for tech in ["flask", "postgresql", "react"])
```

---

## Loss Categories

### Acceptable Loss
- Marketing language / fluff
- Duplicate information
- Formatting variations
- Section reordering

### Concerning Loss
- Task details truncated
- Dependencies not captured
- Risk assessments missing
- Validation criteria simplified

### Critical Loss
- Entire phases dropped
- Validation requirements missing
- Agent specifications lost
- Technology stack omitted

---

## Running the Tests

```bash
# Run all convert tests
uv run pytest tests/test_convert_samples.py -v

# Run with coverage
uv run pytest tests/test_convert_samples.py -v --cov=debussy.converters

# Run specific test
uv run pytest tests/test_convert_samples.py::TestSamplePlanConversion::test_plan1_basic_audit_fails -v
```

## Notes

- Tests use mocked Claude responses to avoid API costs
- For real integration testing, use `--integration` flag (requires API key)
- Sample plans intentionally vary in structure to test robustness

## References

- [Text Similarity in Python](https://spotintelligence.com/2022/12/19/text-similarity-python/) - Overview of similarity techniques
- [Sentence Transformers Documentation](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html) - Semantic similarity with SBERT
- [ROUGE and BERTScore](https://haticeozbolat17.medium.com/bertscore-and-rouge-two-metrics-for-evaluating-text-summarization-systems-6337b1d98917) - Summarization metrics
- [Cosine Similarity with sklearn](https://memgraph.com/blog/cosine-similarity-python-scikit-learn) - TF-IDF approach
