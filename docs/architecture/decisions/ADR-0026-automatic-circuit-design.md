# ADR-0026: Automatic design of circuits and runs

Status: accepted. Done: rooms in the drawing, the two-step proposal (`epc_plan.design`), its acceptance (drawing and board) and the Design tab of the layout editor. Date: 2026-10-27

## Context
Placing every load, assigning each to a circuit, drawing the trunk and the branches and routing the circuits is slow and repetitive. The rules are regular: each room is a circuit of each family of load it holds, a circuit has a maximum number of outlets (15 for lighting), the cables run in trays and conduits from the board to each outlet.

## Decisions
1. **Rooms are part of the drawing.** The person marks each room with its outline and a name (tool "Ambiente"); the rooms are stored with the sheet (`rooms`) and the engine that reads the drawing never sees them. Rooms are not derived from recognized walls: that recognition is not yet reliable on real plans (ADR-0025).
2. **The design has two steps, each a pure function.** Step 1, `propose_runs`: the loads and the board in; straight trunks (BN trays) and one stub (CN conduit) per load off a trunk out, with the fewest trunks and no bends (dynamic programming over the number of trunks, horizontal or vertical, one spine from the board; the shorter wins). It is shown as a preview and accepted before anything else. Step 2, `propose_wiring`: the drawing with the accepted runs and its rooms in; circuits (one per room and family, split evenly over the limit), the circuit of every load and warnings out, each circuit checked by routing it with the engine over the runs. Neither changes nor saves anything. Known limit: the runs follow the median row/column of the loads, not the walls.
3. **Circuits.** One per room and family of load (the family is a property of the kind in the profile: lighting IUG, general sockets TUG, special sockets TUE, air conditioning ACU); a room with more loads than the limit is cut along the longer side of its loads into the fewest balanced groups. Tags are `IUG-01...`, skipping those already taken in the board.
4. **Trunk and branches.** Trays (`BN`) leave the board and reach the entrance of each room, sharing what is already laid; one conduit (`CN`) per circuit goes from the entrance through its loads in the order of the shortest chain. All runs are horizontal and vertical. A circuit's cable is not a line of its own: it follows the conduits, as the engine already models (each stretch records the circuits it carries), so lengths are not counted twice.
5. **Limits and powers are data.** `params.json` (`design.families`) holds the maximum outlets per circuit and the power per outlet; the person may change them in the panel for the proposal. They are typical values: the engineer confirms them against the standard of the project.
6. **The person accepts.** Applying a proposal adds its lines, sets the circuit of each load and the routed circuits (origin the board, destination its last load) in the drawing, as one undoable change, and creates the circuits in the board with their power in VA (`sld.public.add_circuits`: a tag the board already has is left alone; the first board is created when there is none). The layout still never creates circuits on its own.

## Limits (known, accepted)
- Runs do not know about walls: they are straight and orthogonal and may cross a wall where there is no door. Using the recognized walls and doors to route is the next step.
- A branch that crosses a trunk or another conduit gives the engine's warning "cross without a node": they are drawn, not joined.
- Circuits are made per family and room; mixed circuits (lighting and sockets together), three-phase circuits and sizing the cable are the calculation engine's work afterwards, with the lengths the routes now give.
- The power per outlet becomes the load of the board circuit (VA); until confirmed it is a placeholder.
