from tornado.web import Application, RequestHandler, HTTPError
from tornado.ioloop import IOLoop
from tornado.options import define, options
from pymongo import MongoClient
from bson.json_util import loads
import tornado.web
import tornado.escape

define('port', default=8888, help="A port the server is running on", type=int)


class BaseHandler(RequestHandler):
	def set_default_headers(self):
		self.set_header('Access-Control-Allow-Origin', '*')
		self.set_header('Access-Control-Allow-Headers', '*')
		self.set_header('Access-Control-Max-Age', 1000)
		self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
		self.set_header('Access-Control-Allow-Headers',
                    'Content-Type, Access-Control-Allow-Origin, Access-Control-Allow-Headers, X-Requested-By, Access-Control-Allow-Methods')

	def initialize(self):
		self.db = self.settings['db']
		self.collection = self.db['authen']
		self.data = self.db['user']
		x=self.collection.index_information()
		if len(x)==1:
			self.collection.create_index("email", unique=True)

		# self.messsage=""

	def get_current_user(self):
		return self.get_secure_cookie('client')

	def get(self):
		self.render("index.html")

class SignUpHandler(BaseHandler):
	def get(self):
		self.render("signup.html")
	def post(self):
		username = self.get_argument("username")
		password = self.get_argument("password")
		email = self.get_argument("email")
		signup_data = {
            "username": username,
            "password": password,
            "email": email
        }
		# print(signup_data)
		try:
			self.collection.insert_one(signup_data)
		except Exception as e:
			# self.message = "The email already exists in the databse. Please use another \
    		# 				email address to sign up..."
			self.redirect("/signup")
		# self.message = "You have successfully created an account with us!"
		self.redirect('/')


class LoginHandler(BaseHandler):
	def get(self):
		self.render("login.html")

	def post(self):
		email = self.get_argument("email")
		password = self.get_argument("password")
		login_data = self.collection.find_one({"email": email})
		# print(login_data)
		if password==login_data["password"]:
			self.set_secure_cookie("client", self.get_argument("email"))
			self.redirect("/users")
		else:
			# self.message = "The login credentials are incorrect. Please login again..."
			self.redirect("/login")


class LogoutHandler(BaseHandler):
	def get(self):
		self.clear_cookie("client")
		# self.message = "Successfully logged out..."
		self.redirect(self.get_argument("next", self.reverse_url("home")))


class NonIdHandler(BaseHandler):
	@tornado.web.authenticated
	def get(self):
		email = tornado.escape.xhtml_escape(self.current_user)
		self.write("Hello, "+email)
		users_data = self.data.find().sort([("id", -1)]).limit(5)
		self.render("home.html", users=users_data)

	@tornado.web.authenticated
	def post(self):
		fName = self.get_argument("firstname")
		lName = self.get_argument("lastname")
		user_d = self.data.find().sort([("id", -1)]).next()
		id = user_d["id"]+1
		user_data = {
			"id": id,
			"fName": fName,
			"lName": lName
		}
		self.data.insert_one(user_data)
		self.redirect("/users")


if __name__=='__main__':
    cursor = MongoClient('mongodb://localhost:27017')
    settings = {
        "cookie_secret": "asildh#osafo/awdEEWIFaesRwkW=",
        "login_url": "/login",
        "db": cursor['test'],
        "xsrf_form_html": True,
        "xsrf_cookies": True
    }
    application = Application([
        tornado.web.url(r"/", BaseHandler, name="home"),
        tornado.web.url(r"/signup", SignUpHandler, name="signup"),
        tornado.web.url(r"/login", LoginHandler, name="login"),
		tornado.web.url(r"/logout", LogoutHandler, name="logout"),
		tornado.web.url(r"/users", NonIdHandler, name="main"),
    ], **settings)

    application.listen(options.port)
    print("Listening on port {}".format(options.port))
    IOLoop.current().start()
