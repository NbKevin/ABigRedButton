"""
Implements crawler related Flask view functions.

Kevin Ni, kevin.ni@nyu.edu.
"""

import sys
import threading
from pathlib import Path
from flask import Flask, render_template, request

from _a_big_red_button.crawler.controller import Wok
from _a_big_red_button.crawler.db import WokPersistentStorage, WokPersistentSession
from _a_big_red_button.crawler.db_meta import WokPersistentSessionMeta
from _a_big_red_button.support.select_file import select_file
from _a_big_red_button.crawler.export_script_helper import available_export_scripts, get_export_script
from _a_big_red_button.crawler.export_worker import WokPersistentSessionExportScriptThreadedRunner
from _a_big_red_button.support.response import good, bad
from _a_big_red_button.support.log import get_logger
from _a_big_red_button.support.configuration import get_config
from _a_big_red_button.crawler.db_search import search_in_all_sessions

# prepare logger
logger = get_logger('controller-front')


def poll_search_progress():
    if Wok().is_searching:
        return good(finished=False)
    if Wok().search_done:
        if Wok().search_went_wrong:
            what = Wok().search_what_went_wrong
            if what is None:
                return bad("search failed on unknown error, "
                           "check your search term and search again")
            return bad(f"search failed: {what}")
        return good(finished=True, result_count=Wok().search_result_count)
    return bad("cannot poll search progress: have you searched?")


def command_search():
    if not Wok().can_search:
        return bad("cannot search in this state: a search may be going on")

    # reset the search
    Wok().reset_search()
    logger.debug("search has been reset and you may search again")

    args = request.get_json(force=True)
    Wok().search(args['term'])
    return good()


def poll_crawling_progress():
    if Wok().is_crawling:
        return good(finished=Wok().crawling_progress,
                    total=Wok().crawling_total_count)
    if Wok().crawling_done:
        if Wok().crawling_went_wrong:
            return bad("crawling failed, consider reset and crawl again")
        return good(finished=-1,
                    total=Wok().crawling_total_count)  # all done
    return bad("cannot poll crawling progress in this state: "
               "have you started crawling?")


def command_crawl():
    if not Wok().can_crawl:
        return bad("cannot start crawling in this state: "
                   "either you have not searched or a crawler is working already")

    # reset crawler
    Wok().reset_crawl()
    logger.info("crawler has been reset and is ready to crawl again")

    # parse arguments
    args = request.get_json(force=True)
    start, end = int(args['start']), int(args['end'])
    year_start, year_end = int(args['year_start']), int(args['year_end'])
    if year_start <= 0 or year_end <= 0 or year_end < year_start:
        year_range = None
    else:
        year_range = range(year_start, year_end + 1)

    Wok().crawl(start, end, year_range)
    return good()


def command_reset():
    Wok().reset_all()
    if Wok().can_search:
        return good()
    return bad("reset failed, consider restarting the whole app")


# def select_crawler_export_file():
#     logger.debug(f"selecting crawler output file, "
#                  f"using python binary = {sys.executable}")
#     if not WokAnalyser().select_file():
#         return bad("cannot select crawler output")
#     return good(file_name=str(WokAnalyser().file.name),
#                 full_path=str(WokAnalyser().file))


def poll_available_persistent_sessions():
    persistent_manager = WokPersistentStorage()
    available_sessions = list(persistent_manager.all_sessions)

    return good(sessions=[{'term': session.term,
                           'collection_name': session.session_id,
                           'size': len(session),
                           'metadata': WokPersistentSessionMeta.find_by_session(session).dict_for_saving}
                          for session in available_sessions])


def drop_session():
    request_params = request.get_json(force=True)
    if 'sessionId' not in request_params:
        return bad("invalid session id or id not provided")
    session_id = request_params['sessionId']

    # drop session
    session = WokPersistentSession.find_by_session_id(session_id)
    if session is None:
        return bad(f"invalid session id: no session named {session_id} exists")

    # drop session metadata
    session_meta = WokPersistentSessionMeta.find_by_session(session)
    if session_meta is None:
        return bad(f"invalid session id: no session meta for session named {session_id} exists")

    try:
        if session.drop() and session_meta.drop():
            return good(term=session.term, id=session.session_id)
        return bad(f"cannot drop session(id={session_id}) or its metadata, "
                   f"consider manually patch the database")
    except Exception as e:
        return bad(f"error dropping session(id={session_id}): {e}, "
                   f"consider contacting the developer and "
                   f"manually patch the database")


def render_sessions_page():
    persistent_manager = WokPersistentStorage()
    available_sessions = persistent_manager.all_sessions

    return render_template('sessions.html',
                           sessions=({'session': session,
                                      'metadata': WokPersistentSessionMeta.find_by_session(session)} for
                                     session in available_sessions),
                           export_scripts=list(available_export_scripts()))


def export_session():
    # validate arguments phase 1
    parameters = request.get_json(force=True)
    if 'session_id' not in parameters or 'export_script' not in parameters:
        return bad("invalid request: "
                   "missing field 'session_id' or 'export_script'")
    session_id, export_script_name = parameters['session_id'], parameters['export_script']

    # validate arguments phase 2
    session = WokPersistentSession.find_by_session_id(session_id)
    if session is None:
        return bad(f"invalid request: "
                   f"no session with id={session_id}")
    export_script = get_export_script(export_script_name)
    if export_script is None:
        return bad(f"invalid request: "
                   f"no export script with name={export_script_name}")

    # request user to select the export file
    export_file = select_file('Select the export file',
                              ('SNA Export File', "*.csv"),
                              ('Any File', "*.*"))
    if export_file is None:
        return bad("cannot run the export because export file could not "
                   "be selected")

    # start the export process and respond to the client
    logger.info(f"started exporting session(id={session_id}) "
                f"with script(name={export_script_name})")
    export_threaded_runner = WokPersistentSessionExportScriptThreadedRunner(
        export_script,
        session,
        Path(export_file)
    )
    export_threaded_runner.daemon = True
    export_threaded_runner.start()
    return good(message="exporting now...")


def serve_crawler():
    if 'sessionId' in request.args:
        session_id = request.args['sessionId']
        session = WokPersistentSession.find_by_session_id(session_id)
        if session is None:
            logger.warning(f'no such session(id={session_id}), ignored')
            return render_template('crawler.html')

        return render_template('crawler.html', search_term=session.term)

    return render_template('crawler.html')


def serve_term_assembler():
    available_fields = [{'field': k, 'explanation': v} for k, v in get_config('crawler').search_fields.dict.items()]
    available_fields = sorted(available_fields, key=lambda s: s['explanation'])
    return render_template('term.html', available_fields=available_fields)


def find_all_data_about(name: str):
    result = search_in_all_sessions(name)
    return render_template('result.html', result=result, name=name)


def serve_search_index():
    return render_template('search_index.html')


def register_crawler_function(app: Flask):
    app.route('/command/search/', methods=['POST'])(command_search)
    app.route('/command/crawl/', methods=["POST"])(command_crawl)
    app.route('/command/reset/')(command_reset)
    app.route('/poll/crawl/')(poll_crawling_progress)
    app.route('/poll/search/')(poll_search_progress)
    app.route('/command/export/', methods=['POST'])(export_session)
    app.route('/poll/availablePersistentSessions/')(poll_available_persistent_sessions)
    app.route('/sessions/')(render_sessions_page)
    app.route('/command/dropSession/', methods=['POST'])(drop_session)
    app.route('/term/')(serve_term_assembler)
    app.route('/')(serve_crawler)
    app.route('/search/<string:name>/')(find_all_data_about)
    app.route('/search/')(serve_search_index)
