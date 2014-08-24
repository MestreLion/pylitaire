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
# Card handling, game rules independent

import logging
import random

import pygame

import g
import themes

log = logging.getLogger(__name__)


class RANK(g.Enum):
    '''Card ranks'''
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


class SUIT(g.Enum):
    '''Card suits'''
    CLUBS    = 1
    DIAMONDS = 2
    HEARTS   = 3
    SPADES   = 4


class COLORS(g.Enum):
    '''Card "color". Black for Clubs and Spades, Red for Diamonds and Hearts'''
    BLACK = 1
    RED   = 2


class ORIENTATION(g.Enum):
    '''Stack orientation'''
    NONE  = None    # Do not snap
    KEEP  = ()      # Use same orientation of last stacking
    RIGHT = (1, 0)
    DOWN  = (0, 1)
    PILE  = (0, 0)  # No orientation, place on top or card


class Deck(pygame.sprite.LayeredDirty):
    ''' A collection of cards '''

    def __init__(self, theme=None, cardsize=(), proportional=True):
        super(Deck, self).__init__()

        # theme can be either a name or an instance of themes.Theme
        # self.theme is always an instance
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

    def create_cards(self, doubledeck=False, jokers=0, **cardkwargs):
        for suit in SUIT:
            for rank in RANK:
                card = Card(rank=rank, suit=suit, deck=self, **cardkwargs)
                self.add(card)
                self.cards.append(card)
                self.cardsdict[(rank, suit)] = card

    def pop_cards(self):
        '''Break all stacks, pop()'ing each card'''
        for card in self.cards:
            card.pop()

    def resize(self, cardsize):
        for card in self.cards:
            card.resize(cardsize)


class Card(pygame.sprite.DirtySprite):
    ''' A sprite representing a card '''

    snap_overlap = (0.2, 0.2)

    def __init__(self, rank, suit, deck=None,
                 position=(0, 0), faceup=True, orientation=ORIENTATION.DOWN):
        super(Card, self).__init__()

        self.rank = rank
        self.suit = suit
        self.deck = deck

        if self.suit in [SUIT.CLUBS, SUIT.SPADES]:
            self.color = COLORS.BLACK
        else:
            self.color = COLORS.RED

        rankname = RANK.name(self.rank)
        suitname = SUIT.name(self.suit)
        self.name = "%s of %s" % (rankname, suitname)

        if self.rank <= 10:
            shortrank = str(self.rank)
        else:
            shortrank = rankname[:1].upper()
        self.shortname = shortrank + suitname[:1].lower()

        self.parent = None
        self.child = None
        self.orientation = orientation

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
        if self._faceup:
            self.image = self.cardimage
        else:
            self.image = self.deck.back

    def __repr__(self):
        return "<%s(rank=%2d, suit=%r)>" % (
            self.__class__.__name__, self.rank, self.suit)

    def resize(self, cardsize):
        self.dirty = 1

    def start_drag(self, mouse_pos):
        '''Start dragging card. Save the current position and mouse offset,
            so drag() and abort_drag() act as expected.
        '''
        if self._drag_start_pos:
            log.warn("start_drag() called during an ongoing drag. "
                     "Forgot to drop() or abort_drag()?")
        self._drag_start_pos = self.rect.topleft
        self._drag_offset = (mouse_pos[0] - self.rect[0],
                             mouse_pos[1] - self.rect[1])
        self.deck.move_to_front(self)

    def drag(self, mouse_pos):
        '''Drag a card to current mouse position, recursively dragging
            its children as a stack.
        '''
        self.move((mouse_pos[0] - self._drag_offset[0],
                   mouse_pos[1] - self._drag_offset[1]))
        if self.child:
            self.child.snap(self, ORIENTATION.KEEP)

    def abort_drag(self):
        '''Abort a drag, moving the card back to its original position
            and adjusting its children accordingly
        '''
        self.move(self._drag_start_pos)
        self.drop()
        if self.child:
            self.child.snap(self, ORIENTATION.KEEP)

    def drop(self):
        '''Drop the card at its current position.
            Actually a No-Op, just discard the values saved by start_drag()
        '''
        self._drag_offset = self._drag_start_pos = ()

    stop_drag = drop

    def move(self, pos):
        '''Move the card to <pos>, a (x, y) tuple'''
        self.dirty = 1
        self.rect.topleft = pos
        self.deck.move_to_front(self)

    @property
    def faceup(self):
        '''If card is faced up or down. Read-only. To change state, use flip()'''
        return self._faceup

    def flip(self, faceup=None):
        '''Flip a card either face up, down, or toggle'''
        if faceup is None:
            faceup = not self._faceup
        self._faceup = faceup
        if self._faceup:
            self.image = self.cardimage
        else:
            self.image = self.deck.back
        self.dirty = 1

    def start_peep(self):
        '''Temporarily show this card above all others'''
        pass

    def stop_peep(self):
        '''Send the card back to its original Z-Order'''
        pass

    def stack(self, card, orientation=ORIENTATION.KEEP):
        '''Snap to <card> as a child, forming a stack'''
        if card is self:
            log.warn("Trying to stack %s with itself", self)
            return
        if card in self.children:
            log.warn("Trying to stack %s with its descendant %s", self, card)
            # disconnect the descendant
            card.pop()
        if card.child:
            log.warn("Trying to stack %s to %s which already have a child %s",
                     self, card, card.child)
            # disconnect the former child
            card.child.pop()

        # disconnect from old parent
        self.pop()

        # connect to new one
        self.parent = card
        self.parent.child = self

        # snap
        if orientation == ORIENTATION.KEEP:
            orientation = self.orientation
        self.orientation = orientation
        self.snap(card, orientation)

    def pop(self):
        '''Disconnect from its parent, if any, slicing the stack'''
        if self.parent:
            self.parent.child = None
        self.parent = None

    def snap(self, card, orientation=ORIENTATION.KEEP):
        '''Move the card to a position relative to another card,
            also recursively snap all children
        '''
        if orientation == ORIENTATION.KEEP:
            orientation = self.orientation
        if orientation != ORIENTATION.NONE:
            self.move((card.rect.x + orientation[0] * self.snap_overlap[0] * card.rect.width,
                       card.rect.y + orientation[1] * self.snap_overlap[1] * card.rect.height))
        if self.child:
            self.child.snap(self, orientation)

    @property
    def children(self):
        '''List all descendants, in order, not including itself'''
        if self.child:
            return [self.child] + self.child.children
        else:
            return []

    @property
    def stacktail(self):
        '''Return True if card is the tail (leaf) of its current stack'''
        return not self.child

    @property
    def stackhead(self):
        '''Return True if card is the head (root) of its current stack'''
        return not self.parent




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
    card = Card(RANK.QUEEN, SUIT.HEARTS)
    print card, card.shortname, card.name
    window.blit(card.image, (0, 0))
    pygame.display.update()

    # Deck
    deck = Deck()
    print len(deck.cards)
    print deck.card(RANK.ACE, SUIT.SPADES)
    print deck.cards[:5]
    deck.shuffle()
    print deck.cards[:5]
