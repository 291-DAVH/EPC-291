# Findings while characterizing the code (not fixed: this is a refactoring, behaviour stays)

Each one is pinned by a characterization test as it behaves today. They are decisions for after the refactoring.

| # | Where | What | Pinned by |
|---|---|---|---|
| F1 | `management/workflow/scripts/test_workflow.py` | The tests were written for another project layout (they read `90_MANAGEMENT/DELIVERABLES.md`); 26 of 27 error out in this repository. The gate never ran them. Step E0.3 (a `workflow` check) is **discarded** until they are adapted to this layout. | not runnable |
| F2 | `epc_calc.aea_feeder_report.verificaciones` | The feeder report does not apply the pipeline's rule "XLPE without a method means B2": aluminium XLPE feeders without an explicit method fail with `B1 con XLPE no tiene tabla`. The pipeline handles the same circuit. | `engine/calc/tests/golden/core.json` (`feeder_reports.al_xlpe`) |
| F3 | `epc_drawing.sld.sld_generator` | Sizes the main supply cable (acometida) and, without the pipeline's result, the whole circuit with its own simplified formulas (R = 1000/56S, X = 0.08), its own In/Icu series and ampacity tables. | (golden SLD tests, step S1.4) |
| F4 | `backend/.../intake/analyzer.py` | Forces a tool call (`tool_choice` of type `tool`) on the default model `claude-sonnet-5-5`, which the current API rejects. | not testable without the real API |
| F5 | `epc_calc.aea_pipeline.resolver_criterios` | Default insulation is `PVC` while the design-criteria catalog default is `XLPE`. | `golden/pipeline.json` (cases without criteria) |
| F6 | `epc_calc.aea_feeder_report` | Uses Ib for the voltage drop of lighting feeders where the pipeline uses 66 % of it at the end of the line. | `golden/core.json` |
| F7 | `sld_generator` / `mld_generator` | The 30 mA sensitivity is written in the drawings and ignores the `rcd_sensitivity_ma` criterion. | (golden SLD tests) |
| F8 | `management/workflow` vs `issuing` | Emission vocabularies differ (`IFR/IFA/IFC/AS_BUILT` vs `ifa/ifc/as-built`). | not tested |
