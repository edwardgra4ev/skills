<!-- Adapted for Codex from ibmbpm/ibm-baw-skills-and-bob-modes; see NOTICE. -->
# BAW documentation

Generate comprehensive Markdown documentation for an IBM BAW application. No MCP server
or live server connection required.

## Input paths

Three input types are accepted: a TWX export, a BPMN + XSD pair, or a ZIP archive
containing a BPMN + XSD.

### Step 0 — Resolve the input and audience

Use the supplied path first. If none was supplied, discover relevant TWX/BPMN/XSD files in the working project. Ask which input to use only when the context is ambiguous. If no artifact is available, explain how to export one using the target version's Workflow Center or Business Automation Studio.

Use the requested audience. If unspecified, default to a technical reference and state that assumption. Available profiles are executive summary, knowledge transfer, partner handoff and technical reference; their formats are in references/AUDIENCE_FORMATS.md.

### Path A — TWX file

A BAW process application or toolkit export (`.twx`).

**Coverage:** processes, services (all types), business objects, coach views.

---

### Path B — BPMN + XSD pair (or ZIP)

A `.bpmn` file and companion `.xsd` produced by the `generate-baw-bpmn` skill.
If the user provides a `.zip`, unzip it first to locate the `.bpmn` and `.xsd` inside.

**Coverage:** process flow, roles/lanes, all steps and decisions, process variables,
business objects and their fields. Services and coach views are not available from
this input type — note this in the Assumptions & Gaps section.

---

## Steps

### 1 — Discover and identify input

Follow Step 0 above to scan the workspace and confirm the file with the user (or
request one if nothing is found). Once you have a confirmed file path, determine
which input path applies (A = TWX, B = BPMN+XSD or ZIP) and collect the data.

### 2 — Read the reference files

Before generating documentation, read:
- For Path A: `references/TWX_ANALYSIS.md`
- For Path B: `references/BPMN_XSD_ANALYSIS.md`
- Always: `references/DOCUMENTATION_OUTPUT.md` — Technical Reference output structure,
  section order, table formats, and Mermaid diagram conventions
- Always: `references/AUDIENCE_FORMATS.md` — output structures for all four audiences

### 3 — Generate the documentation

Use `<AUDIENCE>` to select the correct output structure and file path from
`references/AUDIENCE_FORMATS.md`. Generate the documentation accordingly.

| Audience | Output file |
|---|---|
| Executive summary | `docs/baw/<AppName>/<AppName>-executive-summary.md` |
| Knowledge transfer (KT) | `docs/baw/<AppName>/<AppName>-kt-guide.md` |
| Partner handoff | `docs/baw/<AppName>/<AppName>-partner-handoff.md` |
| Technical reference | `docs/baw/<AppName>/<AppName>-documentation.md` |

Follow the structure defined in `references/AUDIENCE_FORMATS.md` for the selected
audience exactly. For **Technical reference**, follow `references/DOCUMENTATION_OUTPUT.md`
exactly as before — nothing changes for that audience.

**Content rules by audience:**

- **Executive summary:** Omit all implementation detail. No service steps, no Mermaid
  diagrams, no field-level business object tables. Lead every section with business
  context. If a section would only contain implementation detail, omit it.

- **Knowledge transfer (KT):** Include everything from Technical Reference, plus a
  step-by-step narrative walkthrough for each process, developer notes on each service,
  and a developer onboarding checklist. Flag any known issues or technical debt.

- **Partner handoff:** Include process flows and business objects at standard depth.
  Replace the Assumptions & Gaps section with a populated Improvement Recommendations
  table. Identify recommendations from: missing descriptions, hardcoded values that
  should be environment variables, undocumented endpoints, missing error handling,
  and deprecated service types.

- **Technical reference:** Follow `references/DOCUMENTATION_OUTPUT.md` unchanged.

If a section has no data, include the heading with a note — never silently omit a section
(except for Executive summary, where implementation-only sections are intentionally excluded).

### 4 — Post a plain-language summary in chat

After writing the file, post a conversational summary **directly in the chat response**
(not as a file). Tailor the summary content and tone to `<AUDIENCE>`:

**Executive summary audience:**
Lead with the business purpose in one paragraph. Follow with key roles (inline list)
and the main business outcome. No diagrams, no technical terms. Close with:
> Full executive summary written to `docs/baw/<AppName>/<AppName>-executive-summary.md`.

**Knowledge transfer (KT) audience:**
One paragraph on what the app does. Then bullet-point the most important things a
new developer needs to know: key integration dependencies, any known quirks, data
that flows through the process, and any open issues. Close with the onboarding checklist
preview and:
> Full KT guide written to `docs/baw/<AppName>/<AppName>-kt-guide.md`.

**Partner handoff audience:**
One paragraph describing what is being handed off. Mermaid diagram of the main process
flow. Then list the top improvement recommendations (up to 5, most impactful first).
Close with:
> Full partner handoff document written to `docs/baw/<AppName>/<AppName>-partner-handoff.md`.

**Technical reference audience:**
Follow the existing Step 4 format exactly:

`<App Name> — Project Summary`

One short paragraph: what the application does and who uses it.

**Process Flow** — Mermaid diagram of the main BPD, followed by:
- Swimlanes list (inline)
- **Key decisions** bullet list
- **Process variables**: inline list

**Services (`N` total)** — compact table: Service | Type | Purpose.

**Coach Views (`N`)** — compact table: View | Purpose.

**Notable gaps** — short bullet list.

Close with:
> Full technical documentation written to `docs/baw/<AppName>/<AppName>-documentation.md`.

**Tone rules (all audiences):**
- Write in the user's language. Avoid BAW jargon unless the term is immediately explained.
- Be concrete: name the roles, name the decisions, name what data flows through.
- Keep the summary readable without needing to open the document.

## Boundaries

**In scope:**
- Documenting from a TWX export, a BPMN+XSD pair, or a ZIP containing BPMN+XSD
- Running `extract_twx.py` for TWX inputs; direct XML parsing for BPMN+XSD inputs
- Documenting all artifact types present in the input
- All four audience output formats

**Out of scope — redirect clearly:**
- **REST API path:** not in scope
- **MCP path** (`get_process_model`, `export_solution_expanded`): not in scope
- **Deploying to BAW or managing versions**: use `baw-deployment-manager` or `version-lifecycle-manager`
- **Generating new BPMN from descriptions**: use `generate-baw-bpmn`
- **Generating or modifying Business Object import files**: use `generate-baw-business-objects`
- **Creating coach widgets or task portals**: use `create-baw-widget` or `create-baw-portal`
- **Modifying the application being documented**: this skill is read-only
