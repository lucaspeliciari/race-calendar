import sqlite3
from helpers.categories import categories
from helpers.constants import SETTINGS


def create_tables():
    conn.execute('CREATE TABLE IF NOT EXISTS users ('
                 'id INTEGER UNIQUE, '
                 'username TEXT UNIQUE, '
                 'hash TEXT, '
                 'PRIMARY KEY(id))'
                 )
    conn.execute('CREATE TABLE IF NOT EXISTS categories ('
                 'id INTEGER UNIQUE, '
                 'category_name TEXT UNIQUE, '
                 'PRIMARY KEY(id))'
                 )
    conn.execute('CREATE TABLE IF NOT EXISTS user_categories ('
                 'user_id INTEGER, '
                 'category_id INTEGER, '
                 'FOREIGN KEY (user_id) REFERENCES users (id), '
                 'FOREIGN KEY (category_id) REFERENCES categories (id), '
                 'UNIQUE(user_id, category_id))'  # test this
                 )
    conn.execute('CREATE TABLE IF NOT EXISTS settings ('
                 'id INTEGER UNIQUE, '
                 'setting_name TEXT UNIQUE, '
                 'PRIMARY KEY(id))'
                 )
    conn.execute('CREATE TABLE IF NOT EXISTS user_settings ('
                 'user_id INTEGER, '
                 'setting_id INTEGER, '
                 'FOREIGN KEY (user_id) REFERENCES users (id), '
                 'FOREIGN KEY (setting_id) REFERENCES settings (id), '
                 'UNIQUE(user_id, setting_id))'  # test this
                 )


def populate_categories():
    for i, category in enumerate(categories):
        cur.execute('INSERT OR IGNORE INTO categories VALUES(?, ?)', (i+1, category['name'],))
    conn.commit()


def populate_settings():
    for i, setting in enumerate(SETTINGS):
        cur.execute('INSERT OR IGNORE INTO settings VALUES(?, ?)', (i+1, setting,))
    conn.commit()


def register_user(username, hash, category_count):
    cur.execute('INSERT INTO users(username, hash) VALUES(?, ?)', (username, hash,))
    user_id = cur.lastrowid

    for i in range(category_count):
        cur.execute('INSERT INTO user_categories(user_id, category_id) VALUES(?, ?)', (user_id, i+1,))

    for i in range(len(SETTINGS)):
        cur.execute('INSERT INTO user_settings(user_id, setting_id) VALUES(?, ?)', (user_id, i+1,))

    conn.commit()


def delete_user(user_id):
    cur.execute('DELETE FROM users WHERE id == ?', (user_id,))
    cur.execute('DELETE FROM user_categories WHERE user_id == ?', (user_id,))
    conn.commit()


def get_user_categories(user_id):
    category_ids = cur.execute('SELECT category_id FROM user_categories WHERE user_id == ?', (user_id,)).fetchall()
    category_names = []
    for category_id in category_ids:
        category_names.append(cur.execute('SELECT category_name FROM categories WHERE id == ?', (category_id[0],)).fetchall()[0][0])
    return category_names


def remove_user_category(user_id, category_id):
    cur.execute('DELETE FROM user_categories WHERE user_id == ? AND category_id == ?', (user_id, category_id,))
    conn.commit()


def update_user_categories(user_id, category_names):  # seems to work, but test it a little bit more
    for category in categories:
        if category['name'] in category_names:
            category_id = cur.execute('SELECT id FROM categories WHERE category_name == ?', (category['name'],)).fetchall()
            cur.execute('INSERT OR IGNORE INTO user_categories VALUES(?, ?)', (user_id, category_id[0][0]))
        else:
            category_id = cur.execute('SELECT id FROM categories WHERE category_name == ?', (category['name'],)).fetchall()
            remove_user_category(user_id, category_id[0][0])
    conn.commit()


def get_user_setting(user_id, setting_name):
    setting_id = cur.execute('SELECT id FROM settings WHERE setting_name == ?', (setting_name,)).fetchall()[0][0]
    user_setting = cur.execute('SELECT * FROM user_settings WHERE user_id == ? AND setting_id == ?', (user_id, setting_id,)).fetchall()
    if len(user_setting) == 1:
        return True
    elif len(user_setting) == 0:
        return False
    else:
        raise Exception('Unexpected SQL query: user\'s setting is not unique')


conn = sqlite3.connect('users.db', check_same_thread=False)
create_tables()
cur = conn.cursor()
populate_categories()
populate_settings()
print('Database initialized')


