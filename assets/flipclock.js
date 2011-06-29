/*---------------------------------------------------------------------------*\
 |  flipclock.js                                                             |
 |                                                                           |
 |  Copyright (c) 2010-2011, Code A La Mode, original authors.               |
 |                                                                           |
 |      This file is part of Social Butterfly.                               |
 |                                                                           |
 |      Social Butterfly is free software; you can redistribute it and/or    |
 |      modify it under the terms of the GNU General Public License as       |
 |      published by the Free Software Foundation, either version 3 of the   |
 |      License, or (at your option) any later version.                      |
 |                                                                           |
 |      Social Butterfly is distributed in the hope that it will be useful,  |
 |      but WITHOUT ANY WARRANTY; without even the implied warranty of       |
 |      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        |
 |      GNU General Public License for more details.                         |
 |                                                                           |
 |      You should have received a copy of the GNU General Public License    |
 |      along with Social Butterfly.  If not, see:                           |
 |          <http://www.gnu.org/licenses/>.                                  |
\*---------------------------------------------------------------------------*/


/*---------------------------------------------------------------------------*\
 |                              initFlipClock()                              |
\*---------------------------------------------------------------------------*/

function initFlipClock() {
    preloadImages(
        '/assets/images/0.png', '/assets/images/0-1.png',
        '/assets/images/1.png', '/assets/images/1-2.png',
        '/assets/images/2.png', '/assets/images/2-3.png',
        '/assets/images/3.png', '/assets/images/3-4.png',
        '/assets/images/4.png', '/assets/images/4-5.png',
        '/assets/images/5.png', '/assets/images/5-6.png',
        '/assets/images/6.png', '/assets/images/6-7.png',
        '/assets/images/7.png', '/assets/images/7-8.png',
        '/assets/images/8.png', '/assets/images/8-9.png',
        '/assets/images/9.png', '/assets/images/9-0.png'
    );
}


/*---------------------------------------------------------------------------*\
 |                              preloadImages()                              |
\*---------------------------------------------------------------------------*/

var imageCache = [];

function preloadImages() {
    // Given arguments corresponding to URLs to images, preload those images.
    if (document.images) {
        for (var index = arguments.length; index--;) {
            var cachedImage = document.createElement("img");
            cachedImage.src = arguments[index];
            imageCache.push(cachedImage);
        }
    }
}
