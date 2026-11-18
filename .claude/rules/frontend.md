---
paths:
  - "frontend/**"
---
# Frontend rules
- TypeScript strict; no `any` without justification.
- Reusable components; no copy-pasted UI.
- All API calls go through the typed client; handle errors visibly and meaningfully.
- Every data view has loading, empty, and error states.
- Accessible: semantic elements, labels, keyboard operation, focus management, contrast.
- No decorative or nonfunctional controls (dead buttons, fake data, placeholder links).
- Never expose secrets or tokens to client code.
