import re

def is_palindrome(text: str) -> bool:
    """Sprawdza, czy tekst jest palindromem (ignoruje spacje i wielkość liter)."""
    cleaned = "".join(text.lower().split())
    return cleaned == cleaned[::-1]


def fibonacci(n: int) -> int:
    """Zwraca n-ty element ciągu Fibonacciego."""
    if n < 0:
        raise ValueError("Indeks nie może być ujemny.")
    if n in (0, 1):
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def count_vowels(text: str) -> int:
    """Zlicza liczbę samogłosek (z polskimi znakami)."""
    vowels = set("aeiouyąęó")
    return sum(1 for ch in text.lower() if ch in vowels)



def calculate_discount(price: float, discount: float) -> float:
    """Zwraca cenę po uwzględnieniu zniżki discount (0–1)."""
    if not 0 <= discount <= 1:
        raise ValueError("Discount musi być w zakresie 0–1.")
    return price * (1 - discount)


def flatten_list(nested_list: list) -> list:
    """Spłaszcza listę zagnieżdżoną."""
    result = []

    def flatten(item):
        if isinstance(item, list):
            for element in item:
                flatten(element)
        else:
            result.append(item)

    flatten(nested_list)
    return result


def word_frequencies(text: str) -> dict:
    """Zwraca słownik z częstościami słów, ignorując wielkość liter i interpunkcję."""
    # Usuwamy interpunkcję i dzielimy na słowa
    words = re.findall(r"\b\w+\b", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return freq


def is_prime(n: int) -> bool:
    """Sprawdza, czy liczba n jest pierwsza."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True
