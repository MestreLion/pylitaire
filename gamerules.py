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
        get_games()

    gameclass = _games.get(gamename, None)
    if not gameclass:
        log.error("Game '%s' not found", gamename)
        return

    game = gameclass()
    log.info("Loading game '%s'", game.name)
    return game


def get_games():
    def list_classes(base):
        for cls in base.__subclasses__():
            _games[cls.__name__.lower()] = cls
            list_classes(cls)
    _games.clear()
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

    def status(self):
        '''Status message string that will be displayed for the game by GUI
            at intervals. By default message is:
                Stock left: <stock>  Redeals left: <redeals>
            <stock> is the number of cards in self.stock slot, or the first
            slot in self.slots, if such slot exists.
            <redeals>
        '''
        messages = []

        stock = (getattr(self, "stock", None)
                 or self.slots[0] if self.slots else None)
        if isinstance(stock, cards.Slot):
            messages.append("Stock left: %d" % len(self.slots[0].cards))

        redeals = getattr(self, "redeals", None)
        if redeals is not None:
            messages.append("Redeals left: %d" % redeals)

        return "  ".join(messages)

    def score(self):
        score = 0
        for slot in getattr(self, "foundations", []):
            score += len(slot.cards)
        return score

    def win(self):
        return self.score() == len(self.deck.cards)


class Klondike(Game):
    def __init__(self):
        super(Klondike, self).__init__()

        self.grid = (7, 3)  # size of play area, measured in card "cells"

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

        card = self.deck.cards[c]
        card.place(self.stock)
        card.flip(False)

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

        elif card.is_tail and not card.faceup:
            if card.slot is self.stock:
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
                # and not card.slot in self.foundations

    def droppable(self, card, targets):
        '''Return a subset of <targets> that are valid drop cards for <card>'''
        droplist = []
        for target in targets:

            # dropping to a slot
            if target in self.slots:
                if not target.empty:
                    continue
                if target in self.foundations:
                    if card.is_tail and card.rank == cards.RANK.ACE:
                        droplist.append(target)
                elif target in self.tableau:
                    if card.rank == cards.RANK.KING:
                        droplist.append(target)
                continue

            # dropping to card in foundation
            if target.slot in self.foundations:
                if (card.is_tail
                    and target.is_tail
                    and target.suit == card.suit
                    and target.rank == card.rank - 1):
                    droplist.append(target)

            # dropping to card in tableau
            elif target.slot in self.tableau:
                if (target.faceup
                    and target.is_tail
                    and target.color != card.color
                    and target.rank == card.rank + 1):
                    droplist.append(target)

        return droplist


class Yukon(Klondike):
    def __init__(self):
        super(Yukon, self).__init__()
        self.grid = (7, 4)
        self.slots.remove(self.stock)
        self.slots.remove(self.waste)

    def reset(self, e=4, j=1):
        '''Parametrized to be variation-friendly:
            <e>: extra cards in each column
            <j>: start column for extra cards
        '''
        super(Yukon, self).reset()
        i = 0
        while not self.stock.empty:
            card = self.stock.tail
            card.flip(True)
            card.stack(self.tableau[j + i/e].tail)
            i += 1

    def status(self):
        return "Cards to uncover: %d" % sum((1 if not _.faceup else 0
                                             for _ in self.deck))


class Pylitaire(Yukon):
    '''Yukon variation: 8 tableau slots with 2 extra open cards in each
        (including the first tableau slot)
    '''
    def __init__(self):
        super(Pylitaire, self).__init__()
        self.grid = (8, 4)
        self.tableau.append(self.create_slot((7, 1), cards.ORIENTATION.DOWN))
        for foundation in self.foundations:
            foundation.cell = (foundation.cell[0] + 1, 0)

    def reset(self):
        super(Pylitaire, self).reset(2, 0)


class Backbone(Game):
    def __init__(self):
        super(Backbone, self).__init__()

        self.grid = (8, 4)
        self.redeals = 1

        self.stock = self.create_slot((5, 2))
        self.waste = self.create_slot((6, 2))

        self.foundations = []
        for i in xrange(8):
            self.foundations.append(self.create_slot((4 + i%4, i/4)))

        self.tableau = []
        for i in xrange(8):
            self.tableau.append(self.create_slot((3 * (i/4), i%4)))

        self.backbone = []
        for i in xrange(18):
            self.backbone.append(self.create_slot((1 + i/9, 0.33 * (i%9))))

        for i, slot in enumerate(self.backbone[:-1]):
            slot.blockedby = self.backbone[i+1]

        self.block = self.create_slot((1.5, 3))
        for i in [8, 17]:
            self.backbone[i].blockedby = self.block

        self.deck.create_cards(doubledeck=True)

    def reset(self):
        c = 0
        for slot in self.tableau + self.backbone + [self.block]:
            card = self.deck.cards[c]
            card.place(slot)
            card.flip(True)
            c += 1

        card = self.deck.cards[c]
        card.place(self.stock)
        card.flip(False)

        c += 1
        for card in self.deck.cards[c:]:
            card.stack(self.deck.cards[c-1])
            card.flip(False)
            c += 1

        self.redeals = 1

    def click(self, card):
        if card in self.slots:
            if (card is self.stock
                and not self.waste.empty
                and self.redeals > 0):
                self.redeals -= 1
                cards = self.waste.cards[::-1]
                for c, card in enumerate(cards):
                    if c == 0:
                        card.place(self.stock)
                    else:
                        card.stack(cards[c-1])
                    card.flip()
                return True

        elif card.is_tail and not card.faceup:
            if card.slot is self.stock:
                if self.waste.empty:
                    card.place(self.waste)
                else:
                    card.stack(self.waste.tail)
            card.flip()
            return True

    def doubleclick(self, card):
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
        if target in self.slots:
            card.place(target)
        else:
            card.stack(target)

    def draggable(self, card):
        return (card not in self.slots
                and not (card.slot is self.stock
                         or (card.slot in self.backbone
                             and not card.slot.blockedby.empty)))
                # and not card.slot in self.foundations

    def droppable(self, card, targets):
        droplist = []
        for target in targets:

            # dropping to a slot
            if target in self.slots:
                if not target.empty:
                    continue
                if target in self.foundations:
                    if card.is_tail and card.rank == cards.RANK.ACE:
                        droplist.append(target)
                elif target in self.tableau:
                        droplist.append(target)
                continue

            # dropping to card in foundation
            elif target.slot in self.foundations:
                if (card.is_tail
                    and target.is_tail
                    and target.suit == card.suit
                    and target.rank == card.rank - 1):
                    droplist.append(target)

            # dropping to card in tableau
            elif target.slot in self.tableau:
                if (target.is_tail
                    and target.suit == card.suit
                    and target.rank == card.rank + 1):
                    droplist.append(target)

        return droplist
