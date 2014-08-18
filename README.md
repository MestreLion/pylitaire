Pylitaire
=========

A Solitaire card game made in Python using Pygame

Rules are of [Yukon](http://en.wikipedia.org/wiki/Yukon_%28solitaire%29), which is very similar to the traditional Solitaire (also known as [Klondike](http://en.wikipedia.org/wiki/Klondike_solitaire)), but more challenging and (hopefully) more fun.

Humm, so I guess this project should be named *Pyukon* instead. Maybe I will :)

Uses themes and background in the same format as [Gnome Aisleriot](https://wiki.gnome.org/action/show/Apps/Aisleriot) for a well-polished presentation, and it's easily customizable.

---

Requirements
------------

- [Python 2](http://www.python.org) (tested in 2.7.4)
- [Pygame](http://www.pygame.org), the main game engine
- [Pycairo](http://cairographics.org/pycairo), python bindings for Cairo
- [pyrsvg](http://cairographics.org/pyrsvg/), a python wrapper for `libsrvg`
- [PIL](http://www.pythonware.com/products/pil/)/[Pillow](http://pillow.readthedocs.org), the Python Imaging Library or its modern fork

The above can be installed in Debian-like distros (like Ubuntu/Mint) with:

	sudo apt-get install python python-{pygame,cairo,rsvg,imaging}

*Note on Python 3 support: while the game itself easily ported to Python 3, the dependencies are not. The recent Pygame port to Python 3 is still buggy and not yet packaged in many distros, including Ubuntu. Also both Pycairo and pyrsvg are not available to Python 3, only their `gir` bindings. PIL does not support Python 3 at all. Pillow does, but it was not backported to older releases like Ubuntu 12.04. Bottomline: Python 2 it is :)*


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

Rodigo Silva (MestreLion) <linux@rodrigosilva.com>


Licenses and Copyright
----------------------

Copyright (C) 2014 Rodigo Silva (MestreLion) <linux@rodrigosilva.com>.

License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.

This is free software: you are free to change and redistribute it.

There is NO WARRANTY, to the extent permitted by law.
