var nightlies = [];
var merged;

function main() {
    if (!(nightlies && merged)) { return; }

    console.log(nightlies);
    // console.log(merged);

    console.log("got all required data, working...");

    var nightly = nightlies.shift();

    merged.forEach(function(e, i, a) {
        if (nightly[1] > e.last_updated) {
            $('#merged_changes').append("<h4>" + nightly[0] + "</h4>");
            nightly = nightlies.shift();
        }

        var change = e.subject.link("http://review.cyanogenmod.com/" + e.id)
        change += " (" + e.project + ")"

        $('#merged_changes').append(change + "<br />");
    });
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
