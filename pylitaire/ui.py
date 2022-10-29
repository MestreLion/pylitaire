# This file is part of Pylitaire
# Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""GUI functions and classes.

Design notes:
- Can fully use and modify the global values from g module
- Actions that dependent on a game rule use Game methods
- Purely graphical actions, like drag a card, use Deck/Card methods directly
- Resizing IS game rule dependent, as each game sets its own grid
"""

import logging
import datetime

import pygame

from . import g
from . import graphics
from . import gamerules
from . import enum

log = logging.getLogger(__name__)


class MOUSEBUTTONS(enum.Enum):
    """Pygame mouse buttons."""
    NONE          = None
    LEFT          = 1
    MIDDLE        = 2  # Wheel click button down
    RIGHT         = 3
    WHEEL_UP      = 4  # Rotating upwards
    WHEEL_DOWN    = 5  # Rotating downwards
    WHEEL_LEFT    = 6  # Wheel click sidewards
    WHEEL_RIGHT   = 7  # Wheel click sidewards
    THUMB_BACK    = 8  # Possibly bound to XF86Back key
    THUMB_FORWARD = 9  # Possibly bound to XF86Forward key


class COLORS(enum.Enum):
    RED        = (255,   0,   0)
    GREEN      = (  0, 255,   0)
    BLUE       = (  0,   0, 255)
    YELLOW     = (255, 255,   0)
    CYAN       = (  0, 255, 255)
    MAGENTA    = (255,   0, 255)
    BLACK      = (  0,   0,   0)
    WHITE      = (255, 255, 255)
    GRAY       = (127, 127, 127)


class Quit(Exception):
    pass


class Gui(object):
    def __init__(self):
        self.window = None
        self.size = ()
        self.pos = None
        self.card = None
        self.dragcard = None
        self.clickcard = None
        self.doubleclickcard = None
        self.doubleclicktimer = 0
        self.updatecursor = False
        self.cursorname = ""
        self.statustimer = 0
        self.ticks = 0
        self.gamestarttime = 0
        self.updatestatus = False
        self.win = False
        self.clear = False
        self.board = None
        self.fullboard = None

        self.games = gamerules.get_games()
        self.statusbar = StatusBar(height=g.SBHEIGHT, bgcolor=g.SBCOLOR)
        self.widgets = pygame.sprite.LayeredUpdates(self.statusbar)
        # should be LayeredDirty, but that makes cards/sb interaction glitch
        self.spritegroups = [self.widgets]

        self.game = None

    def run(self, window_size, full_screen, gamename):
        self.resize(window_size, full_screen)
        self.load_game(gamename)

        clock = pygame.time.Clock()
        while True:
            try:
                self.handle_events()
            except Quit:
                break
            self.update()
            updated = self.draw()
            pygame.display.update(updated)

            if g.profile:
                if pygame.time.get_ticks() > 10000:
                    break

            clock.tick(g.FPS * (3 if self.win else 1))

    def load_game(self, gamename):
        self.card = None
        self.dragcard = None
        self.clickcard = None
        self.doubleclickcard = None
        self.doubleclicktimer = 0

        if self.game:
            self.spritegroups.remove(self.game.deck)
            g.background.resize(self.size)  # clear slots

        self.game = gamerules.load_game(gamename)
        self.game.deck.set_theme(g.theme)

        self.spritegroups.insert(0, self.game.deck)
        self.resize_board(self.fullboard)
        self.startgame(True)

    def handle_events(self):
        """Handle all the events generated by pygame.

        Return True if game should keep running.
        """
        self.ticks = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type in [pygame.MOUSEMOTION,
                              pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP]:
                self.pos = event.pos
                self._update_card(updatestatus=False)
            self._handle_event(event, self.game)

    def _update_card(self, force_cursor_update=False, updatestatus=True):
        """Get the (possibly new) card under mouse position.

        Also, if card is different, flag to update the mouse cursor.
        By default, also flag to update the status bar message and score
        """
        if not self.game:
            return
        card = self.game.get_top_item(self.pos)
        # mouse cursor is never changed during drag, no matter what
        # current card may be None when mouse is fast and momentarily
        # moves out of dragged card
        if not self.dragcard and (force_cursor_update or card != self.card):
            self.updatecursor = True
        if updatestatus:
            self.updatestatus = True
        self.card = card

    def _handle_event(self, event, game):
        if (
            event.type == pygame.QUIT or
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            raise Quit

        if event.type == pygame.VIDEORESIZE:
            self.resize(event.size)

        if event.type == pygame.KEYDOWN:

            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                self.startgame(new=True)

            if event.key == pygame.K_SPACE:
                self.startgame(new=False)

            if event.key == pygame.K_F1:
                # noinspection GrazieInspection
                log.debug("HELP!\nHelp me if you can, I'm feeling down,\n"
                          "And I do appreciate you being 'round\n"
                          "Help me get my feet back on the ground\n"
                          "Won't you please, please help me")

            if event.key == pygame.K_F2:
                # Load the next game (in lexicographical order)
                self.load_game(gamerules.get_next(self.game))

            if event.key == pygame.K_F3:
                # Load the previous game (in lexicographical order)
                self.load_game(gamerules.get_next(self.game, reverse=True))

            if event.key == pygame.K_F11:
                self.resize(full_screen=not g.full_screen)

            if event.key == pygame.K_F12:
                self.wingame()

        if self.win or not game:
            return

        if event.type == pygame.KEYDOWN:

            if event.key in (pygame.K_BACKSPACE,):  # TODO: Add XF86Back / SDLK_AC_BACK
                self._action_undo(event, game)

            else:
                log.debug("Key down: %s key=%r, scan=%r",
                          pygame.key.name(event.key),
                          event.key,
                          event.scancode)

        if event.type == pygame.MOUSEBUTTONDOWN and self.card:
            if event.button == MOUSEBUTTONS.LEFT:
                # Time only starts when user clicks a card
                self.gamestarttime = self.gamestarttime or self.ticks

                if (
                    self.card == self.doubleclickcard
                    and self.ticks < self.doubleclicktimer
                ):
                    log.debug("Double click %s", self.card)
                    self.doubleclickcard = None
                    self.doubleclicktimer = 0
                    if game.doubleclick(self.card):
                        # if game lies, mouse cursor will not be updated
                        self._update_card()
                else:
                    if (
                        self.card not in game.slots
                        and game.draggable(self.card)
                    ):
                        log.debug("Start dragging %s", self.card)
                        self.dragcard = self.card
                        self.dragcard.start_drag(self.pos)
                        self.set_mouse_cursor('drag')
                    self.clickcard = self.doubleclickcard = self.card
                    self.doubleclicktimer = self.ticks + g.doubleclicklimit

            elif event.button == MOUSEBUTTONS.RIGHT:
                # Reserved for start peep
                pass

            else:
                log.debug("Pressed mouse button %d", event.button)

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == MOUSEBUTTONS.LEFT:

                if self.dragcard:
                    # GUI assumptions for drop candidates, hope any game is OK:
                    # - not itself (duh)
                    # - not one of its descendants (fair enough)
                    # Note that it *does* allow drop on a card that has a child
                    # It's up for the game rules to decide on that
                    candidates = pygame.sprite.Group(*self.game.deck)
                    candidates.remove(self.dragcard, *self.dragcard.children)
                    candidates.add(*self.game.slots)
                    targetcards = pygame.sprite.spritecollide(self.dragcard, candidates, False)

                    # Ask the game which candidates are valid drop targets
                    # Will also be asked on MOUSEMOVE for target highlight
                    dropcards = game.droppable(self.dragcard, targetcards)
                    if dropcards:
                        dropcard = dropcards[0]  # should choose the closest
                        log.debug("Drop %s onto %s", self.dragcard, dropcard)
                        # let the game itself drop, as GUI shall not assume card
                        # will stack, or just snap, or leave position alone
                        # GUI job is just to end the card drop and fit the slot
                        self.dragcard.drop()
                        slot = self.dragcard.slot
                        self.game.drop(self.dragcard, dropcard)
                        slot.fit()
                        self.dragcard.slot.fit()  # current slot
                    else:
                        log.debug("Abort drag %s", self.dragcard)
                        self.dragcard.abort_drag()
                    self.dragcard = None
                    self._update_card(True)

                if self.clickcard:
                    if self.card == self.clickcard:
                        log.debug("Click %s", self.card)
                        if game.click(self.card):
                            # card may be the same, cursor may be not, hence forced
                            self._update_card(True)
                            # if click changes state, cancel double click
                            # otherwise may turn & move in next mousedown
                            self.doubleclickcard = None
                            self.doubleclicktimer = 0
                    self.clickcard = None

            elif event.button == MOUSEBUTTONS.RIGHT:
                # Reserved for end peep
                pass

            elif event.button == MOUSEBUTTONS.THUMB_BACK:
                self._action_undo(event, game)

    # noinspection PyUnusedLocal
    def _action_undo(self, event, game):  # @UnusedVariable
        if game.undoable() and not self.dragcard:
            game.undo()
            self._update_card()
        else:
            log.info("Undo not available")

    def update(self):
        if not self.game:
            return

        if self.dragcard:
            self.dragcard.drag(pygame.mouse.get_pos())
            for widget in pygame.sprite.spritecollide(self.dragcard,
                                                      self.widgets,
                                                      False):
                widget.dirty = 1

        if self.gamestarttime and self.ticks > self.statustimer:
            self.updatestatus = True
            self.statustimer = self.ticks + 1000

        if self.updatestatus:
            self.updatestatus = False
            title = self.game.title()
            message = self.game.status()
            time = self.gamestarttime and (self.ticks - self.gamestarttime)
            score = self.game.score()
            if (
                time == 0
                or message != self.statusbar.message
                or score   != self.statusbar.score
                or title   != self.statusbar.title
            ):
                log.info("%s\t%s\t%s\t%s", title, message, formattime(time), score)
            self.statusbar.title = title
            self.statusbar.message = message
            self.statusbar.time = time
            self.statusbar.score = score
            self.statusbar.need_update = True

            if self.game.win():
                self.wingame()

        self.game.deck.update()
        for sprite in self.widgets:
            if sprite.need_update:
                sprite.update()

        if self.updatecursor and not self.win:
            self.updatecursor = False
            # 'drag' is handled directly
            if (
                self.card
                and self.card not in self.game.slots
                and self.game.draggable(self.card)
            ):
                self.set_mouse_cursor('draggable')
            else:
                self.set_mouse_cursor('default')

    def draw(self):
        dirty = []

        if self.clear:
            g.background.draw(self.window)
            dirty = [self.window.get_rect()]

        for group in self.spritegroups:
            dirty.extend(group.draw(self.window))

        self.clear = False
        return dirty

    def set_mouse_cursor(self, cursorname):
        if cursorname != self.cursorname:
            pygame.mouse.set_cursor(*(g.cursors[cursorname]))
            log.debug("Update cursor to %s", cursorname)
            self.cursorname = cursorname

    def resize(self, window_size=None, full_screen=None):
        """Resize all widgets according to new window <size>, triggering board resize."""
        self.window = graphics.resize(window_size, full_screen)
        self.size = self.window.get_size()

        for widget in self.widgets:
            widget.resize(self.size)

        self.widgets.clear(self.window, g.background.surface)

        self.fullboard = pygame.Rect(0, 0,
                                     self.size[0],
                                     self.size[1] - self.statusbar.height)
        self.resize_board(self.fullboard)

    def resize_board(self, fullboard):
        """Recalculate board geometry.

        Resize and reposition all board elements according to available <fullboard> space.

        Current board elements are:
        - `game.deck` and its cards, by Deck.resize(maxcardsize).
        - slot image, by its own .resize(cardsize).
        - `game.slots`, by its own .resize(cardsize).
        - Reposition of `game.slots` and its cards via .board_move().
        - As a handy hack, draw slots as background.
        """
        if not self.game:
            return

        pad = margin = g.MARGIN

        board = pygame.Rect(margin, (fullboard.w - 2 * margin[0],
                                     fullboard.h - 2 * margin[1]))

        maxcellsize = ((board.width  + pad[0]) / self.game.grid[0],
                       (board.height + pad[1]) / self.game.grid[1])

        maxcardsize = (maxcellsize[0] - pad[0],
                       maxcellsize[1] - pad[1])

        cardsize = self.game.deck.resize(maxcardsize)

        def drawgrid(r, s=None, c=COLORS.RED, w=1):
            if s:
                r = pygame.Rect(r.topleft, s)
            pygame.draw.rect(g.background.surface, c, r, w)
        if g.debug:
            drawgrid(board)
            drawgrid(board, maxcellsize)
            drawgrid(board, maxcardsize, w=3)
            drawgrid(board, cardsize, COLORS.BLUE)

        # Expand card padding horizontally up to 50% of card size
        # and vertically up to 20% of card size, limiting minimum value
        # to original padding and maximum value to maximum cell size
        pad = (max(pad[0], min(maxcellsize[0] - cardsize[0], cardsize[0] / 2)),
               max(pad[1], min(maxcellsize[1] - cardsize[1], cardsize[1] / 5)))

        # Shrink cell size in terms of actual card size + padding
        cellsize = (cardsize[0] + pad[0],
                    cardsize[1] + pad[1])

        # Trim the play area based on new cell size
        board.size = ((cellsize[0] * self.game.grid[0]) - pad[0],
                      (cellsize[1] * self.game.grid[1]) - pad[1])

        # And center it horizontally
        board.centerx = fullboard.centerx

        if g.debug:
            drawgrid(board, None, COLORS.YELLOW)
            drawgrid(board, cellsize, COLORS.YELLOW)

        self.board = board
        log.debug("Board resized to %r, cell size %r and card size %r",
                  self.board, cellsize, cardsize)

        g.slot.resize(cardsize)
        geometry = pygame.Rect(self.board.topleft, cellsize)
        for slot in self.game.slots:
            slot.resize(cardsize)
            slot.boardmove(geometry)
            slot.fit(board)
            slot.draw(g.background.surface, g.slot.surface)

        if self.win:
            self.game.deck.board = fullboard
            self.game.deck.clear(self.window, self.window)
        else:
            self.game.deck.clear(self.window, g.background.surface)

        self.clear = True

    def startgame(self, new=True):
        if not self.game:
            return
        self.set_mouse_cursor('default')
        self.gamestarttime = 0
        if self.win:
            self.win = False
            self.game.deck.stop_animation()
            self.game.deck.clear(self.window, g.background.surface)
            self.clear = True
        self.updatestatus = True
        if new:
            self.game.new_game()
        else:
            self.game.restart()

    def wingame(self):
        log.info("YOU WIN! In %s, congratulations!",
                 formattime(self.ticks - self.gamestarttime))
        self.win = True
        self.dragcard = None
        self.gamestarttime = 0
        self.set_mouse_cursor('default')
        self.game.deck.clear(self.window, self.window)
        self.game.deck.start_animation(self.fullboard)


class StatusBar(pygame.sprite.DirtySprite):
    def __init__(self, **params):
        self.height     = params.pop('height', 25)
        self.color      = params.pop('color', COLORS.BLACK)
        self.bgcolor    = params.pop('bgcolor', COLORS.GRAY)
        self.padding    = params.pop('padding', (10, 2))
        font            = params.pop('font', None)
        font_name       = params.pop('font_name',  None)
        font_size       = params.pop('font_size',  24)
        width, height   = params.pop('windowsize', (0, 0))
        super(StatusBar, self).__init__()

        self.font = font or pygame.font.Font(font_name, font_size)

        # dummy until resize()
        self.rect = pygame.Rect(0, 0, 0, 0)
        if width and height:
            self.resize((width, height))

        # All dummy until update()
        self.image  = pygame.Surface((0, 0))
        self.llabel = pygame.Surface((0, 0))
        self.mlabel = pygame.Surface((0, 0))
        self.rlabel = pygame.Surface((0, 0))

        self.title = ""
        self.message = ""
        self.time = 0
        self.score = 0

        self.need_update = True
        self.dirty = 1

    def update(self):
        """Rebuild all data needed by draw()"""
        self.need_update = False

        self.image = pygame.Surface(self.rect.size)
        self.image.fill(self.bgcolor)

        ltext = self.message
        mtext = self.title
        rtext = "Time: %s    Score: %3d" % (
            formattime(self.time),
            self.score)

        def renderfont(text):
            return self.font.render(text, True, self.color, self.bgcolor)

        llabel = renderfont(ltext)
        mlabel = renderfont(mtext)
        rlabel = renderfont(rtext)

        lrect = llabel.get_rect()
        lrect.bottomleft = (self.padding[0],
                            self.rect.height - self.padding[1])

        mrect = mlabel.get_rect()
        mrect.midbottom = (self.rect.width / 2,
                           self.rect.height - self.padding[1])

        rrect = rlabel.get_rect()
        rrect.bottomright = (self.rect.width  - self.padding[0],
                             self.rect.height - self.padding[1])

        self.image.blit(llabel, lrect)
        self.image.blit(mlabel, mrect)
        self.image.blit(rlabel, rrect)

        self.dirty = 1

    def resize(self, windowsize):
        """Recalculate self.rect, return self.height"""
        width, height = windowsize
        self.rect.topleft = (0, height - self.height)
        self.rect.size = (width, self.height)

        self.update()
        return self.height


def formattime(ms):
    return datetime.timedelta(seconds=int(ms/1000))
