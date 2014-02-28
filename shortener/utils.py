import random
import string

DEFAULT_ALPHABET = string.digits + string.ascii_letters
SHORT_URL_OFFSET = 4000
SHUFFLE_SEED = 1234


def shuffle(items):
    return random.Random(SHUFFLE_SEED).sample(items, len(items))


def generate_token(counter, alphabet=DEFAULT_ALPHABET):
    '''
    Generates a short url token using the given counter from the alphabet
    min_length: 3 (using SHORT_URL_OFFSET)
    '''
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
