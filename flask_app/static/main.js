requirejs.config({
    baseUrl: 'static/lib',
    paths: {
        jquery: 'jquery-2.2.0.min',
        jqueryui: 'jquery-ui-1.11.4.custom/jquery-ui.min',
        paper: 'paper-core',
    }
});

requirejs(['music']);
