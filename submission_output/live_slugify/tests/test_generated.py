import pytest
from slugify_utility import slugify

def test_tp_1_type_error_on_non_str():
    """TP_1: slugify function accepts a single parameter 'text' of type str and raises TypeError otherwise"""
    with pytest.raises(TypeError):
        slugify(123)
    with pytest.raises(TypeError):
        slugify(None)
    with pytest.raises(TypeError):
        slugify(3.14)
    with pytest.raises(TypeError):
        slugify(['list'])

def test_tp_2_returns_str_for_valid_input():
    """TP_2: slugify function returns a string representing a lowercase URL-safe slug"""
    result = slugify("Valid Input")
    assert isinstance(result, str)

def test_tp_3_all_alpha_lowercase():
    """TP_3: All alphabetic characters in input text are converted to lowercase in output slug"""
    input_text = "AbC DeF"
    output = slugify(input_text)
    assert output == output.lower()
    assert all(c.islower() or not c.isalpha() for c in output)

def test_tp_4_strip_leading_trailing_whitespace():
    """TP_4: Leading and trailing whitespace in input text is ignored in output slug"""
    input_text = "   hello world   "
    output = slugify(input_text)
    assert not output.startswith('-')
    assert not output.endswith('-')
    assert output == "hello-world"

def test_tp_5_whitespace_replaced_by_single_hyphen():
    """TP_5: One or more whitespace characters in input text are replaced with a single hyphen in output slug"""
    input_text = "hello    world\tthis\nis  test"
    output = slugify(input_text)
    assert output == "hello-world-this-is-test"
    assert '--' not in output

def test_tp_6_punctuation_removed_except_hyphen():
    """TP_6: All punctuation characters are removed from input text in output slug except hyphens"""
    input_text = "hello, world! this.is;a:test? - check"
    output = slugify(input_text)
    # Only hyphens allowed punctuation
    for c in output:
        if not (c.isalnum() or c == '-'):
            pytest.fail(f"Unexpected character {c} in output")
    # No punctuation except hyphen
    assert ',' not in output
    assert '!' not in output
    assert '.' not in output
    assert ';' not in output
    assert ':' not in output
    assert '?' not in output

def test_tp_7_existing_hyphens_preserved():
    """TP_7: Existing hyphens in input text are preserved in output slug"""
    input_text = "hello-world-this-is-a-test"
    output = slugify(input_text)
    # Hyphens preserved at corresponding positions (no extra or missing hyphens)
    assert output == input_text.lower()

def test_tp_8_collapse_multiple_adjacent_hyphens():
    """TP_8: Multiple adjacent hyphens in output slug collapse to a single hyphen"""
    input_text = "hello--world---this--is--test"
    output = slugify(input_text)
    assert '--' not in output
    # Hyphens preserved but collapsed
    assert output == "hello-world-this-is-test"

def test_tp_9_empty_string_returns_empty():
    """TP_9: Empty string input returns empty string output"""
    assert slugify('') == ''

def test_tp_10_whitespace_only_returns_empty():
    """TP_10: Input string containing only whitespace returns empty string output"""
    assert slugify('   \t\n') == ''

def test_tp_11_punctuation_only_returns_empty():
    """TP_11: Input string containing only punctuation returns empty string output"""
    assert slugify('!@#$%^&*()') == ''

def test_tp_12_already_slugified_returns_same():
    """TP_12: Input string already slugified returns the same string"""
    input_text = "already-slugified-text"
    output = slugify(input_text)
    assert output == input_text

def test_tp_13_type_error_on_non_string_input():
    """TP_13: slugify raises TypeError if input parameter 'text' is not a string"""
    with pytest.raises(TypeError):
        slugify(123)

def test_tp_14_ascii_handling_assumption():
    """TP_14: slugify handles ASCII characters only; non-ASCII input behavior is undefined"""
    ascii_input = "Hello World 123"
    ascii_output = slugify(ascii_input)
    assert all(ord(c) < 128 for c in ascii_input)
    assert all(ord(c) < 128 for c in ascii_output)
    # Non-ASCII input behavior is undefined, so just call and check no error
    non_ascii_input = "héllö wörld"
    try:
        slugify(non_ascii_input)
    except Exception:
        pytest.skip("Non-ASCII input behavior is undefined and may raise")

def test_tp_15_no_side_effects(monkeypatch):
    """TP_15: slugify has no side effects such as reading/writing files, network requests, or executing external commands"""
    # Patch builtins that could cause side effects to raise if called
    monkeypatch.setattr("builtins.open", lambda *a, **k: pytest.fail("open called"))
    monkeypatch.setattr("os.system", lambda *a, **k: pytest.fail("os.system called"))
    monkeypatch.setattr("subprocess.Popen", lambda *a, **k: pytest.fail("subprocess.Popen called"))
    monkeypatch.setattr("socket.socket", lambda *a, **k: pytest.fail("socket.socket called"))
    # Call slugify with normal input
    slugify("test side effects")

def test_tp_16_performance_linear_scaling():
    """TP_16: slugify runs in O(N) time and uses O(N) space, where N is input string length"""
    import time
    base_input = "a " * 1000  # 2000 chars approx
    start = time.perf_counter()
    slugify(base_input)
    duration_1k = time.perf_counter() - start

    base_input = "a " * 2000  # 4000 chars approx
    start = time.perf_counter()
    slugify(base_input)
    duration_2k = time.perf_counter() - start

    # The time for double input length should not be more than ~3x (allowing some overhead)
    assert duration_2k <= 3 * duration_1k or duration_1k == 0