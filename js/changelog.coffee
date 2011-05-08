String.prototype.cap_first = ->
    @[0].toUpperCase() + @[1..]

parse_date = (date_string) ->
    # 2011-03-04 22:16:48.000000000

    pd = date_string.match /(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})/

    new Date pd[1], pd[2], pd[3], pd[4], pd[5], pd[6]
