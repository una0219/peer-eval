# -*- coding: utf-8 -*-
"""
互评系统后端 — Flask + SQLite
运行: python server.py
访问: http://localhost:5000
"""

import sqlite3
import os
from flask import Flask, request, jsonify, g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

DATABASE = os.path.join(BASE_DIR, 'scores.db')

# ──────────────────── 数据库 ────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            rater_id    TEXT NOT NULL,
            target_id   TEXT NOT NULL,
            score       INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
            PRIMARY KEY (rater_id, target_id)
        )
    ''')
    db.commit()
    db.close()

# ──────────────────── 路由 ────────────────────

@app.route('/')
def index():
    with open(os.path.join(BASE_DIR, 'index.html'), 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/api/scores', methods=['GET'])
def get_all_scores():
    """获取全部评分数据，按评分人分组返回"""
    db = get_db()
    rows = db.execute('SELECT rater_id, target_id, score FROM scores ORDER BY rater_id, target_id').fetchall()
    result = {}
    for row in rows:
        if row['rater_id'] not in result:
            result[row['rater_id']] = {}
        result[row['rater_id']][row['target_id']] = row['score']
    return jsonify(result)


@app.route('/api/scores/<rater_id>', methods=['GET'])
def get_rater_scores(rater_id):
    """获取某人的评分记录（用于回填）"""
    db = get_db()
    rows = db.execute('SELECT target_id, score FROM scores WHERE rater_id = ?', [rater_id]).fetchall()
    result = {}
    for row in rows:
        result[row['target_id']] = row['score']
    return jsonify(result)


@app.route('/api/scores', methods=['POST'])
def save_scores():
    """保存/覆盖评分 { rater_id: str, scores: { target_id: int, ... } }"""
    data = request.get_json(force=True)
    rater_id = data.get('rater_id', '').strip()
    scores = data.get('scores', {})

    if not rater_id:
        return jsonify({'error': '缺少 rater_id'}), 400
    if not scores:
        return jsonify({'error': '缺少 scores'}), 400

    db = get_db()
    for target_id, score in scores.items():
        if not isinstance(score, int) or score < 0 or score > 100:
            return jsonify({'error': f'{target_id} 分数无效: {score}'}), 400
        db.execute(
            'INSERT OR REPLACE INTO scores (rater_id, target_id, score) VALUES (?, ?, ?)',
            [rater_id, target_id, score]
        )
    db.commit()
    return jsonify({'ok': True})


if __name__ == '__main__':
    init_db()
    print('互评系统已启动: http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
