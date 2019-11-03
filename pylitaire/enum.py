# -*- coding: utf-8 -*-
#
#    Copyright (C) 2015 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
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

'''Basic implementation of enum module for Python 2 and 3'''

__all__ = ['Enum']  # not necessary as Enum is the only non-__*__ name

import sys

class _meta(type):
    @property
    def __members__(self):
        return {k: v for k, v in self.__dict__.items()
                if  not k.startswith("_")
                and not self._callable(getattr(self, k))}

    def __iter__(self):
        '''Yield members sorted by value, not declaration order'''
        return iter(sorted(self.__members__.values()))

    def __reversed__(self):
        '''Yield members sorted by descending value order'''
        return reversed(tuple(self))
        # tuple() is required to create a sequence out of the Enum

    def __getitem__(self, k):
        try:
            return self.__members__[k]
        except KeyError:
            # re-raise as AttributeError, for consistency with Enum.VALUE
            raise AttributeError("type object '{}' has no attribute '{}'".
                                 format(self.__name__, k))

    def __contains__(self, k):
        return k in self.__members__

    def __len__(self):
        return len(self.__members__)


class _base(object):
    @staticmethod
    def _callable(obj):
        '''Helper wrapper for callable() that works on Python 3.0 and 3.1'''
        try:
            return callable(obj)
        except NameError:
            # Python 3.0 and 3.1 has no callable()
            # which is a tiny safer than hasattr approach
            return hasattr(obj, "__call__")

    @classmethod
    def name(cls, value):
        '''
        Fallback for getting a friendly member name
        Return a titled string with underscores replaced by spaces
            AnEnum.name(AnEnum.AN_ORDINARY_MEMBER) => "An Ordinary Member"
        Enums can customize member names by overriding this method
        '''
        # value not handled in subclass name()
        for k, v in cls.__members__.items():
            if v == value:
                return k.replace('_', ' ').title()

        # Value not find. Try again using value as member name.
        # Allows usage as Enum.name("VALUE") besides Enum.name(Enum.VALUE)
        return cls.name(cls[value])

    @classmethod
    def members(cls):
        '''
        Return a list of member attribute names (strings),
        ordered by value to make it consistent with class iterator
        '''
        return sorted(cls.__members__, key=cls.__members__.get)


# Python 2
if sys.version_info[0] < 3:
    class Enum(_base):
        '''A basic implementation of Enums for Python 2'''
        __metaclass__ = _meta

# Python 3
else:
    # Python 2 see Python 3 metaclass declaration as SyntaxError, hence exec()
    exec("class Enum(_base, metaclass=_meta):"
         "'''A basic implementation of Enums for Python 3'''")

del sys, _base, _meta


if __name__ == '__main__':
    # Usage and Examples

    class Color(Enum):
        '''Enum class example'''

        # Declaration order is irrelevant, sorting will always be by value
        # Values can be any non-callable, and in Python 3 must be comparable
        # Bottom line: don't make an Enum of functions,
        # and don't mix numbers with strings
        BLACK    =  0
        WHITE    = 10  # This will sort last
        DEFAULT  = -1  # This will sort first
        RED      =  1
        GREEN    =  2
        BLUE     =  3
        NICE_ONE =  4

        # Methods are not considered members
        # That's why member values cannot be callables

        @classmethod
        def name(cls, v):
            '''Optional custom name function'''
            if v == cls.BLACK: return "is back!"
            if v == cls.WHITE: return "Delight"

            # Uses default name as fallback for members not listed above
            return super(Color, cls).name(v)

        @classmethod
        def counterpart(cls, v):
            '''Custom method example'''
            if v == cls.DEFAULT: return v
            if v == cls.BLACK:   return cls.WHITE
            if v == cls.WHITE:   return cls.BLACK

            return v + 1 if v + 1 in cls else cls.DEFAULT

    # Value and types
    print(Color.RED, Color["RED"], type(Color.RED))  # 1, 1, <type 'int'>

    # Testing values
    print("Red is the new Black?",
          Color.BLACK == 1,  # False
          Color.BLACK == 0)  # True

    # Names
    print(Color.name(1))               # "Red"
    print(Color.name("GREEN"))         # "Green"
    print(Color.name(Color.BLUE))      # "Blue"
    print(Color.name(Color.NICE_ONE))  # "Nice One"

    # Custom names
    print("Black", Color.name(Color.BLACK),  # "is back!"
          "White", Color.name("WHITE"))      # "Delight"

    # Membership
    print("is green a color?", Color.GREEN in Color)  # True

    # Iterating the class yields values,
    # iterating on members() yields member attribute names (as strings)
    # Both automatically sorted by value, for consistency with each other
    for color, member in zip(Color, Color.members()):
        print(color, member, Color.name(color))

    # Custom methods
    for color in Color:
        print(Color.name(color), "<=>", Color.name(Color.counterpart(color)))

    # Adding and removing members
    Color.YELLOW = 5
    del Color.NICE_ONE

    # Member count
    print("colors in a rainbow:", len(Color))  # 7

    # Using internal dict
    print("members dict:", Color.__members__)

    # Handling exceptions
    try:
        print(Color.BROWN)
    except Exception as e:
        print(repr(e))  # AttributeError
    try:
        print(Color['BROWN'])
    except Exception as e:
        print(repr(e))  # Also AttributeError, for consistency
    try:
        print(Color['name']) # Color.name exists but is not a member
    except Exception as e:
        print("Members only!", repr(e))  # AttributeError
    try:
        print(Color[2])  # Not allowed
    except Exception as e:
        print("I am NOT a sequence!", repr(e))

    # Reverse
    print("But I have built-in reversed:", tuple(reversed(Color)))

    # Class type, inheritance, structure
    print(type(Color), "is an Enum?", issubclass(Color, Enum))  # <class '__main__._meta'>, True
    print("MRO:", Color.mro())   # Color, Enum, _base, object
    print("class:", dir(Color))

    # Module cleanness
    del Color, color, member
    print("module:", globals())  # only Enum and the default __*__
