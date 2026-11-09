"""SQLite persistence. One atomic optimistic revision per map update."""
import json
import sqlite3
import time
from pathlib import Path

class Conflict(Exception):
    pass

class Store:
    def __init__(self, path: Path, seed: dict):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS project(id INTEGER PRIMARY KEY, revision INTEGER NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, time INTEGER, label TEXT, detail TEXT);
            CREATE TABLE IF NOT EXISTS commands(id TEXT PRIMARY KEY, request TEXT, result TEXT);''')
            db.execute('INSERT OR IGNORE INTO project VALUES(1,1,?)', (json.dumps(seed),))

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def read(self):
        with self.connect() as db:
            revision, raw = db.execute('SELECT revision,data FROM project WHERE id=1').fetchone()
        return {'revision': revision, 'project': json.loads(raw)}

    def save(self, data, revision):
        with self.connect() as db:
            result = db.execute('UPDATE project SET data=?,revision=revision+1 WHERE id=1 AND revision=?', (json.dumps(data), revision))
            if result.rowcount != 1:
                raise Conflict('De kaart werd in een ander venster gewijzigd. Exporteer je wijziging of laad opnieuw.')
        return revision + 1

    def event(self, label, detail=''):
        with self.connect() as db:
            db.execute('INSERT INTO events(time,label,detail) VALUES(?,?,?)', (int(time.time()*1000), label, detail))
            db.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 500)')

    def events(self):
        with self.connect() as db:
            return [dict(zip(['time','label','detail'], r)) for r in db.execute('SELECT time,label,detail FROM events ORDER BY id DESC LIMIT 80')]

    def command(self, id):
        with self.connect() as db:
            row = db.execute('SELECT request,result FROM commands WHERE id=?', (id,)).fetchone()
        return None if row is None else (json.loads(row[0]), json.loads(row[1]))

    def save_command(self, request, result):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO commands VALUES(?,?,?)', (request['id'], json.dumps(request), json.dumps(result)))
            db.execute('DELETE FROM commands WHERE rowid NOT IN (SELECT rowid FROM commands ORDER BY rowid DESC LIMIT 500)')

    def recent_commands(self):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT result FROM commands ORDER BY rowid DESC LIMIT 12')]

    def interrupt_pending(self):
        with self.connect() as db:
            for id, raw in db.execute('SELECT id,result FROM commands').fetchall():
                result = json.loads(raw)
                if result['status'] == 'accepted':
                    result.update(status='failed', message='Lokale server herstart; opdracht niet hervat.')
                    db.execute('UPDATE commands SET result=? WHERE id=?', (json.dumps(result), id))
