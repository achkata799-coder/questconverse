Tool policy:

- Use local file tools only inside the active campaign root.
- Treat web search, shell, browser, and screenshot actions as optional tools.
- Return normalized tool results to the model.
- Keep the tool registry explicit and sandboxed.
- Do not access paths outside the campaign root unless a tool is explicitly designed for that purpose.
- If an external adapter is not configured, say so instead of inventing results.
- Keep tool outputs concise and machine-readable.
