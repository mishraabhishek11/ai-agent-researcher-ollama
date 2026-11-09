# AI Agent Researcher (Ollama)

A Python research agent that runs entirely on a **local LLM through Ollama**. Given a research question, it plans the investigation, searches the web, reads sources, records findings, **verifies each finding against its evidence**, and only then writes a structured report built from verified findings.

---

## Features

### Research Planning
Before any tool is called, the model turns the request into a short, numbered research plan (`create_research_plan`). The plan is printed and passed to the agent as guidance.

### Autonomous Tool-Calling Agent
`research_agent` runs a tool-calling loop (up to `max_steps`, default 100). On each step the model chooses which tool to call next, and the result is fed back into the conversation.

### Web Search
`search_web` queries DuckDuckGo's HTML endpoint and returns titles, URLs and snippets. No API key is required.

### Webpage Reading
`read_webpage` resolves DuckDuckGo redirect links to the real URL, downloads the page, strips `script`/`style`/`noscript` tags and returns up to 12,000 characters of text.

### Research Notes
`add_research_note` stores each finding as `{source, finding, evidence, verified}`. `get_research_notes` returns copies, so callers cannot change the stored notes.

### Evidence Verification
`verify_finding` asks the LLM, in JSON mode, whether the evidence actually supports the finding. Supported findings are marked `verified`.

### Completion Guard
The agent **cannot finish with zero verified findings**. If the model tries to stop early, it is told to take another research action (search, read, add a note or verify).

### Grounded Report Generation
`generate_report` writes the final report **using only verified findings**. The prompt forbids invented facts or URLs. The report has these sections:

1. Executive Summary
2. Introduction
3. Key Findings
4. Analysis
5. Limitations
6. Conclusion
7. Sources

---

## Tech Stack

**Core**
- Python 3
- [Ollama](https://ollama.com/) running locally
- Model: `qwen3:4b` (default)

**Libraries**
- `ollama`: Python client for chat and tool calling
- `requests`: HTTP for search and page downloads
- `beautifulsoup4`: HTML parsing and text extraction

---

## Project Structure

```
ai-agent-researcher-ollama/
├── agent.py      # Research planner, tool-calling agent loop, report generator
├── tools.py      # search_web, read_webpage, research notes, verify_finding
├── main.py       # Entry point: runs the agent and prints the final report
├── requirements.txt  # Python dependencies
└── README.md
```

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/mishraabhishek11/ai-agent-researcher-ollama.git
cd ai-agent-researcher-ollama
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama and pull the model

Download Ollama from [ollama.com](https://ollama.com/download), then run:

```bash
ollama pull qwen3:4b
```

Make sure the Ollama server is running (`ollama serve`, or the desktop app).

### 5. Run the agent

```bash
python main.py
```

---

## Usage

The research question is set in `main.py`:

```python
request = (
    "Research the role of AI agents "
    "in software development. "
    "Identify major use cases, benefits, "
    "and limitations."
)
```

Change `request` to research a different topic. A sample run looks like this:

```
============================================================
RESEARCH PLAN
============================================================
1. Identify major use cases of AI agents in software development
2. ...

--- Agent Step 1 ---
Calling tool: search_web
Arguments: {'query': 'AI agents in software development use cases'}

--- Agent Step 2 ---
Calling tool: read_webpage
...

Research complete.
Verified findings collected: 6

============================================================
FINAL RESEARCH REPORT
============================================================
...
```

1. The agent prints its research plan.
2. Each step shows the tool called and its arguments.
3. When verified findings exist and the model stops calling tools, research ends.
4. The final report is printed to the console.

---

## How It Works

1. **Plan:** the LLM breaks the request into numbered research steps.
2. **Search:** the agent calls `search_web` to find candidate sources.
3. **Read:** `read_webpage` pulls the text of promising sources.
4. **Record:** findings are saved with their source and supporting evidence through `add_research_note`.
5. **Verify:** `verify_finding` checks each finding against its evidence and marks supported findings as verified.
6. **Guard:** if the model tries to finish with no verified findings, it is told to keep researching.
7. **Report:** `generate_report` writes the final report from verified findings only.

```
plan ──► search ──► read ──► add note ──► verify
            ▲                               │
            └──── not enough verified ◄─────┘
                                            │
                              verified ──► report
```

---

## Configuration

| Setting | Location | Default | Description |
|---|---|---|---|
| `MODEL` | `agent.py`, `tools.py` | `qwen3:4b` | Ollama model used for planning, agent steps, verification and the report |
| `max_steps` | `main.py` | `100` | Maximum number of agent loop iterations |
| `max_results` | `search_web` | `5` | Search results returned per query |
| Page text limit | `read_webpage` | `12000` chars | Text kept per page |
| HTTP timeout | `tools.py` | `20` s | Timeout for search and page requests |

> **Note:** `MODEL` is defined in both `agent.py` and `tools.py`. If you switch models, change both.

---

## Adding Your Own Tool

1. Write a function in `tools.py` with a clear docstring. Ollama uses the signature and docstring to build the tool schema.
2. Import it in `agent.py`.
3. Add it to both `AVAILABLE_TOOLS` (name → function) and `TOOLS` (the list passed to the model).
4. Optionally, mention the tool in the agent's system prompt so the model knows when to use it.

---

## Troubleshooting

| Error / Symptom | Cause | Fix |
|---|---|---|
| `ConnectionError` / connection refused from Ollama | Ollama server isn't running | Start Ollama (`ollama serve` or the desktop app) |
| `model "qwen3:4b" not found` | Model not pulled | Run `ollama pull qwen3:4b` |
| `json.JSONDecodeError` or `KeyError: 'supported'` in a tool error | The model returned malformed verification JSON | The agent reports the error back to the model and continues. A larger model reduces how often this happens |
| `search_web` returns no results or HTTP 4xx/5xx | DuckDuckGo rate limiting or blocking | Wait and retry, or lower the request rate |
| "No verified research findings were collected." | Agent hit `max_steps` without verifying anything | Increase `max_steps`, refine the request, or use a stronger model |

---

## Known Limitations

- Research notes are kept **in memory** for a single run. Nothing is saved to disk.
- Verification checks whether the stored evidence supports the finding. It does **not** check that the evidence really appears on the source page.
- Web scraping can be fragile, and some sites block automated requests.
- Small local models may make poor tool-call choices or return malformed JSON.

---

## Learning Objectives

- Building a tool-calling agent loop with Ollama
- Grounding LLM output in retrieved, verified evidence
- Guarding against agents finishing too early
- Using JSON-mode LLM calls as a verification step
- Running a full research pipeline locally, with no cloud API keys

---

## Future Enhancements

- Centralise configuration (model, limits) in one place or in `.env`
- Accept the research question from CLI arguments
- Save notes and reports to disk (Markdown or JSON)
- Check that evidence actually appears in the fetched source text
- Retry on malformed verification JSON
- Add unit tests for the tools and the agent loop
- Add a web or chat UI

---

## Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feat/your-feature`
3. Commit with Conventional Commits: `git commit -m "feat(tools): add arxiv search"`
4. Push the branch: `git push origin feat/your-feature`
5. Open a Pull Request

---

## Author

**Abhishek Mishra**
GitHub: [@mishraabhishek11](https://github.com/mishraabhishek11)

---

## Support

If you find this project useful, please give it a ⭐ on GitHub!
