import psycopg2
import config


def db_insert_user(tg_id, first_name, last_name, language_code, user_name):
    sql_exists = """SELECT tg_id FROM users WHERE tg_id=%s LIMIT 1;"""

    sql_insert = """INSERT INTO users(tg_id, first_name, last_name, lang_code, user_name)
             VALUES(%s, %s, %s, %s, %s);"""

    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()  # create a new cursor
        cur.execute(sql_exists, (tg_id,))
        tg_id_from_db = cur.fetchall()
        if tg_id_from_db == []:
            cur = conn.cursor()
            cur.execute(sql_insert,
                        (tg_id, first_name, last_name, language_code, user_name))  # execute the INSERT statement
            conn.commit()  # commit the changes to the database
            cur.close()  # close communication with the database
        else:
            conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_user_id(tg_id):
    sql = """SELECT id FROM users where tg_id = %s;"""

    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )

    try:
        cur = conn.cursor()
        cur.execute(sql,(tg_id,))
        user_id = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        if not user_id:
            return user_id
        else:
            return user_id[0][0]
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_new_words_from_dictionary(user_id):
    sql = """SELECT d.id, d.word, d.translation FROM dictionary d
            LEFT JOIN (select word_id from user_dictionary where user_id = %s) ud
            ON d.id = ud.word_id
            WHERE ud.word_id IS NULL;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        ids_words = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        return ids_words
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_words_from_dictionary():
    sql = """SELECT id, word FROM dictionary;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()
        cur.execute(sql)
        words_from_dictionary = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return words_from_dictionary


def get_user_dictionary(user_id):
    sql = """SELECT word_id FROM user_dictionary where user_id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()
        cur.execute(sql,(user_id,))
        user_dictionary_from_db = cur.fetchall()
        user_dictionary =[]
        for x in user_dictionary_from_db:
            for y in x:
                user_dictionary.append(y)
        cur.close()  # close communication with the database
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return user_dictionary


def get_repetition(user_id):
    sql = """SELECT d.id, d.word, d.translation  from (
                SELECT *, now() - updated_at as timediff from user_dictionary
            ) as ud 
            LEFT JOIN dictionary as d 
            ON ud.word_id = d.id
            where (
                repetition = 0 or
                repetition = 1 and timediff> cast('15 minutes' as interval) or
                repetition = 2 and timediff> cast('6 hour' as interval) or
                repetition = 3 and timediff> cast('1 day' as interval) or
                repetition = 4 and timediff> cast('2 day' as interval) or
                repetition = 5 and timediff> cast('5 day' as interval) or
                repetition = 6 and timediff> cast('7 day' as interval) or
                repetition = 7 and timediff> cast('14 day' as interval) or
                repetition = 8 and timediff> cast('1 month' as interval)
            )and status != 'already_know' and user_id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()
        cur.execute(sql,(user_id,))
        repetition = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        return repetition
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_tr_word_by_id(id):
    sql = """SELECT translation FROM dictionary where id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()
        cur.execute(sql,(id,))
        tr_word = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return tr_word[0][0]


def insert_word(user_id, word_id, status):
    sql_exists = """SELECT word_id FROM user_dictionary WHERE word_id=%s LIMIT 1;"""

    sql_insert = """INSERT INTO user_dictionary(user_id, word_id, status)
             VALUES(%s, %s, %s);"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()  # create a new cursor
        cur.execute(sql_exists, (word_id,))
        check_word_id = cur.fetchall()
        if not check_word_id:
            cur = conn.cursor()
            cur.execute(sql_insert, (user_id, word_id, status))  # execute the INSERT statement
            conn.commit()  # commit the changes to the database
            cur.close()  # close communication with the database
            conn.close()
        else:
            conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def count_repetition(word_id, user_id, count):
    sql = """SELECT repetition FROM user_dictionary where word_id = %s and user_id = %s;"""
    sql_update = """UPDATE user_dictionary
                    SET repetition = %s
                    WHERE user_id = %s and word_id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require'
    )
    try:
        cur = conn.cursor()
        cur.execute(sql,(word_id, user_id,))
        repetition = cur.fetchall()
        n = repetition[0][0]
        if count == "+1":
            if n < 8:
                n += 1
                cur = conn.cursor()
                cur.execute(sql_update,(n, user_id, word_id))
                conn.commit()
                cur.close()  # close communication with the database
                conn.close()
        elif count == "-1":
            if n > 0:
                n -= 1
                cur = conn.cursor()
                cur.execute(sql_update,(n, word_id, user_id))
                conn.commit()
                cur.close()  # close communication with the database
                conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

