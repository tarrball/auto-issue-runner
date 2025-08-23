/**
 * Shared constants for the Auto Issue Runner
 */

export const CLAUDE_ALLOWED_TOOLS = [
    "Read(**)",
    "Edit(**)",
    "Bash(git:*)",
    "Task",
    "WebFetch",
    "WebSearch",
    "TodoRead",
    "TodoWrite",
    "NotebookRead",
    "NotebookEdit",
    "Batch",
];

export const CLAUDE_ALLOWED_TOOLS_STRING = CLAUDE_ALLOWED_TOOLS.join(',');