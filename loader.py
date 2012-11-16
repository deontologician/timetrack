from cmd import Cmd
import cPickle
import sqlite3
import re
from datetime import datetime, date, time, timedelta

cursor = sqlite3.connect('timetrack.db')

def str_to_datetime(s):
    return cPickle.loads(s)

def datetime_to_str(dt):
    return cPickle.dumps(dt)

sqlite3.register_converter('datetime', str_to_datetime)
sqlite3.register_adapter(datetime, datetime_to_str)

def prettytimes(dt1, dt2):
    '''Prints two times in a nice format'''
    return ' '.join([dt1.strftime('%m/%d/%y %I:%M%p'),
                     dt1.strftime('%I:%M%p')])

class TimeTracker(Cmd):
    '''Keeps track of time!'''
    
    def __init__(self, dbname='timetrack.db'):
        self.conn = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES)
        self.date = date.today()
        self.prompt = '@:: '
        self.tablename = 'events'
        Cmd.__init__(self)

    def default(self, entry):
        r'''Add a new entry to the timetrack database'''
        code, subcode, start, end, name = entry.split(' ', 4)
        if len(subcode) > 1 or not re.match(r'[A-Z]', subcode):
            subcode = None
        start = datetime.combine(self.date, time(*divmod(int(start), 100)))
        end = datetime.combine(self.date, time(*divmod(int(end), 100)))
        with self.conn:
            self.conn.execute('INSERT INTO events (code, subcode, name, start, end)'
                              'VALUES (?, ?, ?, ?, ?)', (code, subcode, name, start, end))

    def do_create(self, line):
        with self.conn:
            self.conn.execute('CREATE TABLE {} (id integer primary key autoincrement,'
                              'code text, subcode text, name text, start datetime,'
                              'end datetime)'.format(self.tablename)
                         )
            print 'Successfully initialized timetrack database.'

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
        print line.format(**self.__dict__)
        
    def do_show(self, line):
        '''show recent entries'''
        try:
            val = int(line)
        except ValueError:
            val = 10
        for code, subcode, name, start, end in \
                self.conn.execute('select code, subcode, name, start, end '
                                  'from events order by end asc limit ?', (val,)):
            print '{} {} {} {}'.format(prettytimes(start, end), name, code, subcode or '-')

    def onecmd(self, st):
        try:
            Cmd.onecmd(self, st)
        except Exception as e:
            print e
            
            
    def do_EOF(self, line):
        return True

if __name__ == '__main__':
    try:
        TimeTracker().cmdloop()
    except KeyboardInterrupt:
        print "exit"
