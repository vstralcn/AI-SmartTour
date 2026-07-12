---
name: testing-smarttour
description: Test AI-SmartTour end-to-end through the tourist and admin UIs. Use when verifying Docker Compose startup, Agent traces, trusted RAG sources, constrained route planning, or knowledge evidence.
---

# Test AI-SmartTour

## Start and verify the stack

```bash
docker compose up -d --build --wait
docker compose ps
```

Require `backend`, `tourist-app`, `admin-panel`, `postgres`, and `redis` to be healthy before UI testing.

## Primary UI flow

1. Open `http://localhost:3000`.
2. Select `历史文化` and click `开始智能导览`.
3. Verify the greeting reflects the selected interest.
4. Ask `景区几点开门？`.
5. Verify:
   - the answer contains `8:00-18:00`;
   - `Agent 执行轨迹` reports an FAQ match with `100%`;
   - `回答依据` shows `常见问题 FAQ` and `100%`.
6. Ask `带孩子游玩3小时，请规划路线`.
7. Verify:
   - profile trace contains `历史文化、亲子游玩`;
   - route trace contains `3 小时和 2 个兴趣标签`;
   - the answer contains `5个景点` and `180分钟`;
   - the planning basis contains the duration and both interests.
8. Ask `月球基地土豆产量多少？`.
9. Verify an explicit insufficient-evidence response, a no-result knowledge trace, and no source card.

## Admin evidence flow

1. Open `http://localhost:3001/knowledge`.
2. Enter `景区几点开门？` in `知识库测试`.
3. Click `测试`.
4. Verify the answer, `置信度 100%`, `景区常见问题`, and the `常见问题 FAQ` evidence excerpt are visible together.

## Recording and evidence

- Maximize Chrome before recording.
- Record the complete tourist and admin flows.
- Add `setup`, `test_start`, and consolidated `assertion` annotations.
- Capture full-screen evidence for FAQ sources, route traces, refusal, and admin evidence.
- Write a separate `test-report.md` with inline uploaded screenshots.

## Browser input note

If native computer automation does not emit Chinese characters, attach to the existing Chrome session through CDP and fill only the form field, dispatching a standard `input` event. Continue navigation, submission, and verification through visible UI interactions.

## Devin Secrets Needed

- None for the default local trusted-fallback flow.
- `LLM_API_KEY` is optional and only needed when explicitly testing Qwen-enhanced generation.
- Never commit `.env` or API keys.

## Out-of-scope profiles

- MuseTalk requires `docker compose --profile gpu up --build` and an NVIDIA-capable environment.
- Do not treat the GPU path or external Qwen path as tested unless their prerequisites are explicitly available and included in the test plan.
