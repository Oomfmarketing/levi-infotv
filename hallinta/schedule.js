/* LeviTV — when is a customer's banner or ticker line shown?
   Shared by the TV page and the customer admin page. ES5 so old TV browsers run it.
   Item fields: on, days [1=Mon … 7=Sun], from/to "HH:MM" (overnight allowed), start/end "YYYY-MM-DD".
   All times are Finnish time (Europe/Helsinki). */
(function (g) {
  var F = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Helsinki', hour12: false,
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', weekday: 'short' });
  var WD = { Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6, Sun: 7 };
  var FI = ['', 'ma', 'ti', 'ke', 'to', 'pe', 'la', 'su'];
  function helNow(d) {
    var p = {};
    F.formatToParts(d || new Date()).forEach(function (x) { p[x.type] = x.value; });
    var h = ('0' + (+p.hour % 24)).slice(-2);
    var wd = WD[p.weekday] || 1;
    return { date: p.year + '-' + p.month + '-' + p.day, time: h + ':' + p.minute, wd: wd,
      label: FI[wd] + ' ' + (+p.day) + '.' + (+p.month) + '. klo ' + h + ':' + p.minute };
  }
  function active(it, d) {
    if (!it || it.on === false) return false;
    var n = helNow(d);
    if (it.start && n.date < it.start) return false;
    if (it.end && n.date > it.end) return false;
    var from = it.from || '', to = it.to || '';
    if (from && to && to <= from) {            // overnight, e.g. 22:00–02:00: the morning part belongs to the previous day
      if (n.time >= from) return dayOk(it, n.wd);
      if (n.time < to) return dayOk(it, n.wd === 1 ? 7 : n.wd - 1);
      return false;
    }
    if (from && n.time < from) return false;
    if (to && n.time >= to) return false;
    return dayOk(it, n.wd);
  }
  function dayOk(it, wd) { return !it.days || !it.days.length || it.days.indexOf(wd) >= 0; }
  g.LeviSchedule = { active: active, helNow: helNow };
})(window);
