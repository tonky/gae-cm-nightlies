var nightlies = [];
var merged = [];
var device = "ace";

Date.prototype.addHours = function(h){
    this.setHours(this.getHours()+h);
        return this;
}

String.prototype.cap_first = function(){
    return this.charAt(0).toUpperCase() + this.slice(1);
}

function parse_date(date_string) {
    // 2011-03-04 22:16:48.000000000

    var pd = date_string.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);

    return new Date(Date.UTC(pd[1], parseInt(pd[2]-1), pd[3], pd[4], pd[5], pd[6]));
}

function main() {
    if (nightlies.length == 0 || merged.length == 0) { return; }

    var nightly = nightlies.shift();

    $('#merged_changes').empty();

    if (nightly && (parse_date(merged[0].last_updated) > parse_date(nightly[1]))) {
        $('#merged_changes').append("<h3>to be included in next nightly:</h3>");
    }

    merged.forEach(function(e, i, a) {
        if(!nightly) { return; }

        var cd = parse_date(e.last_updated);
        var nd = parse_date(nightly[1]);

        while (cd < nd && (nightlies.length > 0)) {
            nightly_link = "<a href='http://download.cyanogenmod.com/?device="+ device +"' name='"+ nightly[0] +"'>" + nightly[0] + "</a>"+
                " <span class='nightly_date'>("+ nd +")</span>";

            $('#merged_changes').append("<h4>" + nightly_link + "</h4>");

            nightly = nightlies.shift();
            nd = parse_date(nightly[1]);
        }

        var change = e.subject.link("http://review.cyanogenmod.com/" + e.id)
        change += " (" + e.project + ")"

        $('#merged_changes').append("<span>" + change + "</span>");
    });

    $("span:contains('ranslat')").addClass("translation");
    $("span:contains('ocaliz')").addClass("translation");
    $("span:contains('ussian')").addClass("translation");
    $("span:contains('hinese')").addClass("translation");
    $("span:contains('ortug')").addClass("translation");
    $("span:contains('erman')").addClass("translation");
    $("span:contains('wedish')").addClass("translation");
    $("span:contains('typo')").addClass("translation");
    $("span:contains('_" + device + "')").addClass("device");
    $("span:contains('" + device + ":')").addClass("device");
    $("span:contains('" + device.cap_first() + ":')").addClass("device");

    $("#device_links a[href$='"+device+"']").addClass("highlight");

    trans_visibility();

    var loc = document.location.toString();

    if (loc.match('#')) {
      var anchor = '#' + loc.split('#')[1];
      location.href = anchor;
    }
}

function parse_nightlies(data) {
    if (data.results.length == 0) {
        return $('#merged_changes').text("Yahoo API is down, please try about five minutes later.");
    }

    nightlies_raw  = data.results[0].match(/[\s\S]*?\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/g);

    if (!nightlies_raw) {
        return $('#merged_changes').append("<h4 class='error'>Device not found. Maybe you misspelled the device name in the url, or device isn't supported yet. This is still WIP, i'll add all CM supported devices eventually. Please click a link in the header.</h1>");
    }

    nightlies_raw.forEach(function(e, i, a) {
        var parsed = e.match(/([\w\d\._-]*?.zip)[\s\S]*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);

        nightlies.push([parsed[1], parsed[2]]);
    });

    if(nightlies.length == 0) {
        return $('#merged_changes').text("Unable to parse nightlies, maybe cyanogenmod mirror is down. Please try a bit later.");
    }

    main();
}

function parse_changelog(data) {
    merged = data;
    main();
}

function get_qs(key, default_) {
  if (default_==null) default_=""; 
  key = key.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
  var regex = new RegExp("[\\?&]"+key+"=([^&#]*)");
  var qs = regex.exec(window.location.href);
  if(qs == null)
    return default_;
  else
    return qs[1];
}

function trans_visibility() {
    if ($("#hide_them").attr("checked")) {
        $(".translation").addClass("hidden");
        $.cookie('cm-nightlies', 1);
    } else {
        $(".translation").removeClass("hidden");
        $.cookie('cm-nightlies', null);
    }
}

$(document).ready(function () {
    device = get_qs("device", device);

    if ($.cookie('cm-nightlies')) { $("#hide_them").attr("checked", true); }

    var nightlies = "http://download.cyanogenmod.com/"
    var changelog = "/changelog/"

    $.get(changelog, {device: device}, parse_changelog);
    $.get(nightlies, {device: device}).success(parse_nightlies);

    $("#hide_them").click(function() { trans_visibility(); });

    $("#announcement_header").click(function() { $("#announcement_text").toggleClass("hidden") ; });
});
