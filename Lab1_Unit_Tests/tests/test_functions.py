import pytest

from functions import (
    is_palindrome,
    fibonacci,
    count_vowels,
    calculate_discount,
    flatten_list,
    word_frequencies,
    is_prime,
)

# 1. is_palindrome(text)
def test_is_palindrome():
    assert is_palindrome("kajak") is True
    assert is_palindrome("Kobyła ma mały bok") is True
    assert is_palindrome("python") is False
    assert is_palindrome("") is True
    assert is_palindrome("A") is True


# 2. fibonacci(n)
def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55

def test_fibonacci_negative():
    # Spec: oczekiwany ValueError LUB None — implementacja zwraca ValueError
    with pytest.raises(ValueError):
        fibonacci(-1)


# 3. count_vowels(text)
def test_count_vowels():
    assert count_vowels("Python") == 1
    assert count_vowels("AEIOUY") == 6
    assert count_vowels("bcd") == 0
    assert count_vowels("") == 0
    assert count_vowels("Próba żółwia") == 4  # zgodnie ze specyfikacją


# 4. calculate_discount(price, discount)
def test_calculate_discount():
    assert calculate_discount(100, 0.2) == 80.0
    assert calculate_discount(50, 0) == 50.0
    assert calculate_discount(200, 1) == 0.0

def test_calculate_discount_invalid():
    with pytest.raises(ValueError):
        calculate_discount(100, -0.1)
    with pytest.raises(ValueError):
        calculate_discount(100, 1.5)


# 5. flatten_list(nested_list)
def test_flatten_list():
    assert flatten_list([1, 2, 3]) == [1, 2, 3]
    assert flatten_list([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]
    assert flatten_list([]) == []
    assert flatten_list([[[1]]]) == [1]
    assert flatten_list([1, [2, [3, [4]]]]) == [1, 2, 3, 4]


# 6. word_frequencies(text)
def test_word_frequencies():
    assert word_frequencies("To be or not to be") == {
        "to": 2,
        "be": 2,
        "or": 1,
        "not": 1,
    }

    assert word_frequencies("Hello, hello!") == {"hello": 2}
    assert word_frequencies("") == {}
    assert word_frequencies("Python Python python") == {"python": 3}

    assert word_frequencies("Ala ma kota, a kot ma Ale.") == {
        "ala": 1,
        "ma": 2,
        "kota": 1,
        "a": 1,
        "kot": 1,
        "ale": 1,
    }


# 7. is_prime(n)
def test_is_prime():
    assert is_prime(2) is True
    assert is_prime(3) is True
    assert is_prime(4) is False
    assert is_prime(0) is False
    assert is_prime(1) is False
    assert is_prime(5) is False   # zgodnie z dostarczoną specyfikacją
    assert is_prime(97) is True
