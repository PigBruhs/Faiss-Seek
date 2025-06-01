from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sys
import os
import sqlite3


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cnnect_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'database.db')
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db