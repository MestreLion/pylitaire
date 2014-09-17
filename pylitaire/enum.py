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

'''Module for the Enum class'''

class Enum(object):
    '''A basic implementation of Enums for Python 2'''

    @classmethod
    def name(cls, value):
        '''Quick-and-dirty fallback for getting the "name" of an enum item
            Enums can customize the name by overwriting this method
        '''

        # value as string, if it matches an enum attribute.
        # Allows short usage as Enum.name("VALUE") besides Enum.name(Enum.VALUE)
        if hasattr(cls, str(value)):
            return cls.name(getattr(cls, value, None))

        # value not handled in subclass name()
        for k, v in cls.__dict__.items():
            if v == value:
                return k.replace('_', ' ').title()

        # value not found
        raise KeyError("Value '%s' not found in enum '%s'" %
                       (value, cls.__name__))

    class _meta(type):
        def __iter__(self):  # "self" for a metaclass refers to classes, not instances
            '''Yield members sorted by value, not declaration order'''
            for name, value in sorted(self.__dict__.items(), key=lambda _: _[1]):
                if (not name.startswith("_") and
                    not name in ['name'] + getattr(self, '__non_members__', [])):
                    yield value
    __metaclass__ = _meta
