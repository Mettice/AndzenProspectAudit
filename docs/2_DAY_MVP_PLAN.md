# 2-Day MVP Plan - Critical Path to Deliverable

**Goal:** Working MVP with LLM-generated insights before Dec 30

**Current Date:** [Check today's date]
**Deadline:** Dec 30 (Boss goes on leave)

---

## Day 1: Foundation & Core LLM Integration

### Morning (4-5 hours)
1. **Install Dependencies** ⏱️ 15 min
   ```bash
   pip install langchain langchain-anthropic langchain-openai
   ```

2. **Create Multi-LLM Service** ⏱️ 1-2 hours
   - `api/services/llm/__init__.py`
   - Support for Claude (Anthropic) and OpenAI
   - Simple interface: `generate_insights(section, data, context)`
   - Basic error handling

3. **Create Prompt Template System** ⏱️ 1-2 hours
   - `api/services/llm/prompts.py`
   - Template for KAV section (highest priority)
   - Template structure: data + industry context + benchmark context + instructions

### Afternoon (3-4 hours)
4. **Test LLM Service with KAV Data** ⏱️ 1 hour
   - Extract sample KAV data
   - Test prompt with Claude/OpenAI
   - Verify output quality
   - Adjust prompts if needed

5. **Integrate LLM into KAV Section** ⏱️ 2-3 hours
   - Modify `api/services/report.py` → `_prepare_kav_data()`
   - Replace `StrategyNarrativeEngine` with LLM call
   - Ensure backward compatibility (fallback if LLM fails)

### End of Day 1 Checkpoint
✅ LLM service working
✅ KAV section generating LLM insights
✅ Report still generates successfully

---

## Day 2: Complete MVP & Testing

### Morning (4-5 hours)
1. **Create Flow Performance Prompt Template** ⏱️ 1 hour
   - Add to `api/services/llm/prompts.py`
   - Template for flow analysis

2. **Integrate LLM into Flow Sections** ⏱️ 2-3 hours
   - Modify flow-related sections in `report.py`
   - Replace hardcoded narratives with LLM calls
   - Test with sample data

3. **Create Data Formatter** ⏱️ 1 hour
   - `api/services/llm/formatter.py`
   - Function to format Klaviyo data for LLM consumption
   - Clean, structured format

### Afternoon (3-4 hours)
4. **Full MVP Test** ⏱️ 1-2 hours
   - Generate complete report
   - Verify all sections render
   - Check LLM insights appear correctly
   - Ensure PDF generation works

5. **Bug Fixes & Polish** ⏱️ 2 hours
   - Fix any critical errors
   - Add error handling for LLM failures
   - Ensure graceful fallbacks
   - Test edge cases

6. **Documentation** ⏱️ 30 min
   - Quick README for MVP
   - List of what's working
   - Known limitations

### End of Day 2 Deliverable
✅ MVP report with LLM insights for:
   - KAV Analysis section
   - Flow Performance sections
✅ Full report generation (HTML + PDF)
✅ Error handling in place
✅ Ready for boss review

---

## Critical Success Factors

### Must Have (MVP):
- ✅ LLM service functional
- ✅ KAV section with LLM insights
- ✅ At least 1-2 flow sections with LLM insights
- ✅ Report generates successfully
- ✅ No breaking changes to existing functionality

### Nice to Have (Can wait):
- ⏸️ All sections with LLM (can add later)
- ⏸️ Gemini integration (Claude + OpenAI enough for MVP)
- ⏸️ Advanced prompt engineering (basic prompts work)
- ⏸️ Benchmark integration (can hardcode for MVP)

---

## Risk Mitigation

### If LLM API fails:
- Graceful fallback to existing narratives
- Log error but don't break report generation

### If prompts need refinement:
- Start with simple, clear prompts
- Can iterate after MVP

### If time runs short:
- Focus on KAV section only (most important)
- Show proof of concept
- Other sections can use existing logic temporarily

---

## Files to Create/Modify

### New Files:
1. `api/services/llm/__init__.py` - Multi-LLM service
2. `api/services/llm/prompts.py` - Prompt templates
3. `api/services/llm/formatter.py` - Data formatting (Day 2)

### Files to Modify:
1. `api/services/report.py` - Replace narratives with LLM calls
2. `requirements.txt` - Add LangChain dependencies

### Files to Skip (for now):
- ❌ Remove deprecated files (can do after MVP)
- ❌ Full cleanup (can do after MVP)
- ❌ All sections with LLM (KAV + Flows enough for MVP)

---

## Daily Standup Questions

**End of Day 1:**
- Is LLM service working?
- Can we generate KAV insights?
- Any blocking issues?

**End of Day 2:**
- Is MVP report generating?
- Are insights appearing correctly?
- Ready for review?

---

## Success Criteria for MVP

The MVP is successful if:
1. ✅ Report generates with LLM insights in KAV section
2. ✅ At least 1-2 flow sections show LLM insights
3. ✅ No errors in report generation
4. ✅ Boss can see the automated insight generation working
5. ✅ System is clearly automated (not manual)

---

## Next Steps After MVP

Once MVP is approved:
- Get Carissa's prompts and refine ours
- Add LLM to remaining sections
- Integrate industry benchmarks
- Clean up deprecated code
- Full testing and refinement

---

**Remember:** MVP = Minimum Viable Product. Focus on proving the concept works, not perfection.

