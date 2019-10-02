
import os 
import logging 
import wsgiref.handlers
import webapp2
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from util.sessions import Session


def doRender(handler,path='index.html', values={}):
   temp = os.path.join(os.path.dirname(__file__),'templates/'+path)
   if not os.path.isfile(temp):
    logging.info('temp='+temp) 
    temp = os.path.join(os.path.dirname(__file__),'templates/index.html')
   logging.info('temp='+temp) 
   # Make a copy and add the path
   newval= dict(values)
   newval['path'] = handler.request.path
   outstr = template.render(temp,newval)
   handler.response.out.write(outstr)
   return True  

class MainHandler(webapp2.RequestHandler):
  def get(self):
   path = self.request.path 
   logging.info('path=' + path);
   try:
    self.session = Session()
    doRender(self,path,{'username':self.session['username']})
   except:
    doRender(self,path)


class User(db.Model):
 acct = db.StringProperty() 
 pw = db.StringProperty() 
 name = db.StringProperty() 

class LoginHandler(webapp2.RequestHandler):
  def get(self):
    doRender(self,'loginscreen.htm')

  def post(self):
     self.session= Session()
     acct = self.request.get('account')
     pw = self.request.get('password')
     logging.info('Checking account='+acct+'pw='+pw)
     que = db.Query(User).filter('acct =',acct).filter('pw =',pw)
     results = que.fetch(limit=1)
     self.session.delete_item('username')
     if pw==''or acct=='':
        doRender(
        self,
        'loginscreen.htm',
        {'error':'Specify Acct and PW'})
     elif len(results)>0:
        user = results[0]
        self.session['username'] = acct
        self.session['userkey'] = user.key()
        doRender(self,'loggedin.htm',{'username':self.session['username']})
     else:
       doRender(
         self,
         'loginscreen.htm',
         {'error':'Incorrect login data'})

class LogoutHandler(webapp2.RequestHandler):
    
  def get(self):
    self.session = Session()
    self.session.delete_item('username')
    self.session.delete_item('userkey')
    doRender(self,'index.html')

class ApplyHandler(webapp2.RequestHandler):
  def get(self):
    doRender(self,'apply.htm')

  def post(self):
    self.session = Session()
    xname = self.request.get('name')
    xacct = self.request.get('account') 
    xpw = self.request.get('password')

    # Check for a user already existing
    que = db.Query(User).filter('acct =',xacct)
    results = que.fetch(limit=1)
    
    if len(results) > 0:
      doRender(self,'apply.htm',{'error':'Account Already Exists'})
      return

    newuser = User(name=xname, acct=xacct, pw=xpw);
    key = newuser.put();
    self.session['username'] = xacct
    self.session['userkey'] = key
    doRender(self,'loggedin.htm',self.session)

class MembersHandler(webapp2.RequestHandler):

  def get(self):
   self.session = Session()
   que = db.Query(User)
   user_list = que.fetch(limit=100)
   newval=dict({})
   newval['username'] = self.session['username']
   doRender(self,'memberscreen.htm',newval)   

class ChatMessage(db.Model):
 user = db.ReferenceProperty()
 text = db.StringProperty()
 created = db.DateTimeProperty(auto_now=True)

class ChatHandler(webapp2.RequestHandler):

 def get(self):  
  que = db.Query(ChatMessage).order('-created')
  chat_list = que.fetch(limit=10)
  doRender(self,'chatscreen.htm')

 def post(self):
  self.session = Session()
  msg = self.request.get('message')
  newchat = ChatMessage(user = self.session['userkey'],text=msg)
  newchat.put();

  que = db.Query(ChatMessage).order('-created')
  chat_list = que.fetch(limit=10)
  doRender(self,'chatscreen.htm',{'chat_list':chat_list})

class MessagesHandler(webapp2.RequestHandler):

 def get(self):
  que=db.Query(ChatMessage).order('-created');
  chat_list=que.fetch(limit=100)
  doRender(self,'messages.htm',{'chat_list':chat_list})


app = webapp2.WSGIApplication([
  ('/memberscreen.htm', MembersHandler),
  ('/login', LoginHandler),
  ('/logout',LogoutHandler),
  ('/apply',ApplyHandler),
  ('/chatscreen.htm',ChatMessage),
  ('/messages.htm',MessagesHandler),
  ('/picture.html',MainHandler),
  ('/light.html',MainHandler),
  ('/intro.html',MainHandler),  
  ('/loggedin.htm',MainHandler),
  ('/apply.htm',MainHandler),
  (r'/.*', MainHandler)],
  debug=True)


