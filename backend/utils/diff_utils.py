import difflib

def compute_diff(old_text: str, new_text: str) -> str:
    """
    Compute text differences:
    + indicates additions
    - indicates deletions
    """
    differ = difflib.Differ()
    diff = list(differ.compare(old_text.splitlines(), new_text.splitlines()))

    formatted_diff = []
    for line in diff:
        if line.startswith("+ "):  # Added content
            formatted_diff.append(f"+ {line[2:]}")
        elif line.startswith("- "):  # Deleted content
            formatted_diff.append(f"- {line[2:]}")
        else:  # Unchanged content
            formatted_diff.append(line[2:])

    return "\n".join(formatted_diff)
