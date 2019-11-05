Pylitaire
=========

A Solitaire card game made in Python using Pygame

Rules are of [Yukon](http://en.wikipedia.org/wiki/Yukon_%28solitaire%29), which is very similar to the traditional Solitaire (also known as [Klondike](http://en.wikipedia.org/wiki/Klondike_solitaire)), but more challenging and (hopefully) more fun.

Humm, so I guess this project should be named *Pyukon* instead. Maybe I will :)

Uses themes and background in the same format as [Gnome Aisleriot](https://wiki.gnome.org/action/show/Apps/Aisleriot) for a well-polished presentation, and it's easily customizable.

---

Requirements
------------

- [Python](https://www.python.org) (tested in 3.6 and 2.7)
- [Pygame](https://www.pygame.org), the main game engine
- [Pillow](https://pillow.readthedocs.org), the modern fork of the Python Imaging Library
- [libRSVG](https://wiki.gnome.org/Projects/LibRsvg), for SVG/SVGZ image format support
- [Pycairo](https://cairographics.org/pycairo), python and GIO bindings for Cairo, to bridge libRSVG to Pygame.

The above can be installed in Debian-like distros (like Ubuntu/Mint) with:

	sudo apt-get install python3 python3-{pygame,gi-cairo,pil} gir1.2-rsvg-2.0

For Python 2:

	sudo apt-get install python python-{pygame,gi-cairo,pil} gir1.2-rsvg-2.0


Install and usage
-----------------

Clone the repository, install the dependencies, and run `python3 -m pylitaire` or `python2 -m pylitaire`

An install script, along with a proper `.desktop` file will be available soon. Icons are already available in `data/icons`

---

Contributing
------------

Patches are welcome! Fork, hack, request pull! See the `TODO` file for a "roadmap" of priorities and most-wanted features.

If you find a bug or have any enhancement request, please to open a [new issue](https://github.com/MestreLion/pylitaire/issues/new)


Written by
----------

Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>


Licenses and Copyright
----------------------

Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>.

License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.

This is free software: you are free to change and redistribute it.

There is NO WARRANTY, to the extent permitted by law.
