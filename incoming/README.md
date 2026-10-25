# incoming/

Modules developed on their own (in another chat, on another machine) waiting to be integrated into the platform. Each folder follows `docs/modules/MODULE-CONTRACT.md`.

- **Start a module:** `python tools/dev/new_module.py <name>` creates `incoming/<name>/` with the contract, the prompt for a new chat, tests, a demo and, if you want it, a screen.
- **Work on it elsewhere:** copy the folder (it needs nothing else), open it in a new chat and paste `PROMPT-FOR-A-NEW-CHAT.md`.
- **Hand it over:** copy it back here as `incoming/<name>/` and ask for it to be integrated (contract, section 9).
- Nothing here is part of the platform's gate or of its builds until it is integrated.
- Books, plans and any client file never go here: they stay in `local/dev-knowledge/` (ignored by git).
