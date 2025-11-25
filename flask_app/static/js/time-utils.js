/* Centralized time helpers used across event templates */
(function (global) {
  if (typeof dayjs !== 'undefined') {
    try { if (typeof dayjs_plugin_customParseFormat !== 'undefined') dayjs.extend(dayjs_plugin_customParseFormat); } catch (e) {}
    try { if (typeof dayjs_plugin_relativeTime !== 'undefined') dayjs.extend(dayjs_plugin_relativeTime); } catch (e) {}
  }

  function tryParse(raw) {
    if (!raw) return null;
    if (typeof dayjs !== 'undefined') {
      let d = dayjs(raw);
      if (d.isValid()) return d;
      const formats = ['YYYY-MM-DD HH:mm:ss', 'YYYY-MM-DDTHH:mm:ss', 'YYYY-MM-DD'];
      for (const f of formats) {
        d = dayjs(raw, f);
        if (d.isValid()) return d;
      }
      return null;
    }
    // Fallback without dayjs
    const dt = new Date(raw);
    return isNaN(dt.getTime()) ? null : {
      isValid: () => true,
      toDate: () => dt,
      diff: (other) => dt.getTime() - (other instanceof Date ? other.getTime() : other.toDate().getTime()),
      format: () => dt.toISOString(),
    };
  }

  function humanDuration(ms) {
    if (ms <= 0) return 'Started';
    const sec = Math.floor(ms / 1000) % 60;
    const min = Math.floor(ms / (1000 * 60)) % 60;
    const hrs = Math.floor(ms / (1000 * 60 * 60)) % 24;
    const days = Math.floor(ms / (1000 * 60 * 60 * 24));
    if (days > 0) return `${days}d ${hrs}h`;
    if (hrs > 0) return `${hrs}h ${min}m`;
    if (min > 0) return `${min}m ${sec}s`;
    return `${sec}s`;
  }

  function formatSingle(raw) {
    const d = tryParse(raw);
    if (!d) return '—';
    const hasTime = /\d{1,2}:\d{2}/.test(raw);
    const datePart = d.format ? d.format(hasTime ? 'MMM D, YYYY · h:mm A' : 'MMM D, YYYY') : String(raw);
    const relative = (d.fromNow ? d.fromNow() : '');
    return `${datePart} ${relative ? '— ' + relative : ''}`;
  }

  function computeStatus(startRaw, endRaw) {
    const now = (typeof dayjs !== 'undefined') ? dayjs() : new Date();
    const start = tryParse(startRaw);
    const end = tryParse(endRaw);
    const before = (a, b) => (a.from ? a.from(b) < 0 : a.diff ? a.diff(b) < 0 : a.toDate() < b);
    const after = (a, b) => (a.diff ? a.diff(b) > 0 : a.toDate() > b);

    if (!start && !end) return 'Unknown';
    if (start && end) {
      if (start.diff ? start.diff(now) > 0 : start.toDate() > now) return 'Waiting';
      if (end.diff ? end.diff(now) < 0 : end.toDate() < now) return 'Closed';
      return 'Open';
    }
    if (start && !end) return (start.diff ? start.diff(now) > 0 : start.toDate() > now) ? 'Waiting' : 'Open';
    if (!start && end) return (end.diff ? end.diff(now) < 0 : end.toDate() < now) ? 'Closed' : 'Open';
    return 'Unknown';
  }

  global.TimeUtils = { tryParse, humanDuration, formatSingle, computeStatus };
})(window);
