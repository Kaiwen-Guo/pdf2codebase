import string
import re

def slugify(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # Strip leading/trailing whitespace
    stripped = text.strip()
    if not stripped:
        return ""

    # Allowed characters: lowercase letters, digits, hyphen
    # Remove punctuation except hyphen
    # Preserve existing hyphens

    # Convert to lowercase
    lowered = stripped.lower()

    # Remove punctuation except hyphen
    # string.punctuation includes hyphen, so remove hyphen from punctuation set
    punctuation = string.punctuation.replace('-', '')
    # Remove all punctuation except hyphen
    no_punct = ''.join(ch for ch in lowered if ch not in punctuation)

    # Replace one or more whitespace characters with single hyphen
    # Whitespace includes space, tab, newline, etc.
    replaced_ws = re.sub(r'\s+', '-', no_punct)

    # Collapse multiple adjacent hyphens to single hyphen
    collapsed_hyphens = re.sub(r'-{2,}', '-', replaced_ws)

    # Strip leading/trailing hyphens that may have resulted from whitespace or punctuation removal
    slug = collapsed_hyphens.strip('-')

    return slug
