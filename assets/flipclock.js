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
        path: '/assets/images/',
        digits: 2,
        width: 10,
        delay: 50
    };

    var methods = {
        init: function(options) {
            if (options) {
                $.extend(settings, options);
            }

            obj = this;
            for (var state = 0; state < 10; state += 0.5) {
                var path = stateToPath(state);
                preloadImages(path);
            }
            for (var digit = 0; digit < settings.digits; digit++) {
                currentState.push(0);
            }

            drawClock();
            return this;
        },

        setClock: function(num) {
            var max = Math.pow(10, settings.digits) - 1;
            if (num > max) {
                var error = '$.flipclock.setClock(' + num + ');, ';
                error += 'but max value is ' + max;
                $.error(error);
                num = max;
            }

            currentNum = num;
            flipClock();
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
            $.error("$.flipClock." + method + "() method doesn't exist");
        }
    };


    var obj = undefined;
    var imageCache = [];
    var currentState = [];
    var currentNum = 0;

    function stateToPath(state) {
        var transition = state != Math.floor(state);
        state = Math.floor(state);
        var file = String(state);
        if (transition) {
            nextState = (state + 1) % 10;
            file += '-' + nextState;
        }
        file += '.png';
        var path = settings.path + file;
        return path;
    }

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

    function drawClock() {
        var html = '';
        for (var index = 0; index < currentState.length; index++) {
            var state = currentState[index];
            var path = stateToPath(state);
            var width = settings.width;
            var imageTag = '<img src="' + path + '" width="' + width + '%" />';
            html = imageTag + html;
        }
        obj.html(html);
    }

    function flipClock() {
        for (var exponent = 0; exponent < settings.digits; exponent++) {
            var digit = currentNum % Math.pow(10, exponent + 1);
            digit = Math.floor(digit / Math.pow(10, exponent));
            while (currentState[exponent] != digit) {
                currentState[exponent] = (currentState[exponent] + 0.5) % 10;
                drawClock();
                var timeoutId = window.setTimeout(flipClock, settings.delay);
                return;
            }
        }
    }

})(jQuery);
