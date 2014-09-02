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


class Command():
    def __init__(self, command, *args, **kwargs):
        self.command = command
        self.args    = args
        self.kwargs  = kwargs

    def execute(self):
        self.command(*self.args, **self.kwargs)

    def __repr__(self):
        args = [str(_) for _ in self.args]
        args.extend(("%s=%s" % (k, v) for k, v in self.kwargs.items()))
        return "<%s.%s(%s)>" % (
            self.command.im_self,
            self.command.__name__,
            ", ".join(args))


class Game(object):
    '''Base class for all game rules.'''
    def __init__(self):
        '''Each of these attributes are required to exist in subclasses:

        <grid>
            The (cx, cy) size of the board, in card units. Default is (0, 0),
            games should redefine this to its own size

        <slots>
            A list of all slots used by the game, empty by default. Games can
            use self.create_slot() to automatically populate this.

        <deck>
            cards.Deck instance to create and handle the cards. Default is a
            deck with no cards. Games should use deck.create_cards() with
            arguments for single or double deck, jokers or not, etc.

        <name>
            The name of the game. By default set to the name of the class.
            Games can redefine this.

        Boilerplate for simple game:

        class SuperSolitaire(Game):
            def __init__(self):
                super(SuperSolitaire, self).__init__()
                self.name = "My Super Solitaire!"
                self.grid = (2, 1)
                self.stock = self.create_slot((0, 0))
                self.waste = self.create_slot((1, 0))
                self.deck.create_cards(doubledeck=True)

        See Klondike for a more realistic game, and Yukon for an example on
        how to subclass an existing game to create a variant.
        '''
        self.grid = (0, 0)
        self.slots = []
        self.deck = cards.Deck()
        self.name = self.__class__.__name__
        self.undocmds = []

    def create_slot(self, *slotargs, **slotkwargs):
        '''Create a game slot. See cards.Slot for arguments.
            A convenience wrapper to be used by subclasses that automatically
            keeps track of all slots created by adding them to self.slots list
        '''
        slot = cards.Slot(*slotargs, **slotkwargs)
        self.slots.append(slot)
        return slot

    def new_game(self):
        '''Handle a New Game event. Simply shuffle cards and call restart()'''
        log.info("New game")
        self.deck.shuffle()
        self.restart(nolog=True)

    def restart(self, nolog=False):
        '''Handle a Restart Game event. Break all stacks and run setup()'''
        if not nolog:
            log.info("Restart game")
        self.undocmds = []
        self.deck.pop_cards()
        self.setup()

    def get_top_item(self, pos):
        '''Return the top item at <pos>, either card or slot, if any.
            Called by GUI
        '''
        card = self.deck.get_top_card(pos)
        if card:
            return card
        for slot in self.slots:
            if slot.rect.collidepoint(pos):
                return slot

    def undoable(self):
        return bool(self.undocmds)

    def undo(self):
        command = self.undocmds.pop()
        if isinstance(command, Command):
            log.debug("Executing undo: %s", command)
            command.execute()
        else:
            for cmd in reversed(command):
                log.debug("Executing undo: %s", cmd)
                cmd.execute()

    # Methods below are meant to be overwritten by subclasses to suit its rules

    def setup(self):
        '''Set up the board, called on new game and restart.
            Games should override or extend this method.
        '''
        pass

    def click(self, item):
        '''Handle click on <element>, either card or slot.
            Games should override or extend this method.
            By default flip() cards and do nothing on slots
            Return True if card state changed.
        '''
        if not item in self.slots:
            item.flip()
            return True

    def doubleclick(self, item):
        '''Handle double click on <widget>, either card or slot.
            Games should override this method, which do nothing by default.
        '''
        pass

    def drop(self, card, target):
        '''Handle drop <card> on a <target>, target may be a card or a slot.
            By default stack() or place() on target, depending on target type.
            This method is only triggered by GUI for a valid drop target, as
            defined by droppable(), so the default action should suit any game.
            Extend this only if game needs additional actions when dropping
            cards.
        '''
        slot = card.slot

        if target in self.slots:
            card.place(target)
        else:
            card.stack(target)

        if slot.empty:
            self.undocmds.append(Command(card.place, slot))
        else:
            self.undocmds.append(Command(card.stack, slot.tail))

    def draggable(self, card):
        '''Return True if <card> can be dragged. This just helps GUI to choose
            which mouse cursor to use on hovering. The actual card drag is
            performed later by GUI
            Games should override this method, which by default return True
            for any card that is faced up
        '''
        return card.faceup

    def droppable(self, card, targets):
        '''Return a subset of <targets> that are valid drop places for <card>
            By default return all targets that are either empty slots or cards
            that are tail of its stack.
            Games should override or extend this method to further filter
            target list according to game rules, as default is very permissive
            and only meant as an initial, "no-brainer" filter
        '''
        droplist = []
        for target in targets:

            # dropping to a slot
            if target in self.slots:
                if target.empty:
                    droplist.append(target)

            # dropping to card
            else:
                if target.is_tail:
                    droplist.append(target)

        return droplist

    def status(self):
        '''Status message string that will be displayed for the game by GUI
            at intervals. Default message is:

                Stock left: <stock>  Redeals left: <redeals>

            <stock> is the number of cards in self.stock slot, or the first
            slot in self.slots, if such slot exists. <redeals> is a game
            attribute, if it exists.

            Games can override or extend this method to better suit them.
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
        '''Return the current game score.
            Default score is the total number of cards in all slots in
            'foundations', if such attribute exists, is iterable and contain
            slots.
            Games can override or extend this method to better suit them.
        '''
        score = 0
        foundations = getattr(self, "foundations", [])
        try:
            for slot in foundations:
                if slot in self.slots:
                    score += len(slot.cards)
        except TypeError:
            pass
        return score

    def win(self):
        '''Return True if victory condition is met.
            By default victory is achieved when score equals the number
            of cards in the deck.
            Games can override or extend this method to better suit them.
        '''
        return self.score() == len(self.deck.cards)


class Klondike(Game):
    def __init__(self, grid=()):
        super(Klondike, self).__init__()

        self.grid = grid or (7, 3.2)

        self.stock = self.create_slot((0, 0), name="Stock")
        self.waste = self.create_slot((1, 0), name="Waste")

        self.foundations = []
        for i in xrange(self.grid[0] - 4, self.grid[0]):
            self.foundations.append(self.create_slot((i, 0),
                                                 name="Foundation %s" % (i-3)))

        self.tableau = []
        for i in xrange(self.grid[0]):
            self.tableau.append(self.create_slot((i, 1),
                                                 cards.ORIENTATION.DOWN,
                                                 name="Tableau %s" % (i+1)))

        self.deck.create_cards(doubledeck=False, jokers=0, faceup=False)

    def setup(self):
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

    def click(self, item):
        # Slot
        if item in self.slots:
            if item is self.stock and not self.waste.empty:
                cards = self.waste.cards[::-1]
                for c, card in enumerate(cards):
                    if c == 0:
                        card.place(self.stock)
                    else:
                        card.stack(cards[c-1])
                    card.flip()
                return True

        # Card
        elif item.is_tail and not item.faceup:
            if item.slot is self.stock:
                if self.waste.empty:
                    item.place(self.waste)
                else:
                    item.stack(self.waste.tail)
            item.flip()
            return True

    def doubleclick(self, item):
        if (item in self.slots
            or item.slot in self.foundations
            or not self.draggable(item)):
            return

        targets = []
        for slot in self.foundations:
            if slot.empty:
                targets.append(slot)
            else:
                targets.append(slot.tail)

        droplist = self.droppable(item, targets)
        if droplist:
            self.drop(item, droplist[0])
            return True

    def droppable(self, card, targets):
        targets = super(Klondike, self).droppable(card, targets)
        droplist = []
        for target in targets:

            # dropping to a slot
            if target in self.slots:
                if target in self.foundations:
                    if card.is_tail and card.rank == cards.RANK.ACE:
                        droplist.append(target)
                elif target in self.tableau:
                    if card.rank == cards.RANK.KING:
                        droplist.append(target)

            # dropping to card in foundation
            elif target.slot in self.foundations:
                if (card.is_tail
                    and target.suit == card.suit
                    and target.rank == card.rank - 1):
                    droplist.append(target)

            # dropping to card in tableau
            elif target.slot in self.tableau:
                if (target.faceup
                    and target.color != card.color
                    and target.rank == card.rank + 1):
                    droplist.append(target)

        return droplist


class Yukon(Klondike):
    def __init__(self, grid=()):
        super(Yukon, self).__init__(grid or (7, 4))
        self.slots.remove(self.stock)
        self.slots.remove(self.waste)

    def setup(self, e=4, j=1):
        '''Parametrized to be variation-friendly:
            <e>: extra cards in each column
            <j>: start column for extra cards
        '''
        super(Yukon, self).setup()
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
        super(Pylitaire, self).__init__((8, 4))

    def setup(self):
        super(Pylitaire, self).setup(2, 0)


class Backbone(Game):
    def __init__(self):
        super(Backbone, self).__init__()

        self.grid = (8, 4)
        self.redeals = 1

        self.stock = self.create_slot((5, 2), name="Stock")
        self.waste = self.create_slot((6, 2), name="Waste")

        self.foundations = []
        for i in xrange(8):
            self.foundations.append(self.create_slot((4 + i%4, i/4),
                                                 name="Foundation %s" % (i+1)))

        self.tableau = []
        for i in xrange(8):
            self.tableau.append(self.create_slot((3 * (i/4), i%4),
                                                 name="Tableau %s" % (i+1)))

        self.backbone = []
        for i in xrange(18):
            self.backbone.append(self.create_slot((1 + i/9, 0.33 * (i%9)),
                                                  name="Backbone %s" % (i+1)))

        for i, slot in enumerate(self.backbone[:-1]):
            slot.blockedby = self.backbone[i+1]

        self.block = self.create_slot((1.5, 3), name="Block")
        for i in [8, 17]:
            self.backbone[i].blockedby = self.block

        self.deck.create_cards(doubledeck=True)

    def setup(self):
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

    def doubleclick(self, item):
        if (item in self.slots
            or item.slot in self.foundations
            or not self.draggable(item)):
            return

        targets = []
        for slot in self.foundations:
            if slot.empty:
                targets.append(slot)
            else:
                targets.append(slot.tail)

        droplist = self.droppable(item, targets)
        if droplist:
            self.drop(item, droplist[0])
            return True

    def draggable(self, card):
        return not (card.slot is self.stock
                    or (card.slot in self.backbone
                        and not card.slot.blockedby.empty))
                # and not card.slot in self.foundations

    def droppable(self, card, targets):
        targets = super(Backbone, self).droppable(card, targets)
        droplist = []
        for target in targets:

            # dropping to a slot
            if target in self.slots:
                if target in self.foundations:
                    if card.is_tail and card.rank == cards.RANK.ACE:
                        droplist.append(target)
                elif target in self.tableau:
                        droplist.append(target)

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


class Test(Game):
    def __init__(self):
        super(Test, self).__init__()
        self.grid = (3, 3)
        self.deck.create_cards()
        for i in xrange(self.grid[0]):
            for j in xrange(self.grid[1] - 1):
                slot = self.create_slot((i, j))
                if j == 1:
                    slot.orientation = cards.ORIENTATION.DOWN

    def setup(self):
        self.deck.cards[0].place(self.slots[1])

        c = 1
        for card in self.deck.cards[c:]:
            card.stack(self.deck.cards[c-1])
            c += 1
        self.slots[1].fit()

    def click(self, item):
        return
