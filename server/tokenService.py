from custom_token import isUser
from dbService import cnnect_db
class TokenService:
    def IsUser(self,token):
        return isUser(token)
    def isAdmin(self,token):
        return IsAdmin(token)
tokenService=TokenService()

def IsAdmin(token):
    print("token的数据是:",token)
    if not token:  # 如果 Token 为空，直接返回 False
        print("token验证失败,token是空的")
        return False
    db=cnnect_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT * FROM users WHERE token = ?And role=?
        """,(token,'admin')
    )
    data = cursor.fetchone()
    if data is not None:
        print("token验证成功")
        return True
    else:
        print("token验证失败")
        return False
