# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""Game rules and logic.

Design notes:
- Game rules should not depend on any other module than cards
- Talks to Deck/Card only via API, but should not rely on its implementation internals
- Talks to GUI only via high-level events such as `click(card)`, `drop(card)`, etc
"""

import logging
import random

from . import cards

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
        args = map(str, self.args)
        args.extend(("%s=%s" % (k, v) for k, v in self.kwargs.items()))
        return "<%s.%s(%s)>" % (
            getattr(self.command, '__self__', ''),
            self.command.__name__,
            ", ".join(args))


class Game(object):
    """Base class for all game rules."""
    def __init__(self):
        """Each of these attributes are required to exist in subclasses:

        <grid>
            The (cx, cy) size of the board, in card units. Default is (0, 0).
            Games should redefine this to its own size.

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

        Boilerplate for a simple game:

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
        """
        self.grid = (0, 0)
        self.slots = []
        self.deck = cards.Deck()
        self.name = self.__class__.__name__
        self.undocmds = []
        self.seed = 0

    ###########################################################################
    # API methods already implemented, subclasses should leave alone

    def new_game(self, seed=0):
        """Handle a New Game event. Simply shuffle cards and call restart()."""
        if not seed:
            seed = random.randrange(2**32)
        self.seed = seed
        log.info("New game #%d", self.seed)
        self.deck.shuffle(self.seed)
        self.restart(nolog=True)
        return self.seed

    def restart(self, nolog=False):
        """Handle a Restart Game event. Break all stacks and run setup()."""
        if not nolog:
            log.info("Restart game")
        self.undocmds = []
        self.deck.pop_cards()
        self.setup()

    def get_top_item(self, pos):
        """Top item at <pos>, either card or slot, if any. Called by GUI engine."""
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

    def title(self):
        """Game Title for Statusbar."""
        return "%s #%s" % (self.name, self.seed)


    ###########################################################################
    # API methods subclasses must implement

    def setup(self):
        """Set up the board, called on new game and restart.

        Games should override this method, which by default do nothing.
        """
        pass

    def click(self, item):
        """Handle click on <element>, either card or slot.

        Games should override or extend this method.
        By default flip() cards and do nothing on slots.

        Return True if card state changed.
        """
        if item not in self.slots:
            item.flip()
            self.add_undo(item.flip)
            return True

    def doubleclick(self, item):
        """Handle double click on <widget>, either card or slot.

        Games should override this method, which by default do nothing.
        """
        pass

    def drop(self, card, target):
        """Handle drop <card> on a <target>, target may be a card or a slot.

        By default stack() or place() on target, depending on target type.

        This is only triggered by GUI for a valid drop target, as defined by droppable(),
        so the default action should suit any game. Extend this only if game needs
        additional actions when dropping cards.
        """
        slot = card.slot  # assuming cards are always in a slot

        if target in self.slots:
            card.place(target)
        else:
            card.stack(target)

        self.add_undo(slot.stack, card)

    def draggable(self, card):
        """Can <card> can be dragged?

        Just a helper for the GUI engine to choose which mouse cursor to use on hovering
        The actual card drag is performed later by the engine.

        Games should override this method, which by default return True for any card that
        is faced up.
        """
        return card.faceup

    def droppable(self, card, targets):
        """Return a subset of <targets> that are valid drop places for <card>.

        By default return all targets that are either empty slots or cards that are
        the tail of its stack.

        Games should override or extend this method to further filter target list
        according to game rules, as default behavior is very permissive and only meant
        as an initial, "no-brainer" filter.
        """
        droplist = []
        for target in targets:

            # dropping to a slot
            if target in self.slots:
                if target.is_empty:
                    droplist.append(target)

            # dropping to card
            else:
                if target.is_tail:
                    droplist.append(target)

        return droplist

    def status(self):
        """Status message string that will be displayed for the game by GUI at intervals.

        Default message is:
                "Stock left: <stock>  Redeals left: <redeals>"

        <stock> is the number of cards in self.stock slot, or the first slot in self.slots,
        if such slot exists.
        <redeals> is a game attribute, if it exists.

        Games can override or extend this method to better suit them.
        """
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
        """Return the current game score.

        Default score is the total number of cards in all slots in 'foundations',
        if such attribute exists, is iterable and contain slots.

        Games can override or extend this method to better suit them.
        """
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
        """Has the victory condition been met?

        By default victory is achieved when score equals the number of cards in the deck.

        Games can override or extend this method to better suit them.
        """
        return self.score() == len(self.deck.cards)

    #########################################
    # Utility methods that subclasses can use

    def create_slot(self, *slotargs, **slotkwargs):
        """Create a game slot. See cards.Slot class for arguments.

        A convenience wrapper to be used by subclasses that automatically keeps track of
        all slots created by adding them to self.slots list.
        """
        slot = cards.Slot(*slotargs, **slotkwargs)
        self.slots.append(slot)
        return slot

    def add_undo(self, command, *args, **kwargs):
        """Add a command to the undo list."""
        self.undocmds.append(Command(command, *args, **kwargs))

    def click_stock_waste(self, stock, waste, redeals=None, maxredeals=-1):
        """Handle click on stock, waste, and their cards."""
        pass

    def double_click_to_foundations(self, item, foundations):
        """Handle double-click on <item>.

        Stack it to a suitable foundation slot if card is draggable() from its location
        and droppable() to any foundation slot.
        """
        if (item in self.slots
            or item.slot in foundations
            or not self.draggable(item)):
            return

        targets = []
        for slot in foundations:
            if slot.is_empty:
                targets.append(slot)
            else:
                targets.append(slot.tail)

        droplist = self.droppable(item, targets)
        if droplist:
            self.drop(item, droplist[0])
            return True


class Klondike(Game):
    def __init__(self, grid=()):
        super(Klondike, self).__init__()

        self.grid = grid or (7, 3.2)

        self.stock = self.create_slot((0, 0), name="Stock")
        self.waste = self.create_slot((1, 0), name="Waste")

        self.foundations = []
        for i in range(self.grid[0] - 4, self.grid[0]):
            self.foundations.append(self.create_slot((i, 0),
                                                 name="Foundation %s" % (i-3)))

        self.tableau = []
        for i in range(self.grid[0]):
            self.tableau.append(self.create_slot((i, 1),
                                                 cards.ORIENTATION.DOWN,
                                                 name="Tableau %s" % (i+1)))

        self.deck.create_cards(doubledeck=False, jokers=0, faceup=False)

    def setup(self):
        super(Klondike, self).setup()

        for card in self.deck.cards:
            self.stock.stack(card)
            card.flip(cards.TURN.FACEDOWN)

        for i, __ in enumerate(self.tableau):
            self.stock.deal(self.tableau[i],      cards.TURN.FACEUP)
            self.stock.deal(self.tableau[i + 1:], cards.TURN.FACEDOWN)

    def click(self, item):
        undo = []
        # Slot
        if item in self.slots:
            if item is self.stock:
                while not self.waste.is_empty:
                    self.waste.deal(self.stock, cards.TURN.FACEDOWN)
                    undo.append(Command(self.stock.deal, self.waste,
                                        cards.TURN.FACEUP))
                self.undocmds.append(undo)
                return True

        # Card
        elif item.is_tail and not item.faceup:
            if item.slot is self.stock:
                self.stock.deal(self.waste)
                undo.append(Command(self.waste.deal, self.stock))

            item.flip()
            undo.append(Command(item.flip))
            self.undocmds.append(undo)
            return True

    def doubleclick(self, item):
        return self.double_click_to_foundations(item, self.foundations)

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

    def status(self):
        return "Cards to uncover: %d" % sum(1 if not c.faceup else 0
                                            for c in self.deck)


class Win(Klondike):
    def __init__(self, grid=()):
        super(Win, self).__init__(grid or (7, 4))
        self.slots.remove(self.stock)
        self.slots.remove(self.waste)

    def setup(self):
        super(Win, self).setup()
        for slot in self.tableau + [self.stock]:
            while not slot.is_empty:
                slot.deal(self.foundations[0], cards.TURN.FACEUP)


class Yukon(Klondike):
    def __init__(self, grid=()):
        super(Yukon, self).__init__(grid or (7, 4))
        self.slots.remove(self.stock)
        self.slots.remove(self.waste)

    def setup(self, i=1):
        """Parameterized to be variation-friendly.

        <i>: tableau column to start dealing extra cards
        """
        super(Yukon, self).setup()
        while not self.stock.is_empty:
            self.stock.deal(self.tableau[i:], cards.TURN.FACEUP)


class Pylitaire(Yukon):
    """Yukon easier variation.

    Allow any card to be dropped on an empty tableau slot, not only Kings
    """
    def __init__(self):
        super(Pylitaire, self).__init__()  # (8, 4)

    def setup(self):
        super(Pylitaire, self).setup()

    def droppable(self, card, targets):
        droplist = super(Pylitaire, self).droppable(card, targets)

        droplist.extend(__ for __ in targets if
                        __ not in droplist and
                        __ in self.tableau and
                        __.is_empty)

        return droplist


class Backbone(Game):
    def __init__(self):
        super(Backbone, self).__init__()

        self.grid = (8, 4)
        self.redeals = 1

        self.stock = self.create_slot((5, 2), name="Stock")
        self.waste = self.create_slot((6, 2), name="Waste")

        self.foundations = []
        for i in range(8):
            self.foundations.append(self.create_slot((4 + i%4, i//4),
                                                 name="Foundation %s" % (i+1)))

        self.tableau = []
        for i in range(8):
            self.tableau.append(self.create_slot((3 * (i//4), i%4),
                                                 name="Tableau %s" % (i+1)))

        self.backbone = []
        for i in range(18):
            self.backbone.append(self.create_slot((1 + i//9, 1.0/3 * (i%9)),
                                                  name="Backbone %s" % (i+1)))

        for i, slot in enumerate(self.backbone[:-1]):
            slot.blockedby = self.backbone[i+1]

        self.block = self.create_slot((1.5, 3), name="Block")
        for i in [8, 17]:
            self.backbone[i].blockedby = self.block

        self.deck.create_cards(doubledeck=True)

    def setup(self):
        for card in self.deck.cards:
            self.stock.stack(card)
            card.flip(cards.TURN.FACEDOWN)

        self.stock.deal(self.tableau + self.backbone + [self.block],
                        cards.TURN.FACEUP)

        self.redeals = 1

    def click(self, item):
        undo = []

        if item in self.slots:
            if item is self.stock and self.redeals > 0:
                while not self.waste.is_empty:
                    self.waste.deal(self.stock, cards.TURN.FACEDOWN)
                    undo.append(Command(self.stock.deal, self.waste,
                                        cards.TURN.FACEUP))
                self.redeals -= 1
                def undo_redeals(self):
                    self.redeals += 1
                undo.append(Command(undo_redeals, self))

        elif item.slot is self.stock:
            self.stock.deal(self.waste, cards.TURN.FACEUP)
            self.add_undo(self.waste.deal, self.stock, cards.TURN.FACEDOWN)
            return True

    def doubleclick(self, item):
        return self.double_click_to_foundations(item, self.foundations)

    def draggable(self, card):
        return not (card.slot is self.stock
                    or card.slot in self.foundations
                    or (card.slot in self.backbone
                        and not card.slot.blockedby.is_empty))

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
                    if ((card.slot not in self.backbone + [self.block])
                         or card.rank == cards.RANK.KING
                    ):
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
        for i in range(self.grid[0]):
            for j in range(self.grid[1] - 1):
                slot = self.create_slot((i, j))
                if j == 1:
                    slot.orientation = cards.ORIENTATION.DOWN

    def setup(self):
        slot = self.slots[1]
        for card in self.deck.cards:
            slot.stack(card)
            card.flip(cards.TURN.FACEUP)
        slot.fit()

    def click(self, item):
        return

    def win(self):
        return not self.slots[-1].is_empty
