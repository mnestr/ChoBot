import psycopg2
import config


def db_insert_user(tg_id, chat_id, first_name, last_name, language_code, user_name):
    sql_exists = """SELECT tg_id FROM users WHERE tg_id=%s LIMIT 1;"""

    sql_insert = """INSERT INTO users(tg_id, chat_id, first_name, last_name, lang_code, user_name)
             VALUES(%s, %s, %s, %s, %s, %s);"""

    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()  # create a new cursor
        cur.execute(sql_exists, (tg_id,))
        tg_id_from_db = cur.fetchall()
        if not tg_id_from_db:
            cur = conn.cursor()
            cur.execute(sql_insert,
                        (tg_id, chat_id, first_name, last_name, language_code, user_name))  # execute the INSERT statement
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
        host=config.host, port=config.port, sslmode='require')
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


def insert_word(word, translation, prt_of_speach, meaning, examp, user_id):
    sql_check = """SELECT id FROM dictionary WHERE  word = %s and translation = %s and part_of_speach = %s"""
    sql_insert = """INSERT INTO dictionary(word, translation, part_of_speach, meaning, example, added_by_user_id)
             VALUES(%s, %s, %s, %s, %s, %s) 
             RETURNING id
             ;"""
    conn = psycopg2.connect(
        database="d4507rcebm77pe", user='yvobcmcbgkgweo',
        password='e88ed490b84655daef799b73606fadeb8bee8f41bf7f4b48654eb213c33fa71b',
        host='ec2-54-155-110-181.eu-west-1.compute.amazonaws.com', port='5432', sslmode='require')
    try:
        cur = conn.cursor()  # create a new cursor
        cur.execute(sql_check, (word, translation, prt_of_speach))
        word_id = cur.fetchone()
        if word_id:
            return word_id[0]
        elif not word_id:
            cur.execute(sql_insert, (word, translation, prt_of_speach, meaning, examp, user_id))
            conn.commit()  # commit the changes to the database
            word_id = cur.fetchone()
            cur.close()  # close communication with the database
            conn.close()
            return word_id[0]
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_new_words_from_dictionary(user_id):
    sql_1 = """select d.id, d.word, d.translation from user_dictionary ud 
                left join dictionary d on ud.word_id = d.id 
                where ud.status = 'to_learn' and ud.user_id = %s and d.stopwords = 0;"""

    sql_2 = """SELECT d.id, d.word, d.translation FROM dictionary d
            LEFT JOIN (select word_id from user_dictionary where user_id = %s) ud
            ON d.id = ud.word_id
            WHERE ud.word_id IS NULL and d.translation is not NULL and stopwords = 0;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql_1, (user_id,))
        ids_words = cur.fetchall()
        if ids_words:
            return ids_words
        elif not ids_words:
            cur = conn.cursor()
            cur.execute(sql_2, (user_id,))
            ids_words = cur.fetchall()
            cur.close()
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
        host=config.host, port=config.port, sslmode='require')
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


def get_repetition(user_id):
    sql = """SELECT t.word_id, t.word, t.translation  from (
                SELECT *, now() - updated_at as timediff from user_dictionary as ud 
                LEFT JOIN dictionary as d ON ud.word_id = d.id) as t
                where (t.repetition = 0 or
                t.repetition = 1 and timediff > interval '15 minutes' or
                t.repetition = 1 and timediff > interval '1 hour' or
                t.repetition = 2 and timediff > interval '6 hour' or
                t.repetition = 3 and timediff > interval '1 day' or
                t.repetition = 4 and timediff > interval '1 day' or
                t.repetition = 5 and timediff > interval '2 day' or
                t.repetition = 6 and timediff > interval '3 day' or
                t.repetition = 7 and timediff > interval '5 day' or
                t.repetition = 8 and timediff > interval '7 day' or
                t.repetition = 9 and timediff > interval '14 day' or
                t.repetition = 10 and timediff > interval '1 month'
                ) and t.status not in ('already_know', 'to_learn') and t.user_id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
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


def get_notify_list():
    sql = """SELECT t.user_id, t.chat_id, count(t.word_id), MAX(t.updated_at), t.notifications_count, 
                t.last_notification_at  from (
                SELECT ud.user_id, ud.word_id, ud.updated_at, ud.repetition, ud.status,
                u.chat_id, u.notifications_count, u.last_notification_at, 
                now() - updated_at as timediff from user_dictionary as ud 
                LEFT JOIN dictionary as d ON ud.word_id = d.id
                LEFT JOIN users as u ON ud.user_id = u.id) as t
                where (t.repetition = 0 or
                t.repetition = 1 and timediff > interval '15 minutes' or
                t.repetition = 2 and timediff > interval '6 hour' or
                t.repetition = 3 and timediff > interval '1 day' or
                t.repetition = 4 and timediff > interval '2 day' or
                t.repetition = 5 and timediff > interval '5 day' or
                t.repetition = 6 and timediff > interval '7 day' or
                t.repetition = 7 and timediff > interval '14 day' or
                t.repetition = 8 and timediff > interval '1 month'
                ) and t.status NOT IN ('already_know', 'to_learn')
                group by t.user_id, t.chat_id, t.notifications_count, t.last_notification_at;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql)
        notify_list = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        return notify_list
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def count_notification(user_id):
    sql = """SELECT notifications_count FROM users where id = %s;"""
    sql_update = """UPDATE users
                    SET notifications_count = %s, last_notification_at = now()
                    WHERE id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql,(user_id,))
        counter = cur.fetchall()
        n = counter[0][0]
        n += 1
        cur = conn.cursor()
        cur.execute(sql_update,(n, user_id))
        conn.commit()
        cur.close()  # close communication with the database
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_descr_from_dict(id):
    sql = """SELECT word, translation, part_of_speach, meaning, example FROM dictionary where id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql,(id,))
        word_dscr = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        return word_dscr[0]
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def upsert_word_user_dict(user_id, word_id, status, user_word_description=None, added_by_user=0):
    sql_upsert = """INSERT INTO user_dictionary (user_id, word_id, status, user_word_description, added_by_user)
                    VALUES(%s, %s, %s, %s, %s) 
                    ON CONFLICT (user_id, word_id) 
                    DO UPDATE SET status = EXCLUDED.status;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()  # create a new cursor
        cur.execute(sql_upsert, (user_id, word_id, status, user_word_description, added_by_user))
        conn.commit()  # commit the changes to the database
        cur.close()  # close communication with the database
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_user_descr(word_id):
    sql = """SELECT user_word_description FROM user_dictionary where word_id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql,(word_id,))
        user_word_description = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        return user_word_description
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
    sql_update_status = """UPDATE user_dictionary
                    SET status = %s
                    WHERE user_id = %s and word_id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql,(word_id, user_id,))
        repetition = cur.fetchall()
        n = repetition[0][0]
        if count == "+1":
            if n < 8:
                n += 1
                cur = conn.cursor()
                cur.execute(sql_update, (n, user_id, word_id))
                conn.commit()
                cur.close()  # close communication with the database
                conn.close()
            elif n >= 8:
                cur = conn.cursor()
                cur.execute(sql_update_status, ('mastered', user_id, word_id))
                conn.commit()
                cur.close()  # close communication with the database
                conn.close()
        elif count == "-1":
            if n > 0:
                n -= 1
                cur = conn.cursor()
                cur.execute(sql_update,(n, user_id, word_id))
                conn.commit()
                cur.close()  # close communication with the database
                conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def find_word_in_dict(word):
    sql = """SELECT id FROM dictionary where word = %s and translation IS NOT NULL and meaning IS NOT NULL;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql,(word,))
        word_id = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        if word_id:
            return word_id[0][0]
        elif not word_id:
            return None
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def check_if_word_in_user_dict(word_id):
    sql = """SELECT user_id FROM user_dictionary where word_id = %s;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql,(word_id,))
        id = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        if id:
            return id[0][0]
        elif not id:
            return None
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_statistics(user_id):
    sql = """SELECT status, count(word_id) FROM user_dictionary where user_id = 46 group by status;"""
    conn = psycopg2.connect(
        database=config.database, user=config.user,
        password=config.password,
        host=config.host, port=config.port, sslmode='require')
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        response = cur.fetchall()
        cur.close()  # close communication with the database
        conn.close()
        statistics = {"already_know": 0, 'to_learn': 0, 'mastered': 0, 'repetition': 0}
        if response:
            for i in response:
                statistics[i[0]] = i[1]
            return statistics
        elif not response:
            return statistics
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
