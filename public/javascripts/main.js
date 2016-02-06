requirejs.config({
    baseUrl: 'javascripts/lib',
    paths: {
        app: '../app',
        jquery: 'jquery-2.2.0.min',
        paper: 'paper-full.min',
    }
});

requirejs(['music']);
