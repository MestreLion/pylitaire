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

import themes
import enum

log = logging.getLogger(__name__)


class RANK(enum.Enum):
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


class SUIT(enum.Enum):
    '''Card suits'''
    CLUBS    = 1
    DIAMONDS = 2
    HEARTS   = 3
    SPADES   = 4


class COLORS(enum.Enum):
    '''Card "color". Black for Clubs and Spades, Red for Diamonds and Hearts'''
    BLACK = 1
    RED   = 2


class ORIENTATION(enum.Enum):
    '''Stack orientation of a card in relation to its parent'''
    NONE  = None    # Do not snap
    KEEP  = ()      # Keep the same orientation of the parent
    RIGHT = ( 1,  0)
    LEFT  = (-1,  0)
    DOWN  = ( 0,  1)
    UP    = ( 0, -1)
    PILE  = ( 0,  0)  # No orientation, place on top of card


class Deck(pygame.sprite.LayeredDirty):
    ''' A collection of cards '''

    def __init__(self, theme=None):
        super(Deck, self).__init__()

        self.theme = theme
        if theme:
            self.set_theme(theme)

        self.cardsize = ()
        self.surface = None
        self.back = None

        # Set the cards
        self.cards = []
        self.cardsdict = {}

    def set_theme(self, theme):
        '''Set the card theme for the deck.
            <theme> can be either an instance of themes.Theme
            or a key name, looked up in themes.themes dict,
            theme attribute will always be set as instance, if any
        '''
        # FIXME: changing theme could trigger a .resize()
        if isinstance(theme, themes.Theme):
            self.theme = theme
        else:
            self.theme = themes.themes.get(theme, None)

        if not self.theme:
            log.warn("Theme '%s' not found. Cards will not be drawn", theme)

    def card(self, rank=0, suit=0):
        '''Return a Card of the given rank and suit
            For double decks it may return either card, as they distinct
            instances but otherwise indistinguishable
        '''
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
        self.remove(*self)
        self.cardsdict.clear()
        del self.cards[:]
        if doubledeck:
            decks = 2
        else:
            decks = 1
        for _ in xrange(decks):
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

    def resize(self, maxcardsize=(), proportional=True):
        if not self.theme:
            self.cardsize = ()
            self.surface = None
            self.back = None
            return

        self.surface = self.theme.render(maxcardsize, proportional)
        size = self.surface.get_size()
        self.cardsize = (size[0] / 13,
                         size[1] /  5)
        self.back = self.surface.subsurface(pygame.Rect(
            (2 * self.cardsize[0],
             4 * self.cardsize[1]),
            self.cardsize))

        for card in self.cards:
            card.resize(self.cardsize)

        return self.cardsize


class Card(pygame.sprite.DirtySprite):
    ''' A sprite representing a card '''

    snap_overlap = (0.2, 0.2)

    def __init__(self, rank, suit, deck=None,
                 position=(0, 0), faceup=True, orientation=ORIENTATION.DOWN,
                 slot=None, id=""):
        super(Card, self).__init__()

        if id:
            id = id.upper()
            rank, suit = id[:-1], id[-1]
            if rank in ['J', 'Q', 'K', 'A']:
                for r in RANK:
                    if r.name[1].upper() == rank:
                        rank = r
                        break
            else:
                rank = int(rank)

            for s in SUIT:
                if s.name[1].upper() == suit:
                    suit = s
                    break

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

        if 2 <= self.rank <= 10:
            shortrank = str(self.rank)
        else:
            shortrank = rankname[:1].upper()
        self.shortname = shortrank + suitname[:1].lower()

        self.slot = None
        self.parent = None
        self.child = None
        self.orientation = orientation

        self._drag_offset = self._drag_start_pos = ()

        self.rect = pygame.Rect(position, (0, 0))

        self._faceup = faceup

        # to be defined in resize()
        self.cardimage = None

    def __repr__(self):
        return "<%s(id=%r)>" % (
            self.__class__.__name__, self.shortname)

    def resize(self, cardsize):
        # this can be smarter on resizing to same size,
        # and should take re-theming into account

        self.rect.size = cardsize

        if not self.deck.surface:
            self.cardimage = None
            return

        imgrect = pygame.Rect(((self.rank - 1) * self.rect.width,
                               (self.suit - 1) * self.rect.height),
                              (self.rect.width, self.rect.height))
        self.cardimage = self.deck.surface.subsurface(imgrect)

        if self._faceup:
            self.image = self.cardimage
        else:
            self.image = self.deck.back

        self.dirty = 1

    def start_drag(self, mouse_pos):
        '''Start dragging card and its children. Save the current position
            and mouse offset, so drag() and abort_drag() act as expected.
        '''
        if self._drag_start_pos:
            log.warn("start_drag() called during an ongoing drag. "
                     "Forgot to drop() or abort_drag()?")
        self._drag_start_pos = self.rect.topleft
        self._drag_offset = (mouse_pos[0] - self.rect[0],
                             mouse_pos[1] - self.rect[1])
        self.deck.move_to_front(self)
        if self.child:
            self.child.start_drag(mouse_pos)

    def drag(self, mouse_pos):
        '''Drag a card to current mouse position, recursively dragging
            its children.
        '''
        self.move((mouse_pos[0] - self._drag_offset[0],
                   mouse_pos[1] - self._drag_offset[1]))
        if self.child:
            self.child.drag(mouse_pos)

    def abort_drag(self):
        '''Abort a drag, moving the card and its children back to its original
            position
        '''
        self.move(self._drag_start_pos)
        if self.child:
            self.child.abort_drag()
        self.drop()

    def drop(self):
        '''Drop the card at its current position.
            Actually a No-Op, just discard the values saved by start_drag()
        '''
        self._drag_offset = self._drag_start_pos = ()
        if self.child:
            self.child.drop()

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

    def stack(self, card, orientation=ORIENTATION.KEEP, overlap=()):
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
        self._set_slot(self.parent.slot)

        # snap
        if orientation == ORIENTATION.KEEP:
            orientation = self.parent.orientation
        self.orientation = orientation
        self.snap(card, orientation, overlap)

    def pop(self):
        '''Disconnect from its parent, if any, slicing the stack
            Also disconnect itself and children from the current slot
        '''
        if self.slot and self.slot.child is self:
            self.slot.child = None
        self._set_slot(None)
        if self.parent:
            self.parent.child = None
        self.parent = None

    def snap(self, card, orientation=ORIENTATION.KEEP, overlap=()):
        '''Move the card to a position relative to another card,
            also recursively snap all children
        '''
        if orientation == ORIENTATION.KEEP:
            orientation = card.orientation
        if not overlap:
            overlap = self.snap_overlap
        if orientation != ORIENTATION.NONE:
            self.move((card.rect.x + orientation[0] * overlap[0] * card.rect.w,
                       card.rect.y + orientation[1] * overlap[1] * card.rect.h))
        if self.child:
            self.child.snap(self, orientation, overlap)

    def place(self, slot):
        '''Set the card and children to <slot>, moving it there and snapping
            children according to slot's alignment (orientation and overlap)
        '''
        if slot.child and slot.child is not self:
            log.warn("Trying to place %s in a non-empty slot %s, first card is %s",
                     self, slot, slot.child)
            # disconnect the former child
            slot.child.pop()
        self.pop()
        slot.child = self
        self._set_slot(slot)
        self.orientation = self.slot.orientation
        self.move(self.slot.rect.topleft)
        if self.child:
            self.child.snap(self, self.orientation, self.slot.overlap)

    def _set_slot(self, slot):
        '''Set the card to <slot>, recursively on all children. Used internally
            by place() and stack()
        '''
        # Could be merged with snap(), but for now that is a strictly graphical
        # function, with no logical assignments, and it's not (yet) the time to
        # break that invariant
        self.slot = slot
        if self.child:
            self.child._set_slot(slot)

    @property
    def children(self):
        '''List all descendants, in order, not including itself'''
        if self.child:
            return [self.child] + self.child.children
        else:
            return []

    @property
    def is_tail(self):
        '''Return True if card is the tail (leaf) of its current stack'''
        return not self.child

    @property
    def is_head(self):
        '''Return True if card is the head (root) of its current stack'''
        return not self.parent


class Slot(pygame.sprite.DirtySprite):
    '''A sprite-like object representing a slot
        It has a <rect> for positioning but no <image> since all slots share
        the same image that is only drawn onto background once per resize
    '''
    def __init__(self,
                 cell=(0, 0),
                 orientation=ORIENTATION.PILE,
                 overlap=(0.2, 0.2),
                 position=(0, 0),
                 size=(0, 0),
                 rank=-1,
                 suit=-1,
                 image=None,
                 name=""):
        '''Create slot at position <cell>, a (cx, cy) tuple in game grid units
            logic units, each cell sized card size + margins. Useful for
            repositioning the slot according to board geometry.
            <position>, as opposed to <cell>, is an absolute (x, y) position
            inside the window. <size> is (x, y), should be set to card size.
            Cards dropped will stack with <orientation> and <overlap>.
            <rank> and <suit> can be useful when creating rules for dropping
            cards: usually rank is RANK.ACE - 1 for foundation and
            RANK.KING + 1 for tableau
            <image> is a pygame.Surface that can be used to draw() the slot
        '''
        super(Slot, self).__init__()

        self.name = name
        self.rank = rank
        self.suit = suit
        self.cell = cell
        self.orientation = orientation
        self.overlap = overlap
        self.board = None

        self.child = None  # Card instance, set by card on place()
        self.rect = pygame.sprite.Rect(position, size)
        self.image = image

    def __repr__(self):
        if self.name:
            return "<%s(%r, name=%r)>" % (
                self.__class__.__name__, self.cell, self.name)
        else:
            return "<%s(%r)>" % (self.__class__.__name__, self.cell)

    def resize(self, cardsize):
        '''Resize the slot to <cardsize> (width, height)'''
        self.rect.size = cardsize

    def move(self, position):
        '''Move the slot to an absolute (x, y) window position'''
        self.rect.topleft = position

    def boardmove(self, geometry):
        '''Reposition according to board <geometry> and current (logical) cell
            grid position, moving its cards accordingly.
            <geometry> is a pygame.Rect indicating the top left cell, ie, the
            absolute position of cell (0, 0) and the board cell size.
        '''
        self.move((geometry.x + self.cell[0] * geometry.size[0],
                   geometry.y + self.cell[1] * geometry.size[1]))
        if self.child:
            self.child.place(self)

    def draw(self, destsurface, image=None):
        '''Blit the slot to a destination <surface>.
            If <image> is given, it will be used as the slot surface
            and saved for future drawings
        '''
        if image:
            self.image = image
        destsurface.blit(self.image, self.rect)

    def fit(self, board=None):
        if board:
            self.board = board

        cards = self.cards
        length = float(len(cards))
        if length < 2 or self.orientation == ORIENTATION.PILE:
            return # nothing to do

        tail = cards[-1]

        if   self.orientation == ORIENTATION.UP:    i=1; attrib = 'top'
        elif self.orientation == ORIENTATION.DOWN:  i=1; attrib = 'bottom'
        elif self.orientation == ORIENTATION.LEFT:  i=0; attrib = 'left'
        elif self.orientation == ORIENTATION.RIGHT: i=0; attrib = 'right'

        edge = getattr(self.rect, attrib)
        dist = self.orientation[i] * self.rect.size[i] * (length - 1)
        max_overlap  = (getattr(self.board, attrib) - edge) / dist
        cur_overlap  = (getattr(tail.rect,  attrib) - edge) / dist

        # overboard or compressed
        if max_overlap < cur_overlap or round(cur_overlap, 2) < self.overlap[i]:
            overlap = min(self.overlap[i], max_overlap)
            log.debug("Fit slot overlap from %.3f, max %.3f, to %.3f",
                      cur_overlap, max_overlap, overlap)
            self.child.child.snap(self.child, self.orientation,
                                  (overlap, overlap))

    @property
    def empty(self):
        '''Return True if the stack is empty'''
        return not self.child

    @property
    def head(self):
        '''Return the stack top card (ie, bottom layer), if any'''
        return self.child
    top = head

    @property
    def tail(self):
        '''Return the stack tip card (ie, topmost layer), if any'''
        if self.child:
            return self.cards[-1]
    tip = tail

    @property
    def cards(self):
        '''Return a list of all cards in this slot, in stack order'''
        if self.child:
            return [self.child] + self.child.children
        else:
            return []




if __name__ == '__main__':
    # unit tests

    # setup
    logging.basicConfig(level=logging.DEBUG)
    pygame.init()
    clock = pygame.time.Clock()
    window = pygame.display.set_mode((800, 600))
    window.fill((0, 80, 16))
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
