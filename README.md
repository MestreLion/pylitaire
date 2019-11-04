Pylitaire
=========

A Solitaire card game made in Python using Pygame

Rules are of [Yukon](http://en.wikipedia.org/wiki/Yukon_%28solitaire%29), which is very similar to the traditional Solitaire (also known as [Klondike](http://en.wikipedia.org/wiki/Klondike_solitaire)), but more challenging and (hopefully) more fun.

Humm, so I guess this project should be named *Pyukon* instead. Maybe I will :)

Uses themes and background in the same format as [Gnome Aisleriot](https://wiki.gnome.org/action/show/Apps/Aisleriot) for a well-polished presentation, and it's easily customizable.

---

Requirements
------------

- [Python 2](http://www.python.org) (tested in 2.7.15+)
- [Pygame](http://www.pygame.org), the main game engine
- [Pillow](http://pillow.readthedocs.org), the modern fork of the Python Imaging Library
- [libRSVG](https://wiki.gnome.org/action/show/Projects/LibRsvg), for SVG/SVGZ image format support
- [Pycairo](http://cairographics.org/pycairo), python and GIO bindings for Cairo, to interface libRSVG and Pygame.

The above can be installed in Debian-like distros (like Ubuntu/Mint) with:

	sudo apt-get install python python-{pygame,gi-cairo,pil} gir1.2-rsvg-2.0

*Note on Python 3 support: On the way! While the game itself is easily ported to Python 3, the dependencies are not. Original PIL is dead, Pillow must be used; Pygame, Pycairo and Pillow were only recently ported to Python 3, which _might_ require code adjustments. Bottomline: Python 2 it is... for now. :)*


Install and usage
-----------------

Clone the repository, install the dependencies, and run the executable `pylitaire`

An install script, along with a proper `.desktop` file will be available soon. Icons are already available in `data/icons`

---

Contributing
------------

Patches are welcome! Fork, hack, request pull! See the `TODO` file for a "roadmap" of priorities and most-wanted features.

If you find a bug or have any enhacement request, please to open a [new issue](https://github.com/MestreLion/pylitaire/issues/new)


Written by
----------

Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>


Licenses and Copyright
----------------------

Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>.

License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.

This is free software: you are free to change and redistribute it.

There is NO WARRANTY, to the extent permitted by law.
