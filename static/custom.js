// Clean URL - remove Query Strings
var clean_uri = location.protocol + "//" + location.host + location.pathname;
window.history.replaceState({}, document.title, clean_uri);

$(document).ready(function () {
    $(function () {
        FastClick.attach(document.body);
    });
});
