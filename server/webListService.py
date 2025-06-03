from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sys
import os
from dbService import cnnect_db
import sqlite3
import bcrypt
from register import record_exists
class WebListService:
    def getWebList(self):
        return GetWbebList()
    def addWeb(self,data):
        return AddWeb(data)
       




webListService=WebListService()
def GetWbebList():
    db=cnnect_db()
    cursor=db.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS webs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT ,
        URL  TEXT NOT NULL,
        info TEXT NOT NULL,
        is_approved INTEGER DEFAULT 0
        )
        '''
    )
    cursor.execute(
        '''
        SELECT id,name,type FROM webs WHERE is_approved=1
        '''
    )
    print("如果数据库不存在则创建数据库")
    data=cursor.fetchall()
    if data is not None:
        print("获取到了数据库数据：",data)
        db.close()
        result={"success":True,"webList":data}
        return result
    else:
        result={'success':False,"webList":{}}
        db.close()
        return result
    

def AddWeb(data):
    print("网站数据：",data)
    db=cnnect_db()
    cursor=db.cursor()
    cursor.execute(
        '''
        SELECT id FROM webs
        '''
    )
    base_id=0
    id=cursor.fetchall()
    print("原来的id",id)
    if not id:
        new_id = base_id
    else:
        new_id=id[-1][0]+1
    if record_exists(db,"webs","url",data['url']):
        db.close()
        print("网站已经存在")
        result={'success':False,'message':'网站已经存在'}
        return result
    cursor.execute(
        '''
        INSERT INTO webs(id,name,type,url,info) VALUES(?,?,?,?,?)
        ''',
        (new_id,data['name'],None,data['url'],data['info'])
    )
    if record_exists(db,"webs","url",data['url']):
        print("成功插入数据")
        result={'success':True,'message':'提交成功，等待管理员审核'}
        db.commit()
        db.close()
        return result
    else:
        print("插入数据失败")
        db.close()
        result={'success':False,'message':'提交失败'}
        return result
    
    
