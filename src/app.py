#
# Web based GUI for the Lishex chess engine
# AB + MCTS variants
#
# Forked from a GUI for the BBC chess engine
# by Maksim Korzh
#

# packages
from flask import Flask
from flask import render_template
from flask import request
import chess
import chess.engine
import chess.pgn
import io
import random
from flask import jsonify
from flask import Response
from datetime import datetime
import json

# Engine path (we can switch between AB / MCTS / etc.)
ENGINE_PATH = r"./engine/lishex"

engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

# create web app instance
app = Flask(__name__)

# root(index) route
@app.route('/')
def root():
    return render_template('index.html')

# make move API
@app.route('/make_move', methods=['POST'])
def make_move():
    global engine
    # extract FEN string from HTTP POST request body
    pgn = request.form.get('pgn')
    
    # read game moves from PGN
    game = chess.pgn.read_game(io.StringIO(pgn))
    
    # init board
    board = game.board()
    
    # loop over moves in game
    for move in game.mainline_moves():
        # make move on chess board
        board.push(move)
    
    # create chess engine instance
    if not engine:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE)
    
    # extract fixed depth value
    fixed_depth = request.form.get('fixed_depth')

    # extract move time value
    move_time = request.form.get('move_time')
    
    # if move time is available
    if move_time != '0':
        if move_time == 'instant':
            try:
                # search for best move instantly
                info = engine.analyse(board, chess.engine.Limit(time=0.1))
            except:
                info = {}
        else:
            try:
                # search for best move with fixed move time
                info = engine.analyse(board, chess.engine.Limit(time=int(move_time)))
            except:
                info = {}

    # if fixed depth is available
    if fixed_depth != '0':
        try:
            # search for best move instantly
            info = engine.analyse(board, chess.engine.Limit(depth=int(fixed_depth)))
        except:
            info = {}
    
    # terminate engine process
    # engine.quit()
    
    try:
        # extract best move from PV
        best_move = info['pv'][0]

        # update internal python chess board state
        board.push(best_move)
        
        # get best score
        try:
            score = -int(str(info['score'])) / 100
        
        except:
            score = str(info['score'])
            
            # inverse score
            if '+' in score:
                score = score.replace('+', '-')
            
            elif '-' in score:
                score = score.replace('-', '+')
          
        return {
            'fen': board.fen(),
            'best_move': str(best_move),
            'score': score,
            'depth': info['depth'],
            'pv': ' '.join([str(move) for move in info['pv']]),
            'nodes': info['nodes'],
            'time': info['time']
        }
    
    except:
        return {
            'fen': board.fen(),
            'score': '#+1'
        }

@app.route('/analytics')
def analytics():
    return render_template('stats.html')

@app.route('/analytics/api/post', methods=['POST'])
def post():
    response = Response('')
    response.headers['Access-Control-Allow-Origin'] = '*'

    stats = {
        'Date': request.form.get('date'),
        'Url': request.form.get('url'),
        'Agent':request.headers.get('User-Agent')
    }

    if request.headers.getlist("X-Forwarded-For"):
       stats['Ip'] = request.headers.getlist("X-Forwarded-For")[0]
    else:
       stats['Ip'] = request.remote_addr
    
    if request.headers.get('Origin'):
        stats['Origin'] = request.headers.get('Origin')
    else:
        stats['Origin'] = 'N/A'
    
    if request.headers.get('Referer'):
        stats['Referer'] = request.headers.get('Referer')
    else:
        stats['Referer'] = 'N/A'
    
    with open('stats.json', 'a') as f: f.write(json.dumps(stats, indent=2) + '\n\n')
    return response


@app.route('/analytics/api/get')
def get():
    stats = []
    
    with open('stats.json') as f:
        for entry in f.read().split('\n\n'):
            try: stats.append(json.loads(entry))
            except: pass
              
    return jsonify({'data': stats})

# main driver
if __name__ == '__main__':
    # start HTTP server
    app.run(debug=True, threaded=True)
