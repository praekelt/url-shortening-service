import random
import string

DEFAULT_ALPHABET = string.digits + string.ascii_letters
SHORT_URL_OFFSET = 4000
SHUFFLE_SEED = 1234


def shuffle(items):
    """
    Reorder a sequence deterministically.

    A pseudo-random number generator is initialised with a constant seed value
    and used to sample all elements in the sequence.

    :class:`random.Random` is a deterministic Mersenne Twister implementation
    and will always return the same sequence of values when initialised with
    the same seed across all Python versions (CPython and the equivalent pypy
    implementations) from 2.3 to at least 3.3. Python 3 documentations asserts
    that if the pseudo-random number generator changes in a future release, a
    backward-compatible implementation will be made available.
    """
    return random.Random(SHUFFLE_SEED).sample(items, len(items))


def generate_token(counter, alphabet=DEFAULT_ALPHABET):
    """
    Generates a short url token using the given counter from the alphabet
    min_length: 3 (using SHORT_URL_OFFSET)
    """
    if not isinstance(counter, int):
        raise TypeError('an integer is required')

    alphabet = shuffle(alphabet)
    base = len(alphabet)
    counter += SHORT_URL_OFFSET

    digits = []
    while counter > 0:
        digits.append(alphabet[counter % base])
        counter = counter // base

    return ''.join(shuffle(digits))
