import pymysql

mysql = pymysql.connect(host = 'localhost', password = '', database = 'Flask_Blog_app', user = 'root')

def exec_query(query, values = None):
    try:
        with mysql.cursor() as cursor:
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
            
            result  = cursor.fetchall()
            mysql.commit()
            return result
    except pymysql.Error as e:
        print(f"Error executing: {e}")
        mysql.ping(reconnect=True)
        return exec_query(query, values)