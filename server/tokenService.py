from custom_token import isUser
class TokenService:
    def IsUser(self,token):
        return isUser(token)
tokenService=TokenService()