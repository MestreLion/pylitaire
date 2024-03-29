# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""Mouse cursor utility functions."""

import sys
import math
import json
import typing as t

import pygame

Cursor: 't.TypeAlias' = t.Union[
    pygame.cursors.Cursor,
    t.Tuple[t.Sequence[int],
            t.Sequence[int],
            t.Sequence[int],
            t.Sequence[int]]
]


def invert_cursor(cursor: Cursor) -> Cursor:
    """Invert the colors of a cursor, ie, swap black and white bits."""
    size, hot, data, mask = cursor
    inv = []
    for i, byte in enumerate(data):
        inv.append((256 + ~byte) & mask[i])
    return size, hot, tuple(inv), mask


def compile(strings, black="X", white=".", xor="o"):  # @ReservedAssignment
    """Convenience wrapper to pygame.cursors.compile().

    Fix the bug prior to pygame 1.92 / python 2 that swaps black and white.
    """
    if pygame.version.vernum < (1, 9, 2):
        black, white = white, black
    return pygame.cursors.compile(strings, black=black, white=white, xor=xor)


def layerlines(bytelist, width=0, char0=".", char1="X"):
    # noinspection PyUnresolvedReferences
    """Read the byte list of an icon "layer" and return a sequence of strings.

    An icon layer is the data or its mask, icon index 2 or 3. Return one for
    each layer line, where each char represents a layer bit.

    Example:
    >>> layerlines(pygame.cursors.arrow[3])  # the arrow mask
    >>> ['.X..............', 'XXX.............', 'XXXX............', ...]
    """
    if not width:
        # Assume square icon
        width = math.sqrt(8 * len(bytelist))
    # A single test to check both the square assumption
    # and the requirement that width must be multiple of 8
    if not width % 8 == 0:
        raise ValueError("Width must be a multiple of 8")
    bytesperline = width / 8
    buffer = ""
    lines = []
    for i, byte in enumerate(bytelist):
        buffer += "{:08b}".format(byte).replace("0", char0).replace("1", char1)
        if (i+1) % bytesperline == 0:
            lines.append(buffer)
            buffer = ""
    return lines


def cursorstrings(
    cursor,
       black="X",    white=".",    transparent=" ",
    hotblack="X", hotwhite=".", hottransparent=" "
):
    """Return a list of strings, each string representing a cursor image line.

    Each char represent a cursor pixel. A pixel can have one of 3 possible values,
    interpreted as "black", "white" and "transparent". One of the pixels is also marked
    as the "hotspot" of the cursor.

    Can be used to view the icon as "ASCII art", dump its data and easily manipulate
    its image, or as input to pygame.cursors.compile().

    Default output format is compatible with its <string> argument.

    NOTE: On Python 2 / Pygame 1.91, pygame.cursors.compile() has a bug that swaps
    black and white. Use compile() wrapper or invert_cursor().
    """
    size, hot, data, mask = cursor
    width, height = size
    chars = black + white + transparent + hotblack + hotwhite + hottransparent
    datalines = layerlines(data, width=width, char0="0", char1="1")
    masklines = layerlines(mask, width=width, char0="0", char1="1")
    buffer = ""
    strings = []
    for i in range(height):
        for j in range(width):
            databit = int(datalines[i][j])
            maskbit = int(masklines[i][j])
            ishot = 3 if (hot == (j, i)) else 0
            if maskbit == 0:
                buffer += chars[2 + ishot]      # transparent
            else:
                if databit == 0:
                    buffer += chars[1 + ishot]  # white
                else:
                    buffer += chars[0 + ishot]  # black
        strings.append(buffer)
        buffer = ""
    return strings


def cursorcode(cursor, indent=4, tuples=True, singlequotes=True, json=False):
    # noinspection PyUnresolvedReferences,PyShadowingNames,PyTypeChecker,PyRedeclaration,GrazieInspection
    """Return a textual representation of all information in a cursor as 3-tuple.

    Items are size, hotspot and image strings. If <tuples> is falsy, return a list instead.

    Output can be directly pasted in code for manual editing of image data, or dumped to
    a json file. The image strings tuple is compatible with pygame.cursors.compile(),
    so the cursor can be easily re-created.

    By default, output delimiters are single quotes `'` and parenthesis `()`, as would the
    repr() of a tuple of strings be. Delimiter format is set by <tuples> and <singlequotes>.

    If <json> is True, delimiters are forced to double quotes `"` and brackets `[]`
    (ie, values as lists instead of tuples), so the output is valid JSON data.

    Example:
    >>> print(cursorcode(pygame.mouse.get_cursor()))
    ...
    >>> code = cursorcode(pygame.cursors.arrow, json=True)
    >>> size, hot, strings = json.loads(code)
    >>> data, mask = pygame.cursors.compile(strings, black="X", white=".")
    >>> pygame.mouse.set_cursor(size, hot, data, mask)

    Note: On Python 2 / Pygame 1.91, swap black and white values to work around
    a bug in pygame.cursors.compile(), or use compile() wrapper:
    >>> data, mask = pygame.cursors.compile(strings, black=".", white="X")
    >>> data, mask =                compile(strings, black="X", white=".")
    Or use invert_cursor() on strings:
    >>> data, mask = pygame.cursors.compile(invert_cursor(strings),
                                                     black="X", white=".")
    """
    if json:
        tuples = False
        singlequotes = False

    size, hot, _, _ = cursor

    template = "\n%s'%%s'" % (indent * " ")
    code = '(%r, %r, (%s\n))' % (
        size, hot, ",".join(template % line for line in cursorstrings(cursor)))

    if not tuples:
        code = code.replace("(", "[").replace(")", "]")

    if not singlequotes:
        code = code.replace("'", '"')

    return code


def xmbcode(xmbfile, maskfile, *args, **kwargs):
    """Convenience wrapper to cursorcode().

    Generate code from a xmb cursor file and its mask file.
    """
    try:
        cursor = pygame.cursors.load_xbm(xmbfile, maskfile)
    except Exception as e:
        # A cheap way to unobtrusively "flag" this exception
        e.xbmfailed = True
        raise e

    return cursorcode(cursor, *args, **kwargs)


def load_cursor(triplet):
    """Return a cursor from a 3-tuple (size, hotspot, cursor strings).

    Output is compatible as input to pygame.mouse.set_cursor(*cursor).

    Input triplet is compatible with cursorcode() output when it is parsed by
    eval() or json.loads()

    Note: as a triplet is NOT a cursor, this function's name is a bit of a misnomer, but
    a convenient one to use in code.

    Example:
    >>> triplet = json.loads(cursorcode(pygame.cursors.arrow))
    >>> pygame.mouse.set_cursor(*load_cursor(triplet))
    """
    size, hot, strings = triplet
    data, mask = compile(strings)
    return size, hot, data, mask


def load_json(path):
    """Convenience wrapper for load_cursor().

    Read a triplet from a JSON-formatted file and return a cursor compatible for use as
    input to pygame.mouse.set_cursor(*cursor).
    """
    with open(path) as fp:
        return load_cursor(json.load(fp))


if __name__ == "__main__":
    if sys.argv[1:]:
        if len(sys.argv) < 3:
            print("Converts a xmb cursor file and its mask to JSON")
            print("Usage: python cursors.py <CURSOR_FILE> <MASK_FILE>")
            print("Or run without arguments for a demonstration")
            sys.exit()
        try:
            print(xmbcode(*sys.argv[1:3], json=True))
        except IOError as e:
            print(e)
        except Exception as e:
            if hasattr(e, 'xbmfailed'):
                print("Error loading cursor: are those valid XMB files?")
            else:
                raise e
        sys.exit()

    # Functions demo
    pygame.init()

    cursor = pygame.cursors.arrow

    size, hot, data, mask = cursor

    print("Using pygame.cursors.arrow")
    print("\nSize, hotspot, data and mask")
    print(size, hot)

    for layer in [data, mask]:
        for line in layerlines(layer):
            print(line)

    print("\nImage (with hotspot)")
    for stringline in cursorstrings(cursor, black="x", hottransparent="O"):
        print(stringline)

    print("\nImage (as JSON)")
    # The is actually the REAL test for this module:
    jsoncode = cursorcode(cursor, json=True)
    triplet = json.loads(jsoncode)  # No exceptions raised, so we have valid JSON :)
    pygame.mouse.set_cursor(*load_cursor(triplet))  # No exceptions either, hooray! :D
    print(jsoncode)

    print("\nImage (as tuples)")
    print(cursorcode(cursor))

    print("\nDefault pygame cursor. It is NOT pygame.cursors.arrow !!!!!!!")
    print(cursorcode(pygame.mouse.get_cursor()))

    print("\nRoundtrip: get_cursor(set_cursor(get_cursor())) works fine, as expected")
    pygame.mouse.set_cursor(*pygame.mouse.get_cursor())
    print(cursorcode(pygame.mouse.get_cursor()))

    if pygame.version.vernum < (1, 9, 2):
        print("\npygame.cursors.compile() is buggy on 1.91 / Python 2, swapping black and white")
        data, mask = pygame.cursors.compile(cursorstrings(cursor))
        print(cursorcode((size, hot, data, mask)))

        print("\ninvert_cursor() can be used to save the day for Python 2 users!")
        data, mask = pygame.cursors.compile(cursorstrings(invert_cursor(cursor)))
        print(cursorcode((size, hot, data, mask)))

    print("\ncompile() works regardless of Pygame / Python version:")
    data, mask = compile(cursorstrings(cursor))
    print(cursorcode((size, hot, data, mask)))
