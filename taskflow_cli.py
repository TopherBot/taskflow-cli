#!/usr/bin/env python3
"""taskflow‑cli – a tiny agent‑friendly todo manager.

Features:
- noun‑verb command hierarchy (`task add`, `task list`, …)
- long‑only flags (`--title`, `--dry-run`)
- JSON output by default when stdout is not a TTY
- `--dry‑run` preview for mutating commands (exit code 10)
- Structured errors (JSON on stderr) with `kind` and `retryable`
- `task schema` command for machine‑readable introspection

The data store is a simple JSON file stored at ``~/.taskflow/tasks.json``.
"""

import json
import os
import sys
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

APP_NAME = "taskflow-cli"
DATA_PATH = Path.home() / ".taskflow" / "tasks.json"

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _ensure_data_file() -> None:
    """Create the data directory/file if it does not exist."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text(json.dumps({"tasks": []}, indent=2))

def _load_tasks() -> List[Dict[str, Any]]:
    _ensure_data_file()
    try:
        content = json.loads(DATA_PATH.read_text())
        return content.get("tasks", [])
    except json.JSONDecodeError as exc:
        _structured_error(
            kind="corrupt_data",
            message=f"Unable to parse tasks file: {exc}",
            retryable=False,
        )
        sys.exit(2)

def _save_tasks(tasks: List[Dict[str, Any]]) -> None:
    DATA_PATH.write_text(json.dumps({"tasks": tasks}, indent=2))

def _next_id(tasks: List[Dict[str, Any]]) -> int:
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1

def _json_output(data: Any, *, output: str) -> None:
    if output == "json" or not sys.stdout.isatty():
        click.echo(json.dumps(data, ensure_ascii=False))
    else:
        # human‑friendly table
        if isinstance(data, list) and data:
            headers = data[0].keys()
            rows = [list(item.values()) for item in data]
            click.echo(tabulate(rows, headers=headers, tablefmt="github"))
        else:
            click.echo(str(data))

def _structured_error(*, kind: str, message: str, retryable: bool) -> None:
    err = {"kind": kind, "message": message, "retryable": retryable}
    click.echo(json.dumps(err), err=True)

# ---------------------------------------------------------------------------
# CLI definition (noun‑verb hierarchy)
# ---------------------------------------------------------------------------

@click.group(name="task", help="Manage your personal todo list.")
def task_group():
    pass

# ---------- add -----------------------------------------------------------
@task_group.command(name="add", help="Create a new task.")
@click.option("--title", required=True, help="Title of the task")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be done without persisting")
def add_cmd(title: str, dry_run: bool) -> None:
    tasks = _load_tasks()
    new_task = {"id": _next_id(tasks), "title": title, "done": False}
    if dry_run:
        _json_output({"preview": new_task}, output="json")
        sys.exit(10)  # dry‑run success code per spec
    tasks.append(new_task)
    _save_tasks(tasks)
    _json_output({"created": new_task}, output="json")

# ---------- list ----------------------------------------------------------
@task_group.command(name="list", help="List existing tasks.")
@click.option("--output", type=click.Choice(["json", "table"], case_sensitive=False), default="json", help="Output format")
def list_cmd(output: str) -> None:
    tasks = _load_tasks()
    _json_output(tasks, output=output)

# ---------- done ----------------------------------------------------------
@task_group.command(name="done", help="Mark a task as completed.")
@click.option("--id", required=True, type=int, help="ID of the task to mark done")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without persisting")
def done_cmd(id: int, dry_run: bool) -> None:
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == id:
            if t["done"]:
                _structured_error(kind="conflict", message="Task already completed", retryable=False)
                sys.exit(5)
            preview = {"id": id, "old": t["done"], "new": True}
            if dry_run:
                _json_output({"preview": preview}, output="json")
                sys.exit(10)
            t["done"] = True
            _save_tasks(tasks)
            _json_output({"updated": preview}, output="json")
            return
    _structured_error(kind="not_found", message=f"Task {id} does not exist", retryable=False)
    sys.exit(6)

# ---------- delete --------------------------------------------------------
@task_group.command(name="delete", help="Delete a task permanently.")
@click.option("--id", required=True, type=int, help="ID of the task to delete")
@click.option("--yes", is_flag=True, default=False, help="Skip interactive confirmation")
@click.option("--dry-run", is_flag=True, default=False, help="Show what would be deleted")
def delete_cmd(id: int, yes: bool, dry_run: bool) -> None:
    tasks = _load_tasks()
    for i, t in enumerate(tasks):
        if t["id"] == id:
            preview = {"id": id, "title": t["title"]}
            if dry_run:
                _json_output({"preview": preview}, output="json")
                sys.exit(10)
            if not yes:
                if not sys.stdin.isatty():
                    _structured_error(kind="interactive_required", message="Confirmation needed", retryable=False)
                    sys.exit(2)
                click.confirm(f"Delete task #{id} – '{t['title']}'?", abort=True)
            del tasks[i]
            _save_tasks(tasks)
            _json_output({"deleted": preview}, output="json")
            return
    _structured_error(kind="not_found", message=f"Task {id} does not exist", retryable=False)
    sys.exit(6)

# ---------- schema --------------------------------------------------------
@task_group.command(name="schema", help="Print machine‑readable command schema (JSON).")
def schema_cmd() -> None:
    # A very small static schema – real tools would generate this dynamically.
    schema = {
        "name": "taskflow-cli",
        "version": "0.1.0",
        "commands": [
            {
                "noun": "task",
                "verb": "add",
                "description": "Create a new task",
                "flags": [
                    {"name": "--title", "type": "string", "required": True},
                    {"name": "--dry-run", "type": "boolean", "required": False},
                ],
            },
            {
                "noun": "task",
                "verb": "list",
                "description": "List existing tasks",
                "flags": [
                    {"name": "--output", "type": "enum", "enum": ["json", "table"], "default": "json"},
                ],
            },
            {
                "noun": "task",
                "verb": "done",
                "description": "Mark a task as completed",
                "flags": [
                    {"name": "--id", "type": "integer", "required": True},
                    {"name": "--dry-run", "type": "boolean", "required": False},
                ],
            },
            {
                "noun": "task",
                "verb": "delete",
                "description": "Delete a task permanently",
                "flags": [
                    {"name": "--id", "type": "integer", "required": True},
                    {"name": "--yes", "type": "boolean", "required": False},
                    {"name": "--dry-run", "type": "boolean", "required": False},
                ],
            },
        ],
        "exit_codes": {
            "0": "Success",
            "2": "Usage error",
            "5": "Conflict (idempotent conflict)",
            "6": "Not found",
            "10": "Dry‑run success",
        },
    }
    click.echo(json.dumps(schema, indent=2))

# ---------------------------------------------------------------------------
# Root entry point
# ---------------------------------------------------------------------------
@click.group()
def cli() -> None:
    "Top‑level entry point – registers sub‑groups."

cli.add_command(task_group)

if __name__ == "__main__":
    cli()

# ---------------------------------------------------------------------------
# Optional: tiny helper for pretty tables without adding a heavy dependency.
# Install with: pip install tabulate
# ---------------------------------------------------------------------------
try:
    from tabulate import tabulate  # type: ignore
except ImportError:  # pragma: no cover
    def tabulate(rows, headers, tablefmt="github"):
        # Very naive fallback – just join with tabs.
        header_line = "\t".join(headers)
        data_lines = ["\t".join(str(v) for v in row) for row in rows]
        return "\n".join([header_line] + data_lines)
