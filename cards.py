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
# Card handling

import logging
import random

import pygame

import g
import themes

log = logging.getLogger(__name__)


class Enum(object):
    ''' A basic implementation of Enums in Python '''

    @classmethod
    def name(cls, value):
        ''' Quick-and-dirty fallback for getting the "name" of an enum item
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
            for name, value in sorted(self.__dict__.items(), key=lambda _: _[1]):
                if (not name.startswith("_") and
                    not name in ['name'] + getattr(self, '__non_members__', [])):
                    yield value
    __metaclass__ = _meta


class RANKS(Enum):
    ''' Card ranks '''
    ACE   =  1
    TWO   =  2
    THREE =  3
    FOUR  =  4
    FIVE  =  5
    SIX   =  6
    SEVEN =  7
    EIGHT =  8
    NINE  =  9
    TEN   = 10
    JACK  = 11
    QUEEN = 12
    KING  = 13


class SUITS(Enum):
    ''' Card suits '''
    CLUBS    = 1
    DIAMONDS = 2
    HEARTS   = 3
    SPADES   = 4


class COLORS(Enum):
    BLACK = 1
    RED   = 2


class Deck(object):
    ''' A collection of cards '''

    def __init__(self, theme=None):
        self.cards = []
        self.cardsdict = {}
        for suit in SUITS:
            for rank in RANKS:
                card = Card(rank=rank, suit=suit, theme=theme)
                self.cards.append(card)
                self.cardsdict[(rank, suit)] = card

    def card(self, rank=0, suit=0):
        ''' Return a Card of the given rank and suit '''
        return self.cardsdict[(rank, suit)]

    def shuffle(self):
        ''' Shuffles the deck cards in-place. Return None '''
        random.shuffle(self.cards)




class Card(pygame.sprite.Sprite):
    ''' A sprite representing a card '''

    def __init__(self, rank=0, suit=0, joker=False, color=0, back=False, theme=None):
        super(Card, self).__init__()

        self.rank = rank
        self.suit = suit

        if self.rank in [SUITS.CLUBS, SUITS.SPADES]:
            self.color = COLORS.BLACK
        else:
            self.color = COLORS.RED

        rankname = RANKS.name(self.rank)
        suitname = SUITS.name(self.suit)
        self.name = "%s of %s" % (rankname, suitname)

        if self.rank <= 10:
            shortrank = str(self.rank)
        else:
            shortrank = rankname[:1].upper()
        self.shortname = shortrank + suitname[:1].lower()

        if isinstance(theme, themes.Theme):
            self.theme = theme
        else:
            theme = theme or g.theme
            self.theme = themes.themes.get(theme, None)

        if not self.theme:
            log.warn("Theme '%s' not found. Card will not be drawable", theme)
            self.rect = pygame.Rect(0, 0, 0, 0)
            self.image = pygame.Surface((0, 0))
            return

        self.rect = pygame.Rect((0, 0), (self.theme.surface.get_rect().width  / 13.,
                                         self.theme.surface.get_rect().height /  5.))
        imgrect = pygame.Rect(((self.rank - 1) * self.rect.width,
                               (self.suit - 1) * self.rect.height),
                              (self.rect.width, self.rect.height))
        self.image = self.theme.surface.subsurface(imgrect)

    def __repr__(self):
        return "<%s(rank=%2d, suit=%r)>" % (
            self.__class__.__name__, self.rank, self.suit)




if __name__ == '__main__':
    # unit tests

    # setup
    logging.basicConfig(level=logging.DEBUG)
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(g.screen_size)
    screen.fill(g.BGCOLOR)
    pygame.display.update()
    themes.init_themes()

    # Card
    card = Card(RANKS.QUEEN, SUITS.HEARTS)
    print card, card.shortname, card.name
    screen.blit(card.image, (0, 0))
    pygame.display.update()

    # Deck
    deck = Deck()
    print len(deck.cards)
    print deck.card(RANKS.ACE, SUITS.SPADES)
    print deck.cards[:5]
    deck.shuffle()
    print deck.cards[:5]
