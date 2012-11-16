import csv, sqlite3
from datetime import date, time, datetime, timedelta

def csv2row(line):
    name = line[0]
    code = line[1]
    subcode = line[2] or None
    m = map(int, line[3].split('/'))
    dt = date(m[2], m[0], m[1])
    t1 = time(*map(int, line[5].split(':')))
    start = datetime.combine(dt, t1)
    t2_arr = map(int, line[6].split(':'))
    if t2_arr[0] > 23:
        dt = dt + timedelta(1)
        t2_arr[0] = t2_arr[0] - 24
    end = datetime.combine(dt, time(*t2_arr))
    return (code, subcode, name, start, end)

if __name__ == '__main__':
    conn = sqlite3.connect('timetrack.db', detect_types=sqlite3.PARSE_DECLTYPES)
    p = csv.reader(open('lograw.csv'))
    p.next() #skip headers
    with conn:
        r = conn.executemany('insert into events(code, subcode, name, start, end)'
                             'values (?, ?, ?, ?, ?)', map(csv2row,p))
    print 'successfully imported {} entries'.format(r.next()[0])
