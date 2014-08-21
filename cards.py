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


class RANKS(g.Enum):
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


class SUITS(g.Enum):
    ''' Card suits '''
    CLUBS    = 1
    DIAMONDS = 2
    HEARTS   = 3
    SPADES   = 4


class COLORS(g.Enum):
    BLACK = 1
    RED   = 2


class Deck(pygame.sprite.LayeredDirty):
    ''' A collection of cards '''

    def __init__(self, theme=None, cardsize=(), proportional=True):

        # Set the theme (self.theme is always an instance of themes.Theme)
        if isinstance(theme, themes.Theme):
            self.theme = theme
        else:
            theme = theme or g.theme
            self.theme = themes.themes.get(theme, None)

        if self.theme:
            self.surface = self.theme.render(cardsize, proportional)
            size = self.surface.get_size()
            self.cardsize = (size[0] / 13,
                             size[1] /  5)
        else:
            log.warn("Theme '%s' not found. Cards will not be drawable", theme)
            self.surface = None
            self.cardsize = ()

        # Set the cards
        self.cards = []
        self.cardsdict = {}
        for suit in SUITS:
            for rank in RANKS:
                card = Card(rank=rank, suit=suit, deck=self, position=g.MARGIN)
                self.cards.append(card)
                self.cardsdict[(rank, suit)] = card

        # Add all cards to the group
        super(Deck, self).__init__(self.cards)

        # Special cards
        if self.surface:
            self.back = self.surface.subsurface(pygame.Rect(
                (2 * self.cardsize[0],
                 4 * self.cardsize[1]),
                self.cardsize))

    def card(self, rank=0, suit=0):
        ''' Return a Card of the given rank and suit '''
        return self.cardsdict[(rank, suit)]

    def shuffle(self):
        ''' Shuffle the deck cards in-place. Return None '''
        self.empty()
        random.shuffle(self.cards)
        self.add(*self.cards)

    def get_top_card(self, pos):
        cards = self.get_sprites_at(pos)
        if cards:
            return cards[-1]  # last card is top card


class Card(pygame.sprite.DirtySprite):
    ''' A sprite representing a card '''

    def __init__(self, rank=0, suit=0, joker=False, color=0, back=False,
                 deck=None, position=(0, 0), faceup=True):
        super(Card, self).__init__()

        self.rank = rank
        self.suit = suit
        self.deck = deck

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

        self._drag_offset = self._drag_start_pos = ()

        if not self.deck.surface:
            self.rect = pygame.Rect(position, (0, 0))
            self.image = pygame.Surface((0, 0))
            return

        self.rect = pygame.Rect(position, self.deck.cardsize)
        imgrect = pygame.Rect(((self.rank - 1) * self.rect.width,
                               (self.suit - 1) * self.rect.height),
                              (self.rect.width, self.rect.height))
        self.cardimage = self.deck.surface.subsurface(imgrect)

        self._faceup = faceup
        self.image = None
        self.flip(self._faceup)


    def __repr__(self):
        return "<%s(rank=%2d, suit=%r)>" % (
            self.__class__.__name__, self.rank, self.suit)

    def drag_start(self, mouse_pos):
        assert not self._drag_offset, "drag_start() called during an ongoing drag."
        self._drag_start_pos = self.rect.topleft
        self._drag_offset = (mouse_pos[0] - self.rect[0],
                             mouse_pos[1] - self.rect[1])
        pygame.mouse.set_cursor(*g.cursors['drag'])
        self.deck.move_to_front(self)

    def drag(self, mouse_pos):
        self.move((mouse_pos[0] - self._drag_offset[0],
                   mouse_pos[1] - self._drag_offset[1]))

    def drag_abort(self, *args):
        self.rect.topleft = self._drag_start_pos
        self.drag_stop()

    def drag_stop(self, *args):
        self._drag_offset = self._drag_start_pos = ()
        pygame.mouse.set_cursor(*g.cursors['draggable'])

    drop = drag_stop

    @property
    def draggable(self, *args):
        return self._faceup

    def move(self, pos):
        self.dirty = 1
        self.rect.topleft = pos

    @property
    def faceup(self):
        return self._faceup

    def flip(self, faceup=None):
        '''Flip a card, either <faceup> or down. If no <faceup>, toggle state'''
        if faceup is None:
            faceup = not self._faceup  # perhaps should be self.faceup
        self._faceup = faceup
        if self._faceup:
            self.image = self.cardimage
        else:
            self.image = self.deck.back
        self.dirty = 1

    @property
    def flippable(self):
        return True




if __name__ == '__main__':
    # unit tests

    # setup
    logging.basicConfig(level=logging.DEBUG)
    pygame.init()
    clock = pygame.time.Clock()
    window = pygame.display.set_mode(g.window_size)
    window.fill(g.BGCOLOR)
    pygame.display.update()
    themes.init_themes()

    # Card
    card = Card(RANKS.QUEEN, SUITS.HEARTS)
    print card, card.shortname, card.name
    window.blit(card.image, (0, 0))
    pygame.display.update()

    # Deck
    deck = Deck()
    print len(deck.cards)
    print deck.card(RANKS.ACE, SUITS.SPADES)
    print deck.cards[:5]
    deck.shuffle()
    print deck.cards[:5]
