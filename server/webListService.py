from flask import Flask, request, jsonify,g
from flask_cors import CORS
import sys
import os
from dbService import cnnect_db
import sqlite3
import bcrypt
from register import record_exists
from imageService import ImageService
imgservice= ImageService()
class WebListService:
    def getWebList(self):
        return GetWbebList()
    def addWeb(self,data):
        return AddWeb(data)
    def webRequestList(self):
        return WebRequestList()
    def approve(self,data):
        return ApproveWeb(data)
    def reject(self,data):
        return Reject(data)
    def delete(self,data):
        return Delete(data)




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
        is_approved INTEGER DEFAULT 0,
        is_create_index INTEGER DEFAULT 0,
        index_count INTEGER DEFAULT 0
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
    webList=[]
    if data is not None:
        print("获取到了数据库数据：",data)
        #将数据转化为字典
        for i in data:
            j={
            "id":i[0],
            "name":i[1],
            "type":i[2],

        }
            webList.append(j)
        db.close()
        result={"success":True,"webList":webList}
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
    
def WebRequestList():
    db=cnnect_db()
    cursor=db.cursor()
    cursor.execute(
        '''
        SELECT id,name,url,info FROM webs WHERE is_approved= ?
        ''',(0,)
    )
    data=cursor.fetchall()
    #转化为字典列表
    web_request_list=[]
    if  data is not None:
        for i in data:
                j={
                "id":i[0],
                "name":i[1],
                "url":i[2],
                "info":i[3],
            }
                web_request_list.append(j)
        print("获取到的数据：",web_request_list)
        result={'success':True,'webRequestList':web_request_list}
        db.close()
        return result
    else:
        result={'success':False,'webRequestList':web_request_list}
        db.close()
        return result
    
def ApproveWeb(data):
    #查看获取到的数据
    print("获取到的要更改的词条的数据:",data)
    db=cnnect_db()
    cursor=db.cursor()
    #建立索引
    result2=imgservice.reconstruct_index_base(name=data['name'],path_or_url=data['url'],max_imgs=300)
    print("建立索引的结果是：",result2)
    if not result2['success']:#如果建立索引失败
            db.close()
            return result2
    #修改数据
    cursor.execute(
        '''
        UPDATE webs set is_approved=?,type=?,is_create_index=?,index_count=? where url=?
        ''',(1,data['type'],1,result2['index_count'],data['url'])
    )
    #查询数据是否修改成功
    cursor.execute(
        '''
        SELECT *  FROM webs where url=? AND is_approved=?
        ''',(data['url'],1)
    )
    data2=cursor.fetchone()
    print("在数据库中查找是否修改成功，结果是：",data2)
    if data2:
        result={'success':True,'message':"审核通过"}
        db.commit()
        db.close()
        #接下来建立索引库
        return result
    else:
        result={'success':False,'message':"数据修改失败"}
        db.close()
        return result


def Reject(data):
    #查看获取到的数据
    print("获取到的要更改的词条的数据:",data)
    db=cnnect_db()
    cursor=db.cursor()
    #修改数据
    cursor.execute(
        '''
        DELETE FROM webs WHERE is_approved=? AND URL=?
        ''',(0,data['url'])
    )
    #查询数据是否修改成功
    cursor.execute(
        '''
        SELECT *  FROM webs where url=? AND is_approved=?
        ''',(data['url'],0)
    )
    data2=cursor.fetchone()
    print("在数据库中查找是否修改成功，结果是：",data2)
    if not data2:#修改成功时，查找返回的是空数据
        result={'success':True,'message':"拒绝请求成功"}
        db.commit()
        db.close()
        #拒绝则无需建立索引库
        return result
    else:
        result={'success':False,'message':"数据修改失败"}
        db.close()
        return result



def Delete(data):
     #查看获取到的数据
    print("获取到的要更改的词条的数据:",data)
    db=cnnect_db()
    cursor=db.cursor()
    #修改数据
    cursor.execute(
        '''
        DELETE FROM webs WHERE is_approved=? AND id=? AND name=?
        ''',(1,data['id'],data['name'])
    )
    #查询数据是否修改成功
    cursor.execute(
        '''
        SELECT *  FROM webs where id=? AND is_approved=? AND name=?
        ''',(data['id'],1,data['name'])
    )
    data2=cursor.fetchone()
    print("在数据库中查找是否修改成功，结果是：",data2)
    if not data2:#修改成功时，查找返回的是空数据
        result={'success':True,'message':"图源删除成功"}
        result2=imgservice.destroy_index_base(name=data['name'])
        if not result2['success']:#删除失败则返回相应的信息
            db.close()
            return result2
        db.commit()
        db.close()
        #删除需删除对应索引库索引库
        return result
    else:
        result={'success':False,'message':"删除失败，图源不存在或权限不足"}
        db.close()
        return result