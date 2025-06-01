from login import login
from register import register
class Auth:
    def Login(self,userId,password):
        return login(userId,password)
    def Register(self,userId,password):
        return register(userId,password)
auth=Auth()