requirejs.config({
    baseUrl: 'javascripts/lib',
    paths: {
        app: '../app',
        jquery: 'jquery-2.2.0.min',
    }
});
define(['music', 'jquery'], function(music, jquery) {
    jquery(document).ready(function($) {
        music.setup($);
    });
});
