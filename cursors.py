# -*- coding: utf-8 -*-
#
#    Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#    This file is part of Pylitaire game
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>
#
# Mouse cursor utility functions

import sys
import math
import json

import pygame


def invert_cursor(cursor):
    ''' Invert the colors of a cursor, ie, swap black and white bits
    '''
    size, hot, data, mask = cursor
    inv = []
    for i, byte in enumerate(data):
        inv.append((256 + ~byte) & mask[i])
    return size, hot, tuple(inv), mask


def compile(strings, black="X", white=".", xor="o"):
    ''' Convenience wrapper to pygame.cursors.compile() with swapped black and
        white arguments, to workaround its arguments swap.
    '''
    return pygame.cursors.compile(strings, black=white, white=black, xor=xor)


def layerlines(bytelist, width=0, char0=".", char1="X"):
    ''' Read the byte list of an icon "layer" (the data or its mask, icon
        index 2 or 3) and return a sequence of strings, one for each layer
        line, where each char represents a layer bit.
        Example:
        >>> layerlines(pygame.cursors.arrow[3])  # the arrow mask
        >>> ['.X..............', 'XXX.............', 'XXXX............', ...]
    '''
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


def cursorstrings(cursor,
                     black="X",    white=".",    transparent=" ",
                  hotblack="X", hotwhite=".", hottransparent=" "):
    ''' Return a list of strings, each string representing a cursor line,
        and char a cursor pixel. Each pixel can have one of 3 possible values,
        interpreted as "black", "white" and "transparent". One of the pixels
        is also marked as the "hotspot" of the cursor.

        Can also be used to view the icon as "ASCII art", dump its data and
        easily manipulate its image

        Default output format is compatible as input to pygame.cursors.compile(),
        to be used as its <string> argument.

        IMPORTANT NOTE!!! pygame.cursors.compile() has a bug that with default
        options it swaps black and white. You may use compile() wrapper as a
        workaround
    '''
    size, hot, data, mask = cursor
    width, height = size
    chars = black + white + transparent + hotblack + hotwhite + hottransparent
    datalines = layerlines(data, width=width, char0="0", char1="1")
    masklines = layerlines(mask, width=width, char0="0", char1="1")
    buffer = ""
    strings = []
    for i in xrange(height):
        for j in xrange(width):
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
    ''' Return a string that is a textual representation of all information in
        a cursor: a 3-tuple (or list) with size, hotspot and image strings.

        Output can be directly pasted in code for manual editing of image data,
        or dumped to a json file. The image strings is compatible as input to
        pygame.cursors.compile(), so the cursor can be easily re-created.

        By default output delimiters are single quotes `'` and parenthesis `()`,
        as would the repr() of a tuple of strings be. Delimiter format is set
        by <tuples> and <singlequotes>.

        If <json> is True, delimiters are forced to double quotes `"` and
        brackets `[]` (ie, values as lists instead of tuples), so the output
        is valid JSON data.

        Example:
        >>> print cursorcode(pygame.mouse.get_cursor())
        ...
        >>> code = cursorcode(pygame.cursors.arrow, json=True)
        >>> size, hot, strings = json.loads(code)
        >>> data, mask = pygame.cursors.compile(strings, black=".", white="X")
        >>> pygame.mouse.set_cursor(size, hot, data, mask)

        Note that (black=".", white="X") arguments are swapped as a workaround
        to the bug in pygame.cursors.compile()
    '''
    if json:
        tuples = False
        singlequotes=False

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
    ''' A convenience wrapper to cursorcode() to generate code
        from a xmb cursor file and its mask file.
    '''
    try:
        cursor = pygame.cursors.load_xbm(xmbfile, maskfile)
    except Exception as e:
        # A cheap way to unobtrusively "flag" this exception
        e.xbmfailed = True
        raise e

    return cursorcode(cursor, *args, **kwargs)


def load_cursor(triplet):
    ''' Return a cursor from a 3-tuple (size, hotspot, cursor strings)

        Output is compatible as input to pygame.mouse.set_cursor(*cursor)

        Input triplet is compatible with cursorcode() output when it is
        parsed by eval() or json.loads()

        Note: as a triplet is NOT a cursor, this function name is a bit of a
        misnomer, but a convenient one to use in code.

        Example:
        triplet = json.loads(cursorcode(pygame.cursors.arrow))
        pygame.mouse.set_cursor(*load_cursor(triplet))
    '''
    size, hot, strings = triplet
    data, mask = compile(strings)
    return size, hot, data, mask




if __name__ == "__main__":
    if sys.argv[1:]:
        if len(sys.argv) < 3:
            print "Converts a xmb cursor file and its mask to JSON"
            print "Usage: python cursors.py <CURSOR_FILE> <MASK_FILE>"
            print "Or run without arguments for a demonstration"
            sys.exit()
        try:
            print xmbcode(*sys.argv[1:3], json=True)
        except IOError as e:
            print e
        except Exception as e:
            if hasattr(e, 'xbmfailed'):
                print "Error loading cursor: are those valid XMB files?"
            else:
                raise e
        sys.exit()

    # Functions demo
    pygame.init()

    cursor = pygame.cursors.arrow

    size, hot, data, mask = cursor

    print "Using pygame.cursors.arrow"
    print "\nSize, hotspot, data and mask"
    print size, hot

    for layer in [data, mask]:
        for line in layerlines(layer):
            print line

    print "\nImage (with hotspot)"
    for stringline in cursorstrings(cursor, black="x", hottransparent="O"):
        print stringline

    print "\nImage (as JSON)"
    # The is actualy the REAL test for this module:
    jsoncode = cursorcode(cursor, json=True)
    triplet = json.loads(jsoncode)  # No exceptions raised, so we have valid JSON :)
    pygame.mouse.set_cursor(*load_cursor(triplet))  # No exceptions either, hooray! :D
    print jsoncode

    print "\nImage (as tuples)"
    print cursorcode(cursor)

    print "\nDefault pygame cursor. It is NOT pygame.cursors.arrow !!!!!!!"
    print cursorcode(pygame.mouse.get_cursor())

    print "\nRoundtrip: get_cursor(set_cursor(get_cursor())) works fine, as expected"
    print cursorcode(pygame.mouse.get_cursor(pygame.mouse.set_cursor(*pygame.mouse.get_cursor())))

    print "\npygame.cursors.compile() IS BUGGY: BY DEFAULT IT SWAPS BLACK AND WHITE!!!!"
    data, mask = pygame.cursors.compile(cursorstrings(cursor))
    print cursorcode((size, hot, data, mask))

    print "\ninvert_cursor() comes in to save the day. (so would compile() wrapper)"
    data, mask = pygame.cursors.compile(cursorstrings(invert_cursor(cursor)))
    print cursorcode((size, hot, data, mask))
