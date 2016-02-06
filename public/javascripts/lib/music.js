define(['jquery', 'paper'], function($, paperJs) {
    paperJs.paper.install(this);

    var upperLeft = new Point(100, 100);
    var timeSpacing = 20;
    var freqSpacing = 20;
    var paths = [];
    var cursor = {
        t: 0,
        fq: 440,
        vPath: null,
        hPath: null,
        update: function() {
            this.vPath.position.x = upperLeft.x + 5 + timeSpacing * t;
            this.hPath.position.x = upperLeft.x + 5 + timeSpacing * t;
            this.hPath.position.y = upperLeft.y + freqSpacing * (fq//todo log freq spacing
    };

    function init() {
        view.viewSize = [window.innerWidth, window.innerHeight];

        for (var i = 0; i < 24; i++) { // two octaves
            var path = new Path({
                strokeColor: 'black',
            });
            var p = upperLeft.add([0, freqSpacing * i]);
            path.add(p);
            p.x = view.viewSize.width - 100;
            path.add(p);
            paths.push(path);
        }

        cursor.hPath = new Path({
            strokeColor: 'red',
        });
        cursor.hPath.add(upperLeft.add([5, -5]));
        cursor.hPath.add(paths[paths.length - 1].firstSegment.point.add([5, 5]));

        cursor.vPath = new Path({
            strokeColor: 'red',
        });
        cursor.vPath.add(upperLeft.add([0, freqSpacing * 0.5]));
        cursor.vPath.add(upperLeft.add([10, freqSpacing * 0.5]));
    }

    //var path = new Path({
    //    strokeColor: 'black',
    //});
    //var start = new Point(100, 100);
    //path.moveTo(start);
    //path.lineTo(start.add([view.viewSize.width - 100, 0]));

    $(document).ready(function() {
        var canvas = document.getElementById('canvas');
        var $canvas = $(canvas);
        paper.setup(canvas);

        view.onFrame = function(event) {
        }

        var tool = new Tool();
        tool.onKeyDown = function(event) {
            switch (event.key) {
                case 'h':
                    cursor.t -= 1;
                    cursor.hPath.position.x -= timeSpacing;
                    break;
                case 'l':
                    cursor.t += 1;
                    cursor.hPath.position.x += timeSpacing;
                    break;
            }
        };

        window.onresize = function() {
            view.viewSize = [window.innerWidth, window.innerHeight];
            for (var i = 0; i < paths.length; i++) {
                if (paths[i].segments.length > 0) {
                    paths[i].removeSegments(1);
                }
                var p1 = paths[i].firstSegment.point;
                var p2 = p1.clone();
                p2.x = view.viewSize.width - 100;
                paths[i].add(p2);
            }
            view.fire('resize', view);
        }

        init();
    });

    return { };
});
