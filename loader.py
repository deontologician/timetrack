from __future__ import print_function

from cmd import Cmd
import cPickle
import sqlite3
import re
from datetime import datetime, date, time, timedelta

cursor = sqlite3.connect('timetrack.db')

def prettytimes(dt1, dt2):
    '''Prints two times in a nice format'''
    return ' '.join([dt1.strftime('%m/%d/%Y %I:%M%p'),
                     dt2.strftime('%I:%M%p')])

class TimeTracker(Cmd):
    '''Keeps track of time!'''
    
    def __init__(self, dbname='timetrack.db'):
        self.conn = sqlite3.connect(dbname, 
                 detect_types=sqlite3.PARSE_DECLTYPES| sqlite3.PARSE_COLNAMES)
        try:
            self.date = self.conn.execute(
                "SELECT max(end) as 'end [timestamp]' from events").next()[0].date()
        except Exception as e:
            print(e)
            self.date = date.today() - timedelta(1)
        print("Date is set for {}".format(self.date))
        print('Last entry:')
        self.do_show('last')
        self.prompt = '@:: '
        Cmd.__init__(self)
        
    def do_sql(self, sql):
        with self.conn:
            for row in self.conn.execute(sql):
                print(*row, sep=' | ')

    def onecmd(self, st):
        try:
            Cmd.onecmd(self, st)
        except Exception as e:
            print(e)
            
            
    def do_EOF(self, line):
        return True

    def default(self, entry):
        r'''Add a new entry to the timetrack database'''
        code, subcode, rest = entry.split(' ', 2)
        name, start, end = rest.rsplit(' ', 2)
        if len(subcode) > 1 or not re.match(r'[A-Z]', subcode):
            subcode = None
        start = datetime.combine(self.date, time(*divmod(int(start), 100)))
        end_time = time(*divmod(int(end), 100))
        if end_time < start.time():
            self.date += timedelta(1)
            print('Date moved forward to {}'.format(self.date))
        end = datetime.combine(self.date, end_time)
        with self.conn:
            self.conn.execute('INSERT INTO events (code, subcode, name, start, end)'
                              'VALUES (?, ?, ?, ?, ?)', (code, subcode, name, start, end))

    def do_create(self, line):
        with self.conn:
            self.conn.execute('CREATE TABLE events (id integer primary key autoincrement,'
                              'code text, subcode text, name text, start timestamp,'
                              'end timestamp)'
                         )
            print('Successfully initialized timetrack database.')

    def do_nextday(self, line):
        try:
            days = int(line)
        except Exception:
            days = 1
        self.date = self.date + timedelta(days)

    def do_prevday(self, line):
        try:
            days = int(line)
        except Exception:
            days = 1
        self.date = self.date - timedelta(days)

    def do_echo(self, line):
        print(line.format(**self.__dict__))
        
    def do_show(self, line):
        '''show recent entries'''
        try:
            val = int(line)
        except ValueError:
            val = 10
        for id_, code, subcode, name, start, end in \
                self.conn.execute('select id, code, subcode, name, start, end '
                                  'from events order by id desc limit ?', (val,)):
            print('{:5} - {} {} {} {}'.format(id_, prettytimes(start, end), code, 
                                              subcode or ' ', name))

    def do_fixdate(self, line):
        '''Fix a date for a range of entries.
        Example:
        @:: fixdate 124-193 2012-11-02
        '''
        args = line.split(' ')
        rng = map(int, args[0].split('-'))
        dt = date(*map(int, args[1].split('-')))
        for i in xrange(rng[0], rng[1] + 1):
            with self.conn:
                entry = self.conn.execute("SELECT start, end FROM events WHERE id = ?",
                                          (i,)).next()
                dt1 = entry[0].date()
                tm1 = entry[0].time()
                dt2 = entry[1].date()
                tm2 = entry[1].time()
                if dt2 > dt1:
                    dt2 = dt + (dt2 - dt1)
                dt1 = dt
                self.conn.execute("UPDATE events SET start=?, end=? WHERE id = ?",
                                  (datetime.combine(dt1, tm1), datetime.combine(dt2, tm2), i))
        print("Set entries {} through {} to {}".format(rng[0], rng[1], dt))


if __name__ == '__main__':
    try:
        TimeTracker().cmdloop()
    except KeyboardInterrupt:
        print("exit")
