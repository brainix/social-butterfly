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


(function($) {

    var settings = {
        urlPathToImages: '/assets/images/',
        numDigits: 2
    };

    var methods = {
        init: function(options) {
            if (options) {
                $.extend(settings, options);
            }

            for (var digit = 0; digit <= 9; digit++) {
                var nextDigit = (digit + 1) % 10;
                var file = digit + '.png';
                var nextFile = digit + '-' + nextDigit + '.png';
                var path = settings.urlPathToImages + file;
                var nextPath = settings.urlPathToImages + nextFile;
                preloadImages(path, nextPath);
            }

            return this;
        }
    };

    $.fn.flipClock = function(method) {
        if (methods[method]) {
            method = methods[method];
            var args = Array.prototype.slice.call(arguments, 1);
            var retVal = method.apply(this, args);
            return retVal;
        } else if (typeof method === 'object' || !method) {
            method = methods.init;
            var retVal = method.apply(this, arguments);
            return retVal;
        } else {
            $.error('$.flipClock has no method named ' + method);
        }
    };


    var imageCache = [];

    function preloadImages() {
        // Given URLs to images, preload those images.
        if (document.images) {
            for (var index = arguments.length; index--;) {
                var cachedImage = document.createElement("img");
                cachedImage.src = arguments[index];
                imageCache.push(cachedImage);
            }
        }
    }

})(jQuery);
