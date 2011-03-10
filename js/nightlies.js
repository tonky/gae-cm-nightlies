var nightlies = [];
var merged;
var buildbot_offset = 0;
var device = "ace";

Date.prototype.addHours= function(h){
    this.setHours(this.getHours()+h);
        return this;
}

function parse_date(date_string) {
    // 2011-03-04 22:16:48.000000000

    var pd = date_string.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);

    return new Date(pd[1], pd[2], pd[3], pd[4], pd[5], pd[6]);
}

function main() {
    if (!(nightlies && merged)) { return; }

    $('#merged_changes').empty();

    var nightly = nightlies.shift();

    merged.forEach(function(e, i, a) {
        nd = parse_date(nightly[1])
        cd = parse_date(e.last_updated)

        nd.addHours(buildbot_offset)

        if (nd > cd) {
            // console.log("Nightly is older than change");
            $('#merged_changes').append("<h4>" + nightly[0] + "</h4>");
            nightly = nightlies.shift();
        }

        var change = e.subject.link("http://review.cyanogenmod.com/" + e.id)
        change += " (" + e.project + ")"

        $('#merged_changes').append("<span>" + change + "</span>");
    });

    $("span:contains('ranslat')").addClass("translation");
    $("span:contains('ussian')").addClass("translation");
    $("span:contains('hinese')").addClass("translation");
    $("span:contains('erman')").addClass("translation");

    $("a[href*='"+device+"']").addClass("highlight");

}

function parse_nightlies(data) {
    nightlies_raw  = data.responseText.match(/cm_[\s\S]*?\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/g);

    nightlies_raw.forEach(function(e, i, a) {
        var parsed = e.match(/([\w\d\._-]*?.zip)[\s\S]*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);

        nightlies.push([parsed[1], parsed[2]]);
    });

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

$(document).ready(function () {
    device = get_qs("device", device);

    var nightlies = "http://mirror.teamdouche.net/"
    var changelog = "/changelog/"

    $.get(changelog, {device: device}, parse_changelog);
    $.get(nightlies, {device: device}, parse_nightlies);
});
