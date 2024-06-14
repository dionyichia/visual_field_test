webcam eye tracker
==================
To run eye tracking software, run the GUIttest.py file

version 1 
This version has a zoomed in image. 

Instructions to run:
1. Press any key to run program
2. Align either eye to the center of the green box, ensure eye is within box
3. Once eye is in place, press space
4. Wait for calibration, once the box around the pupil is of constant size, press space
4.1 To recalibrate, recenter eye and press "C"
5. Ignore confirmation stage for now, press space
5.1 To lock position of eye, press "L" (useless for now, plan to use this so that if eye moves the test will pause)
6. Visual Field test will commence with eye tracker running in background 

version 2
This version contains the orignal code plus a few edits. This has a normal full face view.
Ignore this version, might have accidentally changed something, doesnt rly work. 

version 0.1.2 (12-Oct-2013)


Software developed by Edwin Dalmaijer. For more information on the inner
workings of the pupil tracker, please read [this page](http://www.pygaze.org/2015/06/webcam-eye-tracker/). This module
is built on top of PyGame, and is part of the PyGaze project. Please note
that maintenance is slow, as this is a hobby and work often gets in the
way of those ;)

Webcam eyetracker is open source software and therefore free to use and modify at will.
Warranty, however, is NOT given. If this software fails, causes your computer
to blow up, your spouse to leave you, your toilet to clog and/or the entire
supply of nuclear missles on earth to launch, or anything else that you might
want to blame on us, the author(s) CANNOT IN ANY WAY be held responsible.

Webcam eyetracker was released under the GNU Public License (version 3), of which you
should have received a copy of together with the software:

    Webcam eyetracker is Python software to locate a pupil (or another
    dark patch) in an image, and to follow it. A GUI is provided to
    calibrate the setup.
    Copyright (C) 2014 Edwin S. Dalmaijer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>

