test("helper functions", function() {
  equal("hello".cap_first(), "Hello");
  return deepEqual(parse_date("2011-03-04 22:16:48.000000000"), new Date(2011, 03, 04, 22, 16, 48));
});