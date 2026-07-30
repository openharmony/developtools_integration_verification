# AGENTS.md — OpenHarmony 集成验证

## Scope and responsibility

This repository defines OpenHarmony CI pipeline gate smoke tests and daily build tests at `developtools/integration_verification`. Test cases reference test binaries produced by each subsystem's own GN build. **This repository has no build system of its own** — test binaries are built externally.

## Code map

### Top-level layout

| Directory | Responsibility | Risk |
|---|---|---|
| `cases/smoke/` | CI gate smoke test definitions and runners | **High** — gate CI pipeline correctness |
| `cases/daily/mini_system/` | Daily build mini-system tests (L0/L1/L2) | Medium — daily CI diagnostics |
| `tools/deps_guard/` | ELF dependency guard (also wraps startup_guard) | Medium — CI architecture enforcement |
| `tools/startup_guard/` | Startup resource guard | Medium — CI architecture enforcement |
| `tools/rom_ram_analyzer/` | ROM/RAM analysis (`standard/` for GN-template builds, `lite_small/` for static BUILD.gn scanning) | Low |
| `tools/opensource_tools/` | The only pip-installable Python package in this repo (setuptools, Python ≥3.8) | Medium — distributed as package |
| `tools/fotff/` | Go 1.19 CI fault bisection tool (Cobra CLI) | Medium — CI diagnostics |
| `tools/check.py` | PR file path checker (executes on import, no `if __name__` guard) | Medium — run by CI on PRs |
| `tools/precise_build/` | Precise build analysis | Low |
| `tools/components_deps/` | Component dependency analysis | Low |
| `tools/code_access_control/` | Code access control checks | Low |
| `tools/gated_check_in/` | Ace engine TDD gate check | Low |
| `tools/arkui_tools/` | ArkUI header file count analysis | Low |

### Where to look for common tasks

| Task | Start here | Read first |
|---|---|---|
| Add or change a smoke test | `cases/smoke/basic/screenshot32/new_script/testcases/` or `.../screenshotP7885/new_script/testcases/` | `cases/smoke/repo_cases_matrix.csv` + `testcases.json` |
| Add board support to the test matrix | `cases/smoke/repo_cases_matrix.csv` | Column schema: repo → bundle → board → Y/N → test binary names |
| Change the smoke test runner | `cases/smoke/basic/screenshot32/new_script/main.py` and `.../screenshotP7885/new_script/main.py` | BOTH files must be kept in sync |
| Change device interaction (hdc, snapshot, layout) | `cases/smoke/basic/*/new_script/utils/device.py` | BOTH screenshot variants must be updated |
| Change daily build tests | `cases/daily/mini_system/L*_mini_system_test.py` | argparse signature; these are standalone scripts, not pytest |
| Change ELF dependency rules | `tools/deps_guard/deps_guard.py` | `tools/deps_guard/rules/` — whitelist JSON files |
| Change startup guard rules | `tools/startup_guard/startup_guard.py` | `tools/startup_guard/rules/` — whitelist JSON files |
| Change ROM/RAM analysis | `tools/rom_ram_analyzer/standard/` or `tools/rom_ram_analyzer/lite_small/` | Do NOT mix standard/ and lite_small/ tooling |
| Change opensource tools logic | `tools/opensource_tools/src/` | `tools/opensource_tools/test/conftest.py` + matching test files |
| Change fotff Go logic | `tools/fotff/main.go` | `tools/fotff/fotff.ini` + `go.mod` (Go 1.19) |
| Change PR file checker | `tools/check.py` or `tools/code_access_control/check_arkweb_hard_coded.py` | These execute on import — no `if __name__` guard |
| Add a new tool | `tools/` | If Python, follow argparse pattern; if pip-installable, use `tools/opensource_tools/` as template |

### Nested guidance

- The skill at `.opencode/skills/ohos-design-agent-instruction-quality-review/SKILL.md` applies when reviewing AGENTS.md files.
- `tools/deps_guard/README.md` and `tools/startup_guard/README.md` contain rule-authoring guidance.
- `tools/components_deps/README.md` explains component dependency analysis usage.
- `tools/fotff/README.md` documents fotff architecture and configuration.

---

## Knowledge routing

### Before editing, you MUST

1. **State** your task category from the lists below.
2. **Read** every document listed for that category.
3. **Report** what you read and which constraints you found.
4. **Then** proceed with the change.

### Task-based routing

| If your task involves | Read these first |
|---|---|
| Smoke test definitions, test matrix, or test runner | `cases/smoke/repo_cases_matrix.csv` schema (cols: repo, bundle, boards..., test binaries), then `cases/smoke/basic/*/new_script/testcases.json` |
| Device interaction (hdc, screenshot, UI layout) | `cases/smoke/basic/screenshot32/new_script/utils/device.py` and `.../screenshotP7885/new_script/utils/device.py` — note differences in coordinate systems |
| Daily build mini-system tests | The argparse signature of the relevant `L*_mini_system_test.py` — serial port, archive path, save path |
| ELF dependency checking | `tools/deps_guard/deps_guard.py` argparse + relevant `rules/*/whitelist.json` files |
| Startup resource checking | `tools/startup_guard/startup_guard.py` argparse + relevant `rules/*/whitelist.json` files |
| ROM or RAM analysis | `tools/rom_ram_analyzer/standard/rom_analyzer.py` argparse OR `tools/rom_ram_analyzer/lite_small/src/rom_analysis.py` + `config.yaml` |
| Opensource tooling (spdx, license, README) | `tools/opensource_tools/test/conftest.py` + the matching `test_*.py` file |
| Go CI fault bisection | `tools/fotff/main.go` + `tools/fotff/fotff.ini` + `tools/fotff/go.mod` |
| PR file content checking | `tools/check.py` and `tools/code_access_control/check_arkweb_hard_coded.py` — both execute on import |

### Path-based routing

| When changing files under | Also read |
|---|---|
| `cases/smoke/basic/screenshot32/` | The mirror file in `cases/smoke/basic/screenshotP7885/` — identical structure, different content (resolution variant) |
| `cases/smoke/basic/screenshotP7885/` | The mirror file in `cases/smoke/basic/screenshot32/` |
| `tools/deps_guard/` | `tools/startup_guard/startup_guard.py` — deps_guard dynamically imports and wraps it |
| `tools/rom_ram_analyzer/standard/` | Do NOT reference files in `lite_small/` — different methodology |
| `tools/rom_ram_analyzer/lite_small/` | Do NOT reference files in `standard/` — different methodology |
| `tools/check.py` | `tools/code_access_control/check_arkweb_hard_coded.py` — same pattern, ArkWeb checks |

### Vocabulary

| Term | Meaning |
|---|---|
| 门禁 (gate) | CI pipeline gate — must pass to merge |
| 冒烟 (smoke) | Smoke test — basic functionality verification |
| 单板 (board) | Target hardware board / single-board computer |
| bundle | Subsystem grouping in the test matrix |
| L0 / L1 / L2 | System levels: L0 = lightweight (liteos_m), L1 = small (liteos_a), L2 = standard (linux) |
| hdc | OpenHarmony Device Connector — like adb for OHOS devices |
| GN | Generate Ninja — the build system used by OpenHarmony |
| DFX | Design for X — logging, tracing, fault attribution, observability |
| snapshot | Screenshot captured via hdc on device |
| SN | Device serial number |

---

## Constraints and boundaries

### Do not

- **Modify `cases/smoke/repo_cases_matrix.csv` column names or schema** — this file is parsed programmatically by CI; changing columns breaks matrix parsing.
- **Modify `testcases.json` structure (key names, nesting)** — parsed by `main.py`; changing the schema breaks test discovery.
- **Change the argparse interface of any tool** — tools are called by CI scripts with fixed arguments; adding required args or renaming flags breaks CI.
- **Change only one screenshot variant** — `screenshot32/` and `screenshotP7885/` must stay functionally congruent. Any logic change in one requires the corresponding change in the other.
- **Mix `standard/` and `lite_small/` ROM/RAM analysis tooling** — they use different analysis methodologies (GN-template vs. static BUILD.gn scanning).
- **Add Python dependencies outside `tools/opensource_tools/`** — other tools must run in the CI environment with only the Python standard library.
- **Import or run `tools/check.py` or `tools/code_access_control/check_arkweb_hard_coded.py`** as a module — they execute on import. Set `PR_FILE_PATHS` env var before running.
- **Assume any test runner uses pytest** — only smoke tests (via `pytest.main()`) and `tools/opensource_tools/` use pytest. Daily tests and standalone tools use argparse.
- **Run smoke tests or daily tests without a connected device** — these require a physical device or emulator with hdc/com port access.
- **Commit `.pyc`, `.pyo`, or `__pycache__/`** — `.gitignore` covers these only.

### Ask before

- Adding, removing, or renaming a tool directory under `tools/`.
- Adding a new pip dependency to `tools/opensource_tools/requirements.txt` or `pyproject.toml`.
- Changing the `pytest` invocation pattern in `cases/smoke/basic/*/new_script/main.py`.
- Modifying `tools/fotff/fotff.ini` — controls daemon loop behavior, tester selection, and device configs.
- Changing Go module dependencies in `tools/fotff/go.mod` (Go 1.19).
- Modifying `tools/opensource_tools/pyproject.toml` — affects package build and distribution.
- Adding a new rule directory under `tools/deps_guard/rules/` or `tools/startup_guard/rules/`.
- Changing the Python version requirement (currently Python ≥3.8 for `opensource_tools`, Python 3 for everything else).

### Invariants

- **No build system**: This repo does not build. Do not add Makefiles, CMakeLists.txt, BUILD.gn, setup.py, or build scripts (except `tools/opensource_tools/pyproject.toml` which already exists).
- **Test binaries are external**: `.bin` files named in `repo_cases_matrix.csv` are built by other repositories. Do not attempt to create, generate, or locate them within this repo.
- **No lint/typecheck/format config**: The repo intentionally has none. Do not add `.flake8`, `pyproject.toml` linter configs, `mypy.ini`, or formatter configs.
- **No CI config in repo**: CI is managed externally by OpenHarmony infrastructure. Do not add CI workflow files (`.github/workflows/`, `Jenkinsfile`, etc.).
- **Two screenshot directories, same structure**: `screenshot32/` and `screenshotP7885/` have identical file trees but different content. They are resolution variants — 720×1280 vs. P7885 tablet resolution. P7885 variant uses relative coordinates; screenshot32 uses hardcoded pixels.

### Common agent failure patterns

- **Editing only one screenshot variant**: If you change `screenshot32/new_script/conftest.py`, you must also change `screenshotP7885/new_script/conftest.py` with the resolution-appropriate equivalent.
- **Trying to `pip install` whole repo**: Only `tools/opensource_tools/` is a pip-installable package. Running `pip install .` at repo root will fail.
- **Assuming `__name__ == "__main__"` guard exists**: `tools/check.py` and `tools/code_access_control/check_arkweb_hard_coded.py` execute immediately on import. Do not import them for inspection — read them with a file reader instead.
- **Running hardware tests without hardware**: Smoke tests need `--device_num <SN>`, daily tests need `--com_port`. These will hang or crash without a connected device.
- **Renaming test files under `cases/smoke/basic/*/new_script/testcases/`**: Test file names are likely referenced in `testcases.json`. If they are, renaming breaks test discovery.

---

## Verification

### Minimum checks (run after every change)

```bash
# Syntax-check all changed Python files
python -m py_compile <changed_file.py>

# If changes touch tools/opensource_tools/ (the only offline-testable area):
cd tools/opensource_tools && pip install -r requirements.txt && pytest
```

### Task-specific verification

| If you changed | Verify by |
|---|---|
| `tools/opensource_tools/src/` | `cd tools/opensource_tools && pip install -r requirements.txt && pytest` |
| `tools/opensource_tools/test/` | Same as above |
| `tools/fotff/` Go code | `cd tools/fotff && go build ./... && go vet ./... && go test ./...` |
| Smoke test runner (`main.py`, `conftest.py`, `utils/`) | Requires device: `python cases/smoke/basic/screenshot*/new_script/main.py --device_num <SN> --save_path ./report` |
| Daily mini-system tests | Requires device: `python cases/daily/mini_system/L*_mini_system_test.py --com_port <COM> --archive_path <path> --save_path <dir>` |
| Architecture guard tools | Requires build output: `python tools/deps_guard/deps_guard.py -i <out_path>` |
| Any tool with argparse | `python <tool>.py --help` — confirm the interface is unchanged |
| Any standalone Python script | `python -m py_compile <file>` — at minimum confirm valid syntax |

### Done definition

Before reporting a task as complete, confirm:

1. `python -m py_compile` passes on every changed `.py` file.
2. If `tools/opensource_tools/` is touched, `pytest` passes.
3. If `tools/fotff/` Go code is touched, `go build` and `go vet` pass.
4. Any `screenshot32/` change has a corresponding `screenshotP7885/` change (or you have explicitly stated why not).
5. argparse interfaces are preserved (run `--help` to confirm).
6. No new dependencies were added outside `tools/opensource_tools/`.

### Final response format

When reporting completion, include:
- Files changed and why.
- Commands run for verification (with results).
- Any verification steps you could not run and why (e.g., "smoke test requires physical device with SN, I only verified syntax and argparse signature").
- Which constraints from the Constraints section apply to your change and how you satisfied them.

### Fallback: when validation cannot be run

Most tools require a connected device or build output that is unavailable in a development environment. In this case:

1. At minimum, run `python -m py_compile` on every changed Python file.
2. Run `python <tool>.py --help` to confirm argparse interface is intact.
3. State explicitly: "Full validation requires `<resource>` which is not available. I verified syntax and interface. Manual test with `<resource>` is needed before merge."
4. If you cannot syntax-check (e.g., the env lacks Python 3), flag this as a blocker.
