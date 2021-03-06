from datetime import datetime, timedelta
import datetime as dtime
from event import Event
from agenda import Agenda
from sqlalchemy import extract, and_, desc
import random

class Find(object):
	def __init__(self, db, jdID, event=None, selftime=None, nearest=False, anstype=None):
		self.db = db
		self.jdID = jdID
		self.e = event
		self.nearest = nearest
		self.selftime = selftime
		self.approximate = ['预计需要', '大概要', '预计会占用您']

		self.key = []

		if self.e is not None:
			if self.e.get_detail() is not None:
				self.__key_gen()


	def find(self):
		if self.e.get_detail() is not None:
			check, rst = self.__santity_check()
			if check is False:
				return rst

		rst = self.__which_find()
		return rst

	def help(self):
		rst = self.__help_find()
		return rst


	def __key_gen(self):
		f = open('detail', 'r')
		lines = f.readlines()
		for l in lines:
			self.key.append(l.rstrip())


	def __santity_check(self):
		if self.e.get_detail() not in self.key:
			return False, '啊噢，我还不是很聪明，没有懂您的意思。换种说法的话我也许能懂呢。'
		else:
			return True, ''


	def __which_find(self):
		year, month, day, hour, minute, detail = \
		self.e.get_year(), self.e.get_month(), self.e.get_day(), \
		self.e.get_hour(), self.e.get_minute(), self.e.get_detail()

		nearest = self.nearest

		if year is None and hour is None and detail is None:
			rst = self.__find_none()
		elif hour is None and detail is None:
			rst = self.__find_all()
		elif year is None and hour is None and nearest is True:
			rst = self.__find_next()
		elif year is None and hour is None and nearest is False:
			rst = self.__find_all_detail()
		elif detail is None:
			rst = self.__find_event(year=year, month=month, day=day)
		else:
			rst = self.__confirm(year=year, month=month, \
				day=day, hour=hour, minute=minute, detail=detail)
		return rst


	def __help_find(self):
		event = self.db.session.query(Agenda).filter(Agenda.jdID==self.jdID).all()
		print(event)
		if len(event) == 0:
			phrases = ['''您可以先回复添加来规划您的第一条计划哈。添加计划有很多种方法噢，比如您可以说
			我要添加明天早上9点的会议来添加您的第一条计划。目前支持添加的计划类型有很多噢，包括工作类（如会议、
			和老板碰面、加班、团建），运动类（如健身、跑步、骑行、游泳、打网球），个人活动类（如约会、聚餐、
			看电影、购物）。活动类型也会不断扩展，感谢您的宝贵意见。''']
			n = random.randrange(0, len(phrases), 1)
			rst = '欢迎使用您的智能规划本，' + phrases[n]
		else:
			phrases = ['''您知道吗，查找或删除计划的方法有很多种噢。如果您问: 我今天都安排了什么事情？或者我下次的会议是什么时候？您的智能规划本
			都能懂呢。''', '''查找或删除计划的方法有很多种噢，如果您说：我要查下次会议是什么时候，或者我要删除
			下次会议，您的智能规划本都能明白呢。如果您要更改计划的话，可以先说我要更改计划，规划本会引导您
			完成计划修改哈。''']
			n = random.randrange(0, len(phrases), 1)
			rst = phrases[n]
		return rst

	def __confirm_selftime(self, year, month, day, detail):
		if self.selftime is None:
			query = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID,
				extract('year', Agenda.startTime) == year,
				extract('month', Agenda.startTime) == month,
				extract('day', Agenda.startTime) == day,
				Agenda.agendaDetail == detail))
			event = query.order_by(Agenda.startTime).all()
			return event
		elif self.selftime == '上午':
			t1 = datetime(year, month, day, 0, 0)
			t2 = datetime(year, month, day, 11, 59)
		elif self.selftime == '下午':
			t1 = datetime(year, month, day, 12, 0)
			t2 = datetime(year, month, day, 17, 59)
		else:
			t1 = datetime(year, month, day, 18, 0)
			t2 = datetime(year, month, day, 23, 59)
		query = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID,
			extract('year', Agenda.startTime) == year,
			extract('month', Agenda.startTime) == month,
			extract('day', Agenda.startTime) == day,
			Agenda.startTime.between(t1, t2),
			Agenda.agendaDetail == detail))
		event = query.order_by(Agenda.startTime).all()
		return event


	def __confirm(self, year=None, month=None,\
	 day=None, hour=None, minute=None, detail=None):
		year, month, day, hour, minute, detail = year, month, day, hour, minute, detail
		if hour is None:
			event = self.__confirm_selftime(year, month, day, detail)
			if len(event) == 0:
				ending = self.__find_next().replace('您还没有安排下次的','事实上，您还没有安排任何未来的')
				rst = '您并没有在' + self.e.day_des_gen()
				rst += '' if self.selftime is None else self.selftime
				rst += '安排关于' + detail + '的计划呢。' + ending
			else:
				rst = '您在' + self.e.day_des_gen()
				rst += '' if self.selftime is None else self.selftime 
				rst += '有' + str(len(event)) + '条关于' + detail + '的安排，' 
				rst += '该计划预计是' if len(event) == 1 else '它们的时间分别是，'
				for n, a in enumerate(event):
					a = a.make_event()
					rst += '从' + a.time_des_gen() + '开始到' + a.time_des_gen(False) + '结束，'
				rst += '请不要忘记哟。'
		else:
			event = self.db.session.query(Agenda).filter(
				and_(Agenda.jdID==self.jdID,
				extract('year', Agenda.startTime) == year,
				extract('month', Agenda.startTime) == month,
				extract('day', Agenda.startTime) == day,
				extract('hour', Agenda.startTime) == hour,
				extract('minute', Agenda.startTime) == minute,
				Agenda.agendaDetail == detail)).first()
			if event is None:
				ending = self.__find_next().replace('您还没有安排下次的','事实上，您还没有安排任何未来关于')
				rst = '您并没有在' + self.e.day_des_gen() + self.e.time_des_gen() + \
				'安排' + detail + '计划呢。' + ending
			else:
				opening = ['确实有这个计划噢。', '有的噢。', '您没有记错，确实有这个计划呢。']
				n = random.randrange(0, len(opening), 1)
				a = event.make_event()
				rst = opening[n] + '该计划预计需要' + a.duration_des_gen() + '，结束时间大概在' + \
				a.time_des_gen() + '左右。'
		return rst


	def __find_next(self):
		detail = self.e.get_detail()
		query = self.db.session.query(Agenda).filter(and_(
				Agenda.jdID==self.jdID,
				Agenda.agendaDetail == detail,
				Agenda.startTime >= datetime.now()))
		event = query.order_by(Agenda.startTime).first()
		if event is None:
			rst = '您还没有安排下次关于' + detail + '的计划哟。您可以回复添加计划来规划下一次的' + detail + '。'
		else:
			ending = ['可不要忘了噢！', 
			'如需取消安排，请回复删除下一次的' + detail + '计划或者修改下一次的' + detail + '计划。',
			'感谢您的使用，祝您一切顺意。']
			n = random.randrange(0, len(ending), 1)
			a = event.make_event()
			rst = '您下一次的' + detail + '计划是在' + a.day_des_gen() + a.time_des_gen() + '，' + \
			'预计需要' + a.duration_des_gen() + '，将会在' + a.day_des_gen(start=False) + a.time_des_gen(start=False) + '结束。' + ending[n]
		return rst


	def __find_event(self, year=None, month=None, day=None, hour=None, minute=None):
		now = datetime.now()
		_year, _month, _day = now.year, now.month, now.day if year is None \
		else year, month, day

		_hour, _minute = hour, minute

		query = self.db.session.query(
			Agenda.startTime, Agenda.endTime, Agenda.agendaDetail).filter(and_(
				Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == _year,
				extract('month', Agenda.startTime) == _month,
				extract('day', Agenda.startTime) == _day,
				extract('hour', Agenda.startTime) == _hour,
				extract('minute', Agenda.startTime == _minute)))
		minute = '' if minute == 0 else str(minute) + '分'
		events = query.order_by(Agenda.startTime).all()
		if len(events) == 0:
			pos = '今天' + str(hour) + '点，' if date is None else \
			self.e.day_des_gen(start=True) + self.e.time_des_gen(start=True)
			rst = '您还没有在' + pos + '安排任何计划哟。您可以回复添加' + pos +'的计划来增加新计划。'

		else:
			for e in events:
				a = e.make_event()
				rst += a.get_des()

		return rst


	def __find_none(self):
		now = datetime.now()
		year, month, day = now.year, now.month, now.day
		_nexthreedays = datetime(year, month, day) + timedelta(4)
		query = self.db.session.query(Agenda).filter(and_(
			Agenda.jdID == self.jdID, 
			Agenda.startTime >= now,
			Agenda.startTime <= _nexthreedays))
		events = query.order_by(Agenda.startTime).all()
		if len(events) == 0:
			phrase = ['''在未来三天您没有安排任何计划噢。要想查其他安排的话，请再给我一点线索吧。
			比如您可以这样问：查下我下周五都有什么安排。或者，查查我下周五是不是要开会等等。''', 
			'''我没有记录您未来三天的任何安排噢。请问您具体想查点什么呢？
			比如您可以说：查下我下周五什么时候开会。或者您也可以问：查查我下周五是不是要开会。''']
			n = random.randrange(0, len(phrase), 1)
			return phrase[n]
		else:
			rst = '在未来的三天里，您安排了这些事儿：'
			for e in events:
				i = random.randrange(0, len(self.approximate), 1)
				year, month, day, hour, minute, duration, detail = \
				e.startyear(), e.startmonth(), e.startday(), e.starthour(), \
				e.startminute(), e.duration(), e.detail()
				a = Event(year=year, month=month, day=day, 
					hour=hour, minute=minute, duration=duration, event_detail=detail)
				des = [a.day_des_gen() + a.time_des_gen() + '您安排了' + a.get_detail() + '计划，' + \
				self.approximate[i] + a.duration_des_gen() + '。', 
				a.day_des_gen() + a.time_des_gen() + '您要去' + a.get_detail() + '，' + self.approximate[i]\
				+ a.duration_des_gen() + '。', a.day_des_gen() + a.time_des_gen() + '的' + a.get_detail() +\
				self.approximate[i] + a.duration_des_gen() + '。']
				j = random.randrange(0, len(des), 1)
				rst += des[j]
		return rst


	def __find_all_detail(self):
		detail = self.e.get_detail()
		query = self.db.session.query(Agenda).filter(and_(
				Agenda.jdID==self.jdID,
				Agenda.agendaDetail == detail,
				Agenda.startTime >= datetime.now()))
		event = query.order_by(Agenda.startTime).all()
		if len(event) == 0:
			rst = '您还没有安排任何' + detail + '计划哟。您可以回复添加计划来进行规划。'
		else:
			ending = ['可不要忘了噢！', '如果对这些功能不满意，您可以使用删除或者修改功能来重新安排。',
			'感谢您的使用，祝您一切顺意。']
			n = random.randrange(0, len(ending), 1)
			rst = '一共帮您查到' + str(len(event)) + '条' + detail + '的计划。'
			for e in event:
				a = e.make_event()
				i = random.randrange(0, len(self.approximate), 1)
				rst += a.day_des_gen() + a.time_des_gen() + '的' + detail + '，' + \
				self.approximate[i] + a.duration_des_gen() + '。' 
			rst += ending[n]
		return rst


	def __find_all(self, anstype=None):
		diff = self.e.get_diff_between_now_start()
		if diff.days > 7:
			rst = "不好意思哈，您的规划本只保存过去一星期内的记录。超过一星期的已经被自动删除了哟"
			return rst 

		year, month, day = self.e.get_year(), self.e.get_month(), self.e.get_day()

		query = self.db.session.query(Agenda).filter(and_(
				Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == year,
				extract('month', Agenda.startTime) == month,
				extract('day', Agenda.startTime) == day))
		events = query.order_by(Agenda.startTime).all()
		if len(events) == 0:
			rst = '您的规划本还没有记录' + self.e.day_des_gen(start=True) + '的任何计划哈，'
			return rst
		else:
			n = len(events)
			rst = "这天的" if anstype == '有什么事要做' \
			else self.e.day_des_gen() + '您有这' + str(n) + '件安排：'
			for e in events:
				a = e.make_event()
				rst += a.get_des()
		return rst
