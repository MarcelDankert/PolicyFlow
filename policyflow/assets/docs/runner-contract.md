# Runner Contract

PolicyFlow executes agent-owned phases through a provider-neutral command
contract. The runner can be any local CLI, hosted-model adapter wrapper, or
internal tool that reads PolicyFlow input JSON and writes PolicyFlow result JSON.
PolicyFlow core does not import provider SDKs and does not manage provider
credentials.

The broader evidence boundary for external runtimes, CI systems, and agent
frameworks is documented in
[provider-neutral-integration-contract.md](provider-neutral-integration-contract.md).
Source path: `docs/provider-neutral-integration-contract.md`.

## Runner Configuration

Use `type: command` for the generic adapter path:

```yaml
default_runner: command

runners:
  command:
    type: command
    command:
      - policyflow-runner
      - --input
      - "{input_path}"
      - --output
      - "{output_path}"
```

Supported command placeholders:

- `{input_path}`: temporary JSON file containing the PolicyFlow runner input
- `{output_path}`: temporary JSON file the runner must write
- `{workflow_path}`: workflow file passed to `policyflow run-phase`
- `{phase}`: requested workflow phase
- `{python_executable}`: Python executable running PolicyFlow

The command runs synchronously. Exit code `0` means the runner wrote valid output
JSON. Any non-zero exit code blocks the workflow phase with an actionable
runtime reason based on stderr, stdout, or the exit code.

## Input JSON

PolicyFlow writes a top-level JSON object with these fields:

- `workflow_path`: workflow file path
- `workflow`: full workflow document
- `phase`: requested phase
- `owner_agent`: expected PolicyFlow owner agent for the phase
- `prompt_text`: configured prompt text for the phase, when available
- `agent_text`: configured agent role text for the phase, when available
- `handoff`: inbound handoff object for the phase, when available

The runner should treat `workflow`, `prompt_text`, `agent_text`, and `handoff` as
inputs. It should not mutate the workflow file directly.

## Output JSON

The runner must write a top-level JSON object:

```json
{
  "phase": "implementation",
  "owner_agent": "senior-dev-agent",
  "status": "completed",
  "summary": "Implemented the approved scope.",
  "contract_updates": {
    "owner_agent": "senior-dev-agent",
    "implementation_summary": "Implemented the bounded change.",
    "changed_files": ["policyflow/example.py"],
    "test_summary": "Ran targeted tests.",
    "docs_updates": ["docs/runner-contract.md"],
    "known_limitations": ["none"],
    "unresolved_questions": ["none"]
  },
  "handoff": {
    "to_phase": "review",
    "required_inputs": ["implementation_summary", "test_summary"],
    "produced_outputs": ["review_findings"]
  }
}
```

Required fields:

- `phase`: must match the requested phase
- `owner_agent`: must match the expected PolicyFlow owner agent
- `status`: `completed` or `blocked`
- `summary`: short result summary

For blocked results, include `blockers` or a useful `summary`. PolicyFlow marks
the phase and runtime as blocked and reports the reason.

Optional fields:

- `evidence_updates`: evidence block for evidence-bearing phases
- `contract_updates`: role contract block for canonical agent-owned phases
- `handoff`: next handoff with `to_phase`, `required_inputs`, and
  `produced_outputs`

## Codex Reference Adapter

PolicyFlow ships `python -m policyflow.codex_runner` as a reference adapter for
Codex CLI. It reads the same input JSON, calls `codex exec`, and writes the same
PolicyFlow result JSON. Codex is not required for PolicyFlow runtime
orchestration; it is one provider-specific implementation of the generic command
contract.
