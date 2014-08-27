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

'''Game rules and logic

Design notes:
- Game rules should not depend on any other module than cards
- Talks to Deck/Card only via API, but should not rely on its implementation internals
- Talks to GUI only via high-level events such as `click(card)`, `drop(card)`, etc
'''

import logging

import cards

log = logging.getLogger(__name__)


_games = {}

def load_game(gamename):
    if not _games:
        load_games()

    gameclass = _games.get(gamename, None)
    if not gameclass:
        log.error("Game '%s' not found", gamename)
        return

    game = gameclass()
    log.info("Loading game '%s'", game.name)
    return game


def load_games():
    def list_classes(base):
        for cls in base.__subclasses__():
            _games[cls.__name__.lower()] = cls
            list_classes(cls)
    list_classes(Game)
    return _games


class Game(object):
    def __init__(self):
        self.grid = (0, 0)
        self.slots = []
        self.deck = cards.Deck()
        self.name = self.__class__.__name__

    def create_slot(self, *slotargs, **slotkwargs):
        '''Create a game slot. See cards.Slot for arguments'''
        slot = cards.Slot(*slotargs, **slotkwargs)
        self.slots.append(slot)
        return slot

    def new_game(self):
        self.restart(True)

    def restart(self, new=False):
        if new:
            log.info("New game")
            self.deck.shuffle()
        else:
            log.info("Restart game")
        self.deck.pop_cards()
        self.reset()

    def get_top_card_or_slot(self, pos):
        '''Return the top card at <pos>, or a slot, if any'''
        card = self.deck.get_top_card(pos)
        if card:
            return card
        for slot in self.slots:
            if slot.rect.collidepoint(pos):
                return slot


class Klondike(Game):
    def __init__(self):
        super(Klondike, self).__init__()

        self.grid = (7, 4)  # size of play area, measured in card "cells"

        self.stock = self.create_slot((0, 0))
        self.waste = self.create_slot((1, 0))

        self.foundations = []
        for i in xrange(self.grid[0] - 4, self.grid[0]):
            self.foundations.append(self.create_slot((i, 0)))

        self.tableau = []
        for i in xrange(self.grid[0]):
            self.tableau.append(self.create_slot((i, 1),
                                                 cards.ORIENTATION.DOWN))

        self.deck.create_cards(doubledeck=False, jokers=0, faceup=False)


    def reset(self):
        '''Called once per game, either new one or restart same game'''
        c = 0

        for col, slot in enumerate(self.tableau):
            for row in xrange(col + 1):
                card = self.deck.cards[c]
                card.flip(row >= col)
                if row == 0:
                    card.place(slot)
                else:
                    card.stack(self.deck.cards[c-1])
                c += 1

        self.deck.cards[c].place(self.stock)
        c += 1
        for card in self.deck.cards[c:]:
            card.stack(self.deck.cards[c-1])
            card.flip(False)
            c += 1

    def click(self, card):
        '''Handle click on <card>, which may be a slot.
            Return True if card state changed
        '''
        if card in self.slots:
            if card is self.stock and not self.waste.empty:
                cards = self.waste.cards[::-1]
                for c, card in enumerate(cards):
                    if c == 0:
                        card.place(self.stock)
                    else:
                        card.stack(cards[c-1])
                    card.flip()
                return True

        elif card.stacktail and not card.faceup:
            if card.headslot is self.stock:
                if self.waste.empty:
                    card.place(self.waste)
                else:
                    card.stack(self.waste.tail)
            card.flip()
            return True

    def doubleclick(self, card):
        '''Handle double click on <card>. Return True if card state changed'''
        if card in self.slots or card.slot in self.foundations:
            return

        targets = []
        for slot in self.foundations:
            if slot.empty:
                targets.append(slot)
            else:
                targets.append(slot.tail)

        droplist = self.droppable(card, targets)
        if droplist:
            self.drop(card, droplist[0])
            return True

    def drop(self, card, target):
        '''Handle <card> dropped onto <target>'''
        if target in self.slots:
            card.place(target)
        else:
            card.stack(target)

    def draggable(self, card):
        '''Return True if card can be dragged.
            Used to set mouse cursor. Actual drag is performed by GUI
        '''
        return (card not in self.slots
                and card.faceup)
                # and not card.headslot in self.foundations

    def droppable(self, card, targets):
        '''Return a subset of <targets> that are valid drop cards for <card>'''
        droplist = []
        for target in targets:

            # dropping to a slot
            if target in self.slots:
                if not target.empty:
                    continue
                if target in self.foundations:
                    if card.stacktail and card.rank == cards.RANK.ACE:
                        droplist.append(target)
                elif target in self.tableau:
                    if card.rank == cards.RANK.KING:
                        droplist.append(target)
                continue

            headslot = target.headslot

            # dropping to card in foundation
            if headslot in self.foundations:
                if (card.stacktail
                    and target.stacktail
                    and target.suit == card.suit
                    and target.rank == card.rank - 1):
                    droplist.append(target)

            # droppping to card in tableau
            elif headslot in self.tableau:
                if (target.faceup
                    and target.stacktail
                    and target.color != card.color
                    and target.rank == card.rank + 1):
                    droplist.append(target)

        return droplist


class Yukon(Klondike):
    def __init__(self):
        super(Yukon, self).__init__()
        self.slots.remove(self.stock)
        self.slots.remove(self.waste)

    def reset(self):
        super(Yukon, self).reset()
        e = 4  # extra cards in each but the first column
        i = 0
        while not self.stock.empty:
            card = self.stock.tail
            card.flip()
            card.stack(self.tableau[1 + i/e].tail)
            i += 1


class Pylitaire(Klondike):
    '''Yukon variation: 8 tableau slots with 2 extra open cards in each
        (including the first tableau slot)
    '''
    def __init__(self):
        super(Pylitaire, self).__init__()
        self.slots.remove(self.stock)
        self.slots.remove(self.waste)
        self.grid = (8, 4)
        self.tableau.append(self.create_slot((7, 1), cards.ORIENTATION.DOWN))
        for foundation in self.foundations:
            foundation.cell = (foundation.cell[0] + 1, 0)

    def reset(self):
        super(Pylitaire, self).reset()
        e = 2  # extra cards in each column
        i = 0
        while not self.stock.empty:
            card = self.stock.tail
            card.flip()
            card.stack(self.tableau[i/e].tail)
            i += 1
