# Slugify Utility

Generated Python project from an English software specification.

## Public API

- `slugify(text: str) -> str`: Converts human-readable text into a lowercase URL-safe slug string.

## Requirements

- `REQ_1` [api]: The slugify function must accept a single parameter 'text' of type str.
- `REQ_2` [api]: The slugify function must return a string representing a lowercase URL-safe slug.
- `REQ_3` [behavior]: All alphabetic characters in the input text must be converted to lowercase in the output slug.
- `REQ_4` [behavior]: Leading and trailing whitespace in the input text must be ignored in the output slug.
- `REQ_5` [behavior]: One or more whitespace characters in the input text must be replaced with a single hyphen in the output slug.
- `REQ_6` [behavior]: All punctuation characters must be removed from the input text in the output slug.
- `REQ_7` [behavior]: Existing hyphens in the input text must be preserved in the output slug.
- `REQ_8` [behavior]: Multiple adjacent hyphens in the output slug must collapse to a single hyphen.
- `REQ_9` [boundary]: If the input text is an empty string, the output slug must be an empty string.
- `REQ_10` [boundary]: If the input text contains only whitespace characters, the output slug must be an empty string.
- `REQ_11` [boundary]: If the input text contains only punctuation characters, the output slug must be an empty string.
- `REQ_12` [boundary]: If the input text is already a slugified string, the output must be the same string.
- `REQ_13` [error]: The slugify function must raise a TypeError if the input parameter 'text' is not a string.
- `REQ_14` [assumption]: The slugify function must handle ASCII characters only.
- `REQ_15` [side_effect]: The slugify function must have no side effects such as reading or writing files, making network requests, or executing external commands.
- `REQ_16` [performance]: The slugify function must run in O(N) time complexity and use O(N) space complexity, where N is the length of the input string.

## Test Plan Trace

- `TP_1` -> REQ_1: slugify function accepts a single parameter 'text' of type str
- `TP_2` -> REQ_2: slugify function returns a string representing a lowercase URL-safe slug
- `TP_3` -> REQ_3: All alphabetic characters in input text are converted to lowercase in output slug
- `TP_4` -> REQ_4: Leading and trailing whitespace in input text is ignored in output slug
- `TP_5` -> REQ_5: One or more whitespace characters in input text are replaced with a single hyphen in output slug
- `TP_6` -> REQ_6: All punctuation characters are removed from input text in output slug
- `TP_7` -> REQ_7: Existing hyphens in input text are preserved in output slug
- `TP_8` -> REQ_8: Multiple adjacent hyphens in output slug collapse to a single hyphen
- `TP_9` -> REQ_9: Empty string input returns empty string output
- `TP_10` -> REQ_10: Input string containing only whitespace returns empty string output
- `TP_11` -> REQ_11: Input string containing only punctuation returns empty string output
- `TP_12` -> REQ_12: Input string already slugified returns the same string
- `TP_13` -> REQ_13: slugify raises TypeError if input parameter 'text' is not a string
- `TP_14` -> REQ_14: slugify handles ASCII characters only
- `TP_15` -> REQ_15: slugify has no side effects such as reading/writing files, network requests, or executing external commands
- `TP_16` -> REQ_16: slugify runs in O(N) time and uses O(N) space, where N is input string length

## Run

```bash
PYTHONPATH=generated python main.py
PYTHONPATH=generated python -m pytest -q tests/test_generated.py
```

## Generated Layout

```text
generated/          # generated source modules
tests/              # generated pytest suite
project_spec.json   # normalized requirements and public APIs
test_plan.json      # executable test-plan items
codebase_manifest.json
```
