import inspect
import random
import re


def camelcase_to_underscores(argument):
    ''' Converts a camelcase param like theNewAttribute to the equivalent
    python underscore variable like the_new_attribute'''
    result = ''
    prev_char_title = True
    for char in argument:
        if char.istitle() and not prev_char_title:
            # Only add underscore if char is capital, not first letter, and prev
            # char wasn't capital
            result += "_"
        prev_char_title = char.istitle()
        if not char.isspace():  # Only add non-whitespace
            result += char.lower()
    return result


def method_names_from_class(clazz):
    return [x[0] for x in inspect.getmembers(clazz, predicate=inspect.ismethod)]


def get_random_hex(length=8):
    chars = range(10) + ['a', 'b', 'c', 'd', 'e', 'f']
    return ''.join(unicode(random.choice(chars)) for x in range(length))


def get_random_message_id():
    sizes = 8, 4, 4, 4, 12
    return '{}-{}-{}-{}-{}'.format(*(get_random_hex(i) for i in sizes))


def iso_8601_datetime(datetime):
    return datetime.strftime("%Y-%m-%dT%H:%M:%SZ")


def rfc_1123_datetime(datetime):
    RFC1123 = '%a, %d %b %Y %H:%M:%S GMT'
    return datetime.strftime(RFC1123)
