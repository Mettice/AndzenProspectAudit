# 2-Day MVP Quick Checklist

## ✅ Day 1 Checklist

### Setup (30 min)
- [ ] Install LangChain: `pip install langchain langchain-anthropic langchain-openai`
- [ ] Create `api/services/llm/` directory
- [ ] Add API keys to environment variables

### Core LLM Service (2-3 hours)
- [ ] Create `api/services/llm/__init__.py` with multi-LLM support
- [ ] Test Claude connection
- [ ] Test OpenAI connection
- [ ] Create simple `generate_insights()` function

### KAV Section Integration (2-3 hours)
- [ ] Create `api/services/llm/prompts.py` with KAV template
- [ ] Create KAV prompt template (data + context + instructions)
- [ ] Modify `api/services/report.py` → `_prepare_kav_data()`
- [ ] Replace `StrategyNarrativeEngine` with LLM call
- [ ] Test KAV section with LLM insights

### End of Day 1
- [ ] Report generates successfully
- [ ] KAV section shows LLM-generated insights
- [ ] No breaking errors

---

## ✅ Day 2 Checklist

### Flow Sections (2-3 hours)
- [ ] Add Flow Performance prompt template
- [ ] Integrate LLM into flow sections
- [ ] Test flow insights generation

### Data Formatting (1 hour)
- [ ] Create `api/services/llm/formatter.py`
- [ ] Format Klaviyo data for LLM consumption
- [ ] Test data formatting

### Full MVP Test (2 hours)
- [ ] Generate complete report
- [ ] Verify HTML renders correctly
- [ ] Verify PDF generates
- [ ] Check LLM insights appear in sections
- [ ] Test error handling (what if LLM fails?)

### Bug Fixes (1-2 hours)
- [ ] Fix any critical errors
- [ ] Add fallback logic if LLM fails
- [ ] Ensure graceful degradation
- [ ] Test edge cases

### Documentation (30 min)
- [ ] Document what's working
- [ ] List known limitations
- [ ] Prepare demo for boss

### End of Day 2
- [ ] ✅ MVP ready for review
- [ ] ✅ Report generates with LLM insights
- [ ] ✅ No critical bugs
- [ ] ✅ Ready to show boss

---

## 🚨 Critical Path Items (Must Do)

1. **LLM Service Works** - Without this, nothing works
2. **KAV Section with LLM** - This is the proof of concept
3. **Report Generates** - Must not break existing functionality
4. **Error Handling** - System must not crash if LLM fails

---

## ⏸️ Can Skip for MVP (Do Later)

- Gemini integration (Claude + OpenAI enough)
- All sections with LLM (KAV + Flows enough)
- Advanced prompt engineering (basic works)
- Benchmark integration (can hardcode)
- Removing deprecated files (cleanup later)
- Full code cleanup (after MVP approved)

---

## 🎯 Success = MVP Works If:

1. ✅ Report generates
2. ✅ KAV section has LLM insights
3. ✅ At least 1-2 flow sections have LLM insights
4. ✅ No errors
5. ✅ Boss can see it's automated

---

## 📝 Notes

- **Focus on working, not perfect**
- **If stuck, simplify and move on**
- **Test frequently**
- **Keep existing functionality working**

