from flask import Flask, render_template, request, escape, session, copy_current_request_context
from vsearch import search4letters
from checker import check_logged_in
from DBcm import UseDataBase, ConnectionError, CredentialsError, SQLError
from threading import Thread
from time import sleep

app = Flask(__name__)

app.config['dbconfig'] = {'host': '127.0.0.1',
                          'user': 'vsearch',
                          'password': 'vsearchpasswd',
                          'database': 'vsearchlogDB',}

@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in.'

@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'You are now logged out.'

@app.route('/search4', methods=['POST'])
def do_search() -> 'html':
    @copy_current_request_context
    def log_request(req: 'flask_request', res: str) -> None:
        sleep(15)
        with UseDataBase(app.config['dbconfig']) as cursor:
            _SQL = """insert into log
                   (phrase, letters, ip, browser_string, results)
                   values
                   (%s, %s, %s, %s, %s)"""
            cursor.execute(_SQL, (req.form['phrase'],
                                  req.form['letters'],
                                  req.remote_addr,
                                  req.user_agent.browser,
                                  res, ))
    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are the results:'
    results = str(search4letters(phrase, letters))
    try:
        t = Thread(target=log_request, args=(request, results))
        t.start()
    except Exception as err:
        print('Logging failed with this error:', str(err))
    return render_template('results.html',
                           the_title = title,
                           the_phrase = phrase,
                           the_letters = letters,
                           the_results = results,)

@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html',
                           the_title='Welcome to search4letters on the web!')

@app.route('/viewlog')
@check_logged_in
def view_the_log() ->'html':
    try:
        with UseDataBase(app.config['dbconfig']) as cursor:
            _SQL = """select phrase, letters, ip, browser_string, results from log"""
            cursor.execute(_SQL)
            contents = []
            contents = cursor.fetchall()
            titles=('Phrase', 'Letters', 'Remote_addr', 'User_agent', 'Results')
            return render_template('viewlog.html',
                                   the_title='View Log',
                                   the_row_titles=titles,
                                   the_data=contents)
    except ConnectionError as error:
        print('Is your database switched on? Error: ', str(error))
    except CredentialsError as error:
        print('User-id/Password issue. Error: ', str(error))
    except SQLError as error:
        print('Is your query correct? Error: ', str(error))
    except Exception as error:
        print('Something went wrong: ', str(error))
    return 'Error'

app.secret_key = 'YouWillNeverGuessMySecretKey'

if __name__ == '__main__':
    app.run(debug=True)
