# taskflow‑cli

**A minimal yet robust CLI for a local todo list**

- ✅ Noun‑Verb command hierarchy (`task add`, `task list`, `task done`, `task delete`)
- ✅ All flags are long‑form (`--title`, `--dry‑run`)
- ✅ JSON is the default output when not attached to a TTY; human‑friendly tables when piped to a terminal
- ✅ `--dry‑run` provides a preview of destructive actions and exits with code 10
- ✅ `task schema` prints a machine‑readable description of the command tree (great for AI agents)
- ✅ Structured error objects with `kind`, `message`, `retryable`

## Installation
```bash
# Using pip (Python 3.10+ required)
python -m pip install --user taskflow-cli
```
Or run the single‑file version directly:
```bash
curl -sSL https://raw.githubusercontent.com/topherbot/taskflow-cli/main/taskflow_cli.py -o taskflow_cli.py
chmod +x taskflow_cli.py
./taskflow_cli.py --help
```

## Quick start
```bash
# Add a task (dry‑run preview first)
taskflow-cli task add --title "Write blog post" --dry-run

# Actually add it
taskflow-cli task add --title "Write blog post"

# List tasks (human table)
taskflow-cli task list

# List tasks as JSON (useful for pipelines)
taskflow-cli task list --output json

# Mark a task as done (idempotent)
taskflow-cli task done --id 1

# Delete a task (requires confirmation unless --yes is passed)
taskflow-cli task delete --id 1 --yes
```

## Schema introspection
```bash
# Print the whole command schema (machine‑readable JSON)
taskflow-cli task schema
```

## Development
```bash
# Clone the repo
git clone https://github.com/topherbot/taskflow-cli.git
cd taskflow-cli

# Install the development dependencies
python -m pip install -r requirements.txt

# Run the CLI from source
python -m taskflow_cli --help
```

---
*Built with ❤️ by TopherBot. Open‑source, MIT licensed.*

---
