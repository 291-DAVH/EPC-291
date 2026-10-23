---
name: "structure-customer-input"
description: "Analyzes information sent by the customer (voice of customer, user stories, meeting notes, documents), removes noise and duplicates, and stores it as structured, verifiable requirements with acceptance criteria and open questions."
---

# structure-customer-input

Owner plugin: `intake-analysis`. Script: `claude/plugins/intake-analysis/scripts/intake.py`.

The end user never sees this work. They see their item change from *Received* to *Under analysis* to *Turned into requirements*, and then the requirements. Do not mention tools, models, plugins or internal files in anything written for them.

## Automatic path
The backend runs this same analysis through the Claude API (`backend/src/epc/modules/intake/analyzer.py`): it sends the pending items (text only, amounts replaced by `[importe omitido]`, no attachments), forces a `submit_analysis` tool call in the format below, validates it with `intake.py` (`validate`) and stores it with `intake.py` (`apply`), so an automatic run and a manual run leave identical files. In the web app: project > Input data > *Analizar con Claude* (admin/engineer; the key `ANTHROPIC_API_KEY` is set on the server and the engineer confirms that the text leaves the server). Every call is recorded in `workspace/01-input/intake/analysis_usage.json`. The manual workflow below remains valid.

## Hard rules
1. **No invented data.** Every figure, name or condition must come from the input. If something is missing, write it as an open question; never fill it in.
2. **Confidential money.** Prices, budgets, fees, amounts and commercial conditions are not copied anywhere (requirement text, acceptance criteria, questions). Record only that economic information exists. The tool rejects amounts.
3. **One requirement = one verifiable statement** (max 300 characters). Split compound needs. Keep the customer's intent; remove the emotion and the story.
4. **Traceability.** Each requirement lists the intake ids it came from (`source_intake`).
5. **Language.** Write requirements in the project's locale (`es-AR` by default). Explain your work to the user in Spanish.
6. A decision that changes scope, schedule or design is not a requirement to record silently: put it in `open_questions` and tell the engineer.

## Workflow
1. `python intake.py pending --project CLIENT/CODE` (or without `--project` for every project). Read `pending` and `existing_requirements`.
2. For each pending item decide:
   - **New requirement(s):** rewrite the need as verifiable statements. Classify:
     - `type`: `funcional` (what the system does), `no funcional` (quality: availability, safety, noise, performance), `restricción` (limits: deadline, standard, budget class, access), `documental` (what must be delivered and in which form);
     - `priority`: `alta` if it affects safety, continuity of operation, a contractual deadline or an authority/insurer requirement; `media` by default; `baja` for preferences;
     - `discipline`: electrical, civil, hvac, fire, mechanical, instrumentation, telecom, or `general`.
   - **Merge** into an existing requirement when it says the same thing (`merge_into`), adding the new source.
   - **Keep analyzing** (`intake_status: analyzing`) when you cannot write a verifiable statement without asking something; list the questions.
3. Add `acceptance` criteria: how the engineer will prove it is met (a document, a test, an approval). Prefer measurable criteria already implied by the input; otherwise leave the number as an open question.
4. Write the analysis JSON (format in the script header) and run `python intake.py apply CLIENT/CODE analysis.json`. Fix every rejection; nothing is written until it is valid.
5. Report to the engineer in Spanish: what was created or merged, the open questions to ask the client, and anything that needs a decision.

## Quality checklist
- Would two engineers read the statement the same way?
- Can you tell, without asking, when it is satisfied?
- Is the priority justified by safety, continuity, deadline or authority?
- Did every open question come from a real gap in the input?
