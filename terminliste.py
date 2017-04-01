#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
import copy
import datetime
import dateutil
import sys
import urllib
import vobject

month_names = [
'',
'Januar',
'Februar',
'Mars',
'April',
'Mai',
'Juni',
'Juli',
'August',
'September',
'Oktober',
'November',
'Desember',
]

class Event:
	def __init__(self):
		self.summary     = u''
		self.description = u''
		self.tags        = []
		self.start       = datetime.date(2000, 1, 1)
		self.stop        = None

	@staticmethod
	def parse(vevent):
		event = Event()
		event.summary      = vevent.summary.value
		event.description  = vevent.description.value
		event.start        = vevent.dtstart.value
		if hasattr(vevent, 'dtend'):
			event.stop         = vevent.dtend.value
		try:
			event.tags = vevent.x_tags.value.split(',')
		except AttributeError:
			event.tags = []

		ret = []

		rruleset = vevent.getrruleset()
		if rruleset:
			duration = vevent.dtend.value - vevent.dtstart.value
			for start in list(rruleset):
				stop = start + duration
				e = copy.copy(event)
				e.start = start
				e.stop = stop
				ret.append(e)
		else:
			ret.append(event)

		return ret

	def get_html(self):
		ret = []
		ret.append(u'<div class="event">')
		if type(self.stop) is datetime.date:
			self.stop -= datetime.timedelta(days=1)
		if self.start.day == self.stop.day:
			day = '{}.'.format(self.start.day)
		else:
			day = '{}. - {}.'.format(self.start.day, self.stop.day)
		ret.append(u'<h1><small>{} - </small>{}</h1>'.format(day, self.summary))
		if self.tags:
			ret.append(u'<div class="tags">')
			ret.append(u''.join([u'<div class="tag {0}">{0}</div>'.format(tag.lower(), tag) for tag in self.tags]))
			ret.append(u'</div>')
		ret.append(u'<div class="description">{}</div>'.format(self.description))
		ret.append(u'</div>')
		ret.append(u'')
		return u'\n'.join(ret)

	def __str__(self):
		return u'''{}
    {}
    Tag: {}'''.format(self.summary, self.description, ', '.join(self.tags))

def gettext(element, path, default=u''):
	a = element.find(path)
	if a is None:
		return default
	if a.text is None:
		return default
	return a.text

url='http://www.manstadskolekorps.no/?plugin=all-in-one-event-calendar&controller=ai1ec_exporter_controller&action=export_events'

sys.stdout.write('<!DOCTYPE html>\n')
sys.stdout.write('<html lang="nb">\n')
sys.stdout.write('<head>\n')
sys.stdout.write('<meta charset="UTF-8">\n')
sys.stdout.write('<title>Terminliste</title>\n')
sys.stdout.write('<link rel="stylesheet" href="styles.css">\n')
sys.stdout.write('</head>\n')
sys.stdout.write('<body>\n')
sys.stdout.write('<div class="terminliste">\n')
sys.stdout.write('<img src="logo_banner_300.png" >\n')

datestart = datetime.date.today()#date(2017,  1,  1)
dateend   = datetime.date(2017, 4, 30)

events=[]
cal=vobject.readOne(urllib.urlopen(url))
for child in cal.getChildren():
	if not isinstance(child, vobject.icalendar.RecurringComponent):
		continue

	if False:
		start = child.dtstart.value
		if isinstance(start, datetime.datetime):
			start = start.date()
		if start > dateend:
			continue

		try:
			end = child.dtend.value
			if isinstance(end, datetime.datetime):
				end = end.date()
			if end < datestart:
				continue
		except AttributeError:
			pass

	events.extend(Event.parse(child))

lastMonth = None
for event in sorted(events, key=lambda x: x.start if type(x.start) is datetime.date else x.start.date()):
	if (event.start if type(event.start) is datetime.date else event.start.date()) > dateend:
		continue
	if (event.stop if type(event.stop) is datetime.date else event.stop.date()) < datestart:
		continue
	if 'samspill' in event.summary.lower():
		continue
	if 'trening, drillen' in event.summary.lower():
		continue
	if u'korøvelse' in event.summary.lower():
		continue
	if lastMonth != event.start.month:
		if lastMonth is not None:
			sys.stdout.write('</div><hr>\n')
		lastMonth = event.start.month
		sys.stdout.write('<div class="month"><h1>{}</h1>\n'.format(month_names[lastMonth]))
	sys.stdout.write(event.get_html().encode('utf-8'))

sys.stdout.write('</div>\n')
sys.stdout.write('</body>\n')
sys.stdout.write('</html>\n')
