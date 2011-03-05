var nightlies = [];
var merged;
var buildbot_offset = 0;

Date.prototype.addHours= function(h){
    this.setHours(this.getHours()+h);
        return this;
}

function parse_date(date_string) {
    // 2011-03-04 22:16:48.000000000

    var pd = date_string.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);

    // console.log(pd);

    return new Date(pd[1], pd[2], pd[3], pd[4], pd[5], pd[6]);
}

function main() {
    if (!(nightlies && merged)) { return; }

    // console.log(nightlies);
    // console.log(merged);

    console.log("got all required data, working...");

    var nightly = nightlies.shift();

    merged.forEach(function(e, i, a) {
        nd = parse_date(nightly[1])
        cd = parse_date(e.last_updated)

        nd.addHours(20)

        if (nd > cd) {
            $('#merged_changes').append("<h4>" + nightly[0] + "</h4>");
            nightly = nightlies.shift();
        }

        var change = e.subject.link("http://review.cyanogenmod.com/" + e.id)
        change += " (" + e.project + ")"

        $('#merged_changes').append("<span>" + change + "</span>");
    });

    $("span:contains('ranslation')").addClass("translation");

}

function parse_nightlies(data) {
    console.log("got nightlies");

    nightlies_raw  = data.responseText.match(/cm_[\s\S]*?\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/g);

    nightlies_raw.forEach(function(e, i, a) {
        var parsed = e.match(/(cm_.*?.zip)[\s\S]*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);

        nightlies.push([parsed[1], parsed[2]]);
    });

    main();
}

function parse_changelog(data) {
    console.log("got changelog");

    merged = data;

    main();
}

$(document).ready(function () {
    var device = "ace";

    var nightlies = "http://mirror.teamdouche.net/"
    var changelog = "/changelog/"

    console.log("getting nightlies...");

    $.get(changelog, success=parse_changelog);
    $.get(nightlies, {device: device}, parse_nightlies);
});
