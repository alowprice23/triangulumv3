import re
from typing import List, Set

# A simple approximation
CHARS_PER_TOKEN = 4

IMPORTANT_KEYWORDS = {
    "error", "fail", "failed", "failure", "exception", "traceback",
    "warning", "warn", "critical", "fatal"
}

def count_tokens(text: str) -> int:
    """A simple proxy for token counting."""
    return len(text) // CHARS_PER_TOKEN

def compress_text(text: str, max_tokens: int) -> str:
    """
    Compresses a large text to fit within a token budget, preserving important lines.

    Args:
        text: The text to compress.
        max_tokens: The maximum number of tokens allowed.

    Returns:
        The compressed text.
    """
    if count_tokens(text) <= max_tokens:
        return text

    lines = text.splitlines()
    if not lines:
        return ""

    num_lines = len(lines)
    max_chars = max_tokens * CHARS_PER_TOKEN

    # Identify important lines
    important_indices = set()
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in IMPORTANT_KEYWORDS):
            important_indices.add(i)

    # Always include the first and last few lines (e.g., 10 each)
    head_size = min(15, num_lines // 3)
    tail_size = min(15, num_lines // 3)

    selected_indices = set(range(head_size)) | set(range(num_lines - tail_size, num_lines))
    selected_indices.update(important_indices)

    # Build the compressed text
    compressed_lines = []
    current_chars = 0
    last_index_added = -1

    sorted_indices = sorted(list(selected_indices))

    for i in sorted_indices:
        line_to_add = lines[i]

        if current_chars + len(line_to_add) > max_chars:
            # Stop if we are about to exceed the budget
            break

        # Add a marker for skipped lines
        if last_index_added != -1 and i > last_index_added + 1:
            skip_marker = f"\n... ({i - last_index_added - 1} lines skipped) ...\n"
            if current_chars + len(line_to_add) + len(skip_marker) <= max_chars:
                compressed_lines.append(skip_marker)
                current_chars += len(skip_marker)

        compressed_lines.append(line_to_add)
        current_chars += len(line_to_add) + 1 # +1 for newline
        last_index_added = i

    # Final check if we still have space, add a final ellipsis if needed
    result = "\n".join(compressed_lines)
    if len(lines) > len(selected_indices) and last_index_added < len(lines) -1:
        result += f"\n... ({len(lines) - last_index_added -1} more lines truncated) ..."

    # If the result is still too large (due to a few very long lines), truncate it
    if count_tokens(result) > max_tokens:
        return result[:max_chars] + "\n... (truncated)"

    return result
