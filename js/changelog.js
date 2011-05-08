var parse_date;
String.prototype.cap_first = function() {
  return this[0].toUpperCase() + this.slice(1);
};
parse_date = function(date_string) {
  var pd;
  pd = date_string.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/);
  return new Date(pd[1], pd[2], pd[3], pd[4], pd[5], pd[6]);
};