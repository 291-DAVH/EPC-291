# What is an EPC?

**EPC = Engineering, Procurement, Construction.** A delivery model in which **one contractor** designs a facility, buys its equipment and materials, builds it and commissions it, normally for a fixed price and date. The same model appears as LSTK (lump-sum turnkey), EPCC or EPIC; the usual standard form is the FIDIC Silver Book. The contractor carries most technical and financial risk (cost overruns from design change or procurement problems), which is why scope clarity and traceability matter so much. A variant, **EPCM**, gives the contractor a management role instead of full execution risk.

Sources: [IEEE Technology Navigator: turnkey project](https://technav.ieee.org/topic/turnkey-project/), [John F. Hunt: EPC contracts](https://www.johnfhunt.co.uk/blog/construction/epc-construction-contracts/), [Hogan Lovells: EPC or EPCM](https://www.hoganlovells.com/publications/epc-or-epcm-contracts), [PM Study Circle: EPC contracts](https://pmstudycircle.com/epc-contracts/).

## Lifecycle

| Stage | What happens | Typical output | In EPC-291 |
|---|---|---|---|
| Concept / pre-FEED | Design basis, feasibility, boundaries of the concept | Design basis, options | phase `IC`, `starting-data`, charter |
| FEED (basic engineering) | Scope, preliminary engineering, cost estimate (about +/-15-20 %) | Philosophies, P&IDs, datasheets, line lists, plot plan | phase `IB` |
| Detailed engineering | Approved scope becomes build-ready documents (IFC) | Calculations, drawings, specifications, datasheets | phase `ID`, `IE`; calc / drawing engines |
| Procurement | Buy, expedite, inspect | RFQs, bid comparisons, purchase orders, MTO/BOM | procurement module |
| Construction | Build, supervise, control changes | Site RFIs, redlines, punch lists | construction module |
| Commissioning and handover | Test, start up, deliver documents | Protocols, as-built, close-out | phase `ASB` |

Sources: [Phases of the oil and gas project life-cycle](https://whatispiping.com/phases-of-a-project/), [McGough EPC white paper](https://www.mcgough.com/wp-content/uploads/2026/03/EPC-White-Paper-Final.pdf). The sources differ on stage names and boundaries; the table is a working synthesis.

## The artifacts that drive an EPC project
- **MDR / MDL (master document register / list):** every document to be delivered, by discipline and phase, with its metadata. Once agreed it becomes part of the contract. In EPC-291 this is the `LME` (deliverables master list). Source: [OpenText on the MDR](https://blogs.opentext.com/understanding-the-master-document-register-within-an-engineering-capital-project/).
- **WBS (EDT):** engineering is broken down by discipline, then area/location, then work items, then deliverables. A WBS dictionary defines each element, and the filing structure follows the same levels. Source: [Planning Planet: WBS for an EPC project](https://planningplanet.com/comment/65151).
- **Engineering work packages (EWP) -> construction work packages (CWP):** a set of engineering deliverables that later feeds a construction package. In EPC-291 an EWP is a review package `PQ-nn`.
- **Document control:** revisions, transmittals and review status. The recurrent failures are version confusion, inconsistent transmittals, unclear review status and missing audit evidence. EPC-291 answers with state-by-location, SHA-256 ledger and one-way publish to `deliverables/`.

## Who is who
| Role | Meaning here |
|---|---|
| Owner / client | Defines requirements, approves deliverables (we receive their *voice of customer*) |
| EPC contractor | Our user: the engineering office or EPC company using the platform |
| Discipline engineers | Electrical, civil, HVAC, fire protection, mechanical, instrumentation, telecom |
| Reviewer / auditor | Independent checks before anything is issued |
| Document controller | Numbering, revisions, transmittals |

## Consequences for the software
1. The product is **document- and traceability-centric**: requirement -> deliverable -> drawing -> issue.
2. It must support **several disciplines** and **phases** on the same documents (they mature, they are not copied).
3. **Management** (WBS, schedule, risks, changes, MDR) is a first-class domain, not an add-on.
4. The **client portal** shows deliverables, data and reports only; the engineering machinery stays invisible.
