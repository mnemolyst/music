define(function() {
    var Scene2D = function(canvas) {
        this.context = canvas.getContext('2d');
        this.sceneWidth = canvas.width;
        this.sceneHeight = canvas.height;
        this.halfWidth = this.sceneWidth * 0.5;
        this.halfHeight = this.sceneHeight * 0.5;

        this.render = function() {
            this.context.save();
            this.context.fillStyle = '#ffffff';
            this.context.fillRect(0, 0, this.sceneWidth, this.sceneHeight);
            this.context.restore();
        }

        this.tic = function() {
            this.render();
        }
    }

    function setup($) {
        var canvas = $('#canvas');
        var offset = canvas.offset();
        var scene = new Scene2D(canvas[0]);
        var state = 'none';

        //setInterval(function () {
        //    scene.tic();
        //    frames++;
        //}, renderInterval);

        $(document).keydown(function(event) {
            if (state == 'alert_next_key') {
                state = 'none';
                alert(event.which);
            }

            // KEYS
            switch(event.which) {
                case 8:                                       //backspace
                break;
                case 9:                                       //tab
                break;
                case 13:                                      //enter
                break;
                case 27:                                      //esc
                break;
                case 37:                                      //left arrow
                    if (event.shiftKey) {
                    } else {
                        scene.panX -= 5;
                    }
                break;
                case 38:                                      //up arrow
                    scene.panY -= 5;
                break;
                case 39:                                      //right arrow
                    if (event.shiftKey) {
                    } else {
                        scene.panX += 5;
                    }
                break;
                case 40:                                      //down arrow
                    scene.panY += 5;
                break;
                case 46:                                      //delete
                break;
                case 48: case 49: case 50:                    //'0'-'2'
                break;
                case 51: case 52: case 53: case 54: case 55: case 56: case 57: //'3'-'9'
                    addPoly(event.which - 48);
                break;
                case 61:                                      //'=' / '+'
                break;
                case 65:                                      //'a'
                    addRhombA();
                break;
                case 66:                                      //'b'
                    addRhombB();
                break;
                case 67:                                      //'c'
                break;
                case 68:                                      //'d'
                    addDart(); //TODO
                break;
                case 69:                                      //'e'
                break;
                case 70:                                      //'f'
                    addPoly(Math.floor(Math.random()*6+3));
                break;
                case 71:                                      //'g'
                    gravity = !gravity;
                break;
                case 72:                                      //'h'
                    hoist = !hoist;
                break;
                case 73:                                      //'i'
                    scene.scale *= 1.1;
                break;
                case 76:                                      //'l'
                break;
                case 78:                                      //'n'
                    drawText = !drawText;
                break;
                case 79:                                      //'o'
                    scene.scale /= 1.1;
                break;
                case 80:                                      //'p'
                    pause = !pause;
                break;
                case 82:                                      //'r'
                break;
                case 83:                                      //'s'
                break;
                case 85:                                      //'u'
                    scene.zTranslate -= 0.2;
                break;
                case 86:                                      //'v'
                break;
                case 87:                                      //'w'
                break;
                case 89:                                      //'y'
                break;
                case 90:                                      //'z'
                break;
                case 173:                                     //'-'
                break;
                case 190:                                     //'.'
                break;
                case 191:                                     //'/'
                break;
                case 192:                                     //'`'
                    if (event.shiftKey)
                    state = 'alert_next_key';
                break;
                case 220:                                     //'\'
                break;
            }
        });

        $('#canvas').mousedown(function(event) {
        });

        $('#canvas').mousemove(function(event) {
        });

        $('#canvas').mouseup(function(event) {
        });

        alert('hi');
    }

    return {
        setup: setup,
    }
});
