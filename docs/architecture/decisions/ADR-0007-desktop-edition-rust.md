# ADR-0007: Desktop edition with Rust (Tauri), engine stays in Python

Status: Proposed. Date: 2026-10-23.

## Context
The product must also run as a cross-platform desktop application (Windows, macOS, Linux): offline work, no server to install, data on the user's machine. The owner wants the desktop version built with Rust. The engineering engine (`engine/`) is mathematics-heavy and already written and tested in Python (NumPy-style calculations, rules, drawing, documents); rewriting it would cost time and risk new numerical errors in a domain where results are checked against standards.

## Decision
- The desktop shell is a **Rust application built with Tauri**: native window, installer, auto-update, file dialogs, secure local storage. Rust owns everything that touches the operating system.
- The UI is the existing React app (`frontend/web`, plus `frontend/console` for the admin role), rendered by the system webview. No second UI is written.
- The **engineering engine and the backend stay in Python**. The desktop edition ships them as a bundled **sidecar** process (the same `backend/` code frozen with PyInstaller or similar) that Tauri starts on a random local port, bound to 127.0.0.1 with a per-session token, and stops on exit.
- Local state uses **SQLite** (ADR-0006: the repository layer hides the engine); project files stay in a folder the user chooses.
- Rust may later take over isolated, performance-critical pieces behind the same interfaces (for example geometry or large batch calculations) once a benchmark justifies it; that is an optimization, not a rewrite.

## Consequences
- (+) One engine and one UI for web, desktop and Claude Code: a calculation is fixed once.
- (+) Small native binary, no Electron; Rust gives a solid base for signing, updates and OS integration.
- (-) Packaging Python inside the installer increases size and needs per-platform builds and signing (CI matrix on three operating systems).
- (-) Two toolchains (Rust and Python) in the desktop build; mitigated by keeping Rust code small and in `desktop/`.
- (-) Authentication, subscriptions and licensing need an offline mode (US-0027).
- Open question for the owner: acceptable installer size and whether the desktop edition must work fully offline from day one.
