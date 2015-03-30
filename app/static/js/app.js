$(document).ready(function () {

    addAlert("<center><h1>Software Engineer</h1></center>");

    window.setTimeout(function () {
	addAlert("<center><h1>Urbana, Illinois & San Francisco Bay Area</h1></center>");
    }, 1000);

    window.setTimeout(function () {
	addAlert("<center><p>Here you can find various links pertaining to Eli Hickox.</p></center>");
    }, 10000);

    window.setTimeout(function () {
	addAlert("<center><p>Check out a sample of my photography below.</p></center>");
    }, 20000);

    window.setTimeout(function () {
	addAlert("<center><p>Photographs and Website ©2015, Eli Hickox</p></center>");
    }, 20000);
});

function addAlert(message) {
    var id = createUUID();
    var JQueryId = "#" + id;

    $('#alerts').append(
	'<div style="display:none;" class="alert-alert-warning" id="' + id + '">' +
	    '<button type="button" class="close" data-dismiss="alert">' +
	    '</button>' + message + '</div>');

    $(JQueryId).fadeIn(3000);
    window.setTimeout(function () {

	// closing the popup
	$(JQueryId).fadeTo(300, 0.5).slideUp(2000, function () {
	    $(JQueryId).alert('close');
	});


    }, 10000);
}

function onError() {
    addAlert('Lost connection to server.');
}

function ViewModel()
{
    var self = this;
    self.bookmarksArray = ko.observableArray();
}

function Bookmark(name, description)
{
    var self = this;
    self.Name = ko.observable(name);
    self.Description = ko.observable(description);
    self.tags = ko.observableArray();
    self.ImageSrc = ko.computed(function () { return 'http://api.webthumbnail.org?width=100&height=100&screen=1024&url=' + self.Name();});
}

function Tag(name)
{
    var self = this;
    self.Name = name;
}

function createUUID() {
    // http://www.ietf.org/rfc/rfc4122.txt
    var s = [];
    var hexDigits = "0123456789abcdef";
    for (var i = 0; i < 36; i++) {
	s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
    }
    s[14] = "4";  // bits 12-15 of the time_hi_and_version field to 0010
    s[19] = hexDigits.substr((s[19] & 0x3) | 0x8, 1);  // bits 6-7 of the clock_seq_hi_and_reserved to 01
    s[8] = s[13] = s[18] = s[23] = "-";

    var uuid = s.join("");
    return uuid;
}
