import bottle

import cgi
import re
import datetime
import user
import sys

from pymongo import MongoClient

connection = MongoClient('localhost', 27017)

@bottle.route('/')
def blog_index():
    username = login_check()

    db = connection.blog
    posts = db.posts
    cursor = posts.find().sort('date', direction=-1).limit(10)
    l = []
    for post in cursor:
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")  # formatando data
        if 'tags' not in post:
            post['tags'] = []  # preenche vazio
        if 'comments' not in post:
            post['comments'] = []
        if 'category' not in post:
            post['category'] = ''
        if 'permalink_category' not in post:
            post['permalink_category'] = ''
        l.append(
            {'title': post['title'], 'body': post['body'], 'post_date': post['date'], 'permalink': post['permalink'],
             'tags': post['tags'], 'author': post['author'], 'category': post['category'],
              'permalink_category': post['permalink_category'], 'comments': post['comments']})
        print post['title']

    return bottle.template('blog_template', dict(myposts=l, username=username))


@bottle.get('/newpost')
def get_newpost():
    username = login_check()
    db = connection.blog
    cate_coll = db.categorys
    cursor = cate_coll.find().sort('category', direction=-1)
    cate_array = []
    for cate in cursor:
        cate_array.append(dict(id=cate['permalink'], name=cate['category']))

    return bottle.template("newpost_template", dict(subject="", body="", errors="", tags="", categorys=cate_array,username=username))


@bottle.get('/newcategory')
def get_newcategory():
    username = login_check()

    return bottle.template("newcategory_template", dict(errors="",username=username))


@bottle.post('/newcategory')
def post_newcategory():
    category = bottle.request.forms.get("category")

    if category == "":
        errors = "Category must have a name"
        return bottle.template("newcategory_template", dict(errors=errors))

    permalink = insert_category(category)

    # redireciona para post criado
    # bottle.redirect("/category/" + permalink)
    bottle.redirect("/newcategory")


@bottle.post('/newpost')
def post_newpost():
    username = login_check()

    title = bottle.request.forms.get("subject")
    post = bottle.request.forms.get("body")
    tags = bottle.request.forms.get("tags")
    category = bottle.request.forms.get("category")

    if title == "" or post == "":
        errors = "Post must contain a title and blog entry"
        return bottle.template("newpost_template", dict(subject=cgi.escape(title, quote=True),
                                                        body=cgi.escape(post, quote=True), tags=tags, errors=errors))

    # Extraindo  tags
    tags = cgi.escape(tags)
    tags_array = extract_tags(tags)

    # Entrada de dados, insira SCAPE
    escaped_post = cgi.escape(post, quote=True)

    # substituir alguns <p> para as quebras de paragrafo
    newline = re.compile('\r?\n')
    formatted_post = newline.sub("<p>", escaped_post)

    permalink = insert_entry(title, formatted_post, tags_array, username, category)

    # redireciona para post criado
    bottle.redirect("/post/" + permalink)


def insert_category(category):
    print "inserindo categorias no blog", category

    db = connection.blog
    categorys = db.categorys

    exp = re.compile('\W')  # combinar qualquer coisa que nao alfanumerico
    whitespace = re.compile('\s')
    temp_category = whitespace.sub("_", category)
    permalink = exp.sub('', temp_category)

    category = {"category": category,
                "permalink": permalink,
                "date": datetime.datetime.utcnow()}

    try:
        categorys.insert(category)
        print "Inserido category"

    except:
        print "Erro ao inserir category"
        print "Erros inesperado:", sys.exc_info()[0]

    return permalink


# insere a entrada de dados do blog e retorna um permalink
def insert_entry(title, post, tags_array, author, category):
    print "inserindo entrada de dados no blog", title, post

    db = connection.blog
    posts = db.posts

    exp = re.compile('\W')  # combinar qualquer coisa que nao alfanumerico
    whitespace = re.compile('\s')
    temp_title = whitespace.sub("_", title)
    temp_category = whitespace.sub("_", category)
    permalink = exp.sub('', temp_title)
    permalink_category = exp.sub('', temp_category)

    post = {"title": title,
            "author": author,
            "body": post,
            "permalink": permalink,
            "tags": tags_array,
            "category": category,
            "permalink_category": permalink_category,
            "date": datetime.datetime.utcnow()}

    try:
        posts.insert(post)
        print "Inserido post"

    except:
        print "Erro ao inserir post"
        print "Erros inesperado:", sys.exc_info()[0]

    return permalink


def extract_tags(tags):
    whitespace = re.compile('\s')
    nowhite = whitespace.sub("", tags)
    tags_array = nowhite.split(',')

    # limpando
    cleaned = []
    for tag in tags_array:
        if (tag not in cleaned and tag != ""):
            cleaned.append(tag)

    return cleaned


# chamado tanto para os requests regulares e requests JSON
@bottle.get("/post/<permalink>")
def show_post(permalink="notfound"):
    username = login_check()
    db = connection.blog
    posts = db.posts

    permalink = cgi.escape(permalink)

    # determina requisica do json
    path_re = re.compile(r"^([^\.]+).json$")

    print "about to query on permalink = ", permalink
    post = posts.find_one({'permalink': permalink})

    if not post:
        bottle.redirect("/post_not_found")

    print "date of entry is ", post['date']

    # Formata Data
    post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")

    # inicializacao dos campos do formulario  para adicionar de comentarios
    comment = {}
    comment['name'] = ""
    comment['email'] = ""
    comment['body'] = ""

    return bottle.template("entry_template", dict(post=post, username=username, errors="", comment=comment))

# chamado tanto para os requests regulares e requests JSON
@bottle.get("/category/<tag>")
def show_category(tag="notfound"):
    username = login_check()
    db = connection.blog
    posts = db.posts

    tag = cgi.escape(tag)
    cursor = posts.find({'permalink_category': tag}).sort('date', direction=-1)
    l = []

    for post in cursor:
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")
        if ('tags' not in post):
            post['tags'] = []
        if ('comments' not in post):
            post['comments'] = []
        if ('category' not in post):
            post['category'] = ''
        if ('permalink_category' not in post):
            post['permalink_category'] = ''

        l.append({'title': post['title'], 'body': post['body'], 'post_date': post['date'],
                  'permalink': post['permalink'],
                  'tags': post['tags'],
                  'author': post['author'],
                  'category': post['category'],
                  'author': post['author'],
                  'permalink_category': post['permalink_category']})

    return bottle.template('blog_template', dict(myposts=l, username=username))

# usado para processar um comentario em um post de blog
@bottle.post('/newcomment')
def post_newcomment():
    name = bottle.request.forms.get("commentName")
    email = bottle.request.forms.get("commentEmail")
    body = bottle.request.forms.get("commentBody")
    permalink = bottle.request.forms.get("permalink")

    db = connection.blog
    posts = db.posts

    permalink = cgi.escape(permalink)

    post = posts.find_one({'permalink': permalink})

    if post == None:
        bottle.redirect("/post_not_found")

    errors = ""
    if name == "" or body == "":

        # Formata data
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")

        # Inicializa Comentarios
        comment = {}
        comment['name'] = name
        comment['email'] = email
        comment['body'] = body

        errors = "Post must contain your name and an actual comment."
        print "newcomment: comment contained error..returning form with errors"
        return bottle.template("entry_template", dict(post=post, username="indefinido", errors=errors, comment=comment))
    else:
        comment = {}
        comment['author'] = name
        if (email != ""):
            comment['email'] = email
            comment['body'] = body

    try:

        last_error = posts.update({'permalink': permalink}, {'$push': {'comments': comment}}, upsert=False)

        print "about to update a blog post with a comment"

    except:
        print "Could not update the collection, error"
        print "Unexpected error:", sys.exc_info()[0]
        print "newcomment: added the comment....redirecting to post"

    bottle.redirect("/post/" + permalink)


@bottle.get("/post_not_found")
def post_not_found():
    return "Desculpe, post nao encontrado"


@bottle.route('/tag/<tag>')
def posts_by_tag(tag="notfound"):
    username = login_check()
    db = connection.blog
    posts = db.posts

    tag = cgi.escape(tag)
    cursor = posts.find({'tags': tag}).sort('date', direction=-1)
    l = []

    for post in cursor:
        post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")
        if ('tags' not in post):
            post['tags'] = []
        if ('comments' not in post):
            post['comments'] = []
        if ('category' not in post):
            post['category'] = ''
        if ('permalink_category' not in post):
            post['permalink_category'] = ''

        l.append({'title': post['title'], 'body': post['body'], 'post_date': post['date'],
                  'permalink': post['permalink'],
                  'tags': post['tags'],
                  'author': post['author'],
                  'category': post['category'],
                  'author': post['author'],
                  'permalink_category': post['permalink_category']})

    return bottle.template('blog_template', dict(myposts=l, username=username))


@bottle.get('/signup')
def present_signup():
    return bottle.template("signup",
                           dict(username="", password="",
                                password_error="",
                                email="", username_error="", email_error="",
                                verify_error=""))


@bottle.post('/signup')
def process_signup():
    email = bottle.request.forms.get("email")
    username = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")
    verify = bottle.request.forms.get("verify")

    errors = {'username': cgi.escape(username), 'email': cgi.escape(email)}
    if user.validate_signup(username, password, verify, email, errors):
        if not user.newuser(connection, username, password, email):
            # trata duplicados
            errors['username_error'] = "Username already in use. Please choose another"
            return bottle.template("signup", errors)

        session_id = user.start_session(connection, username)
        print session_id
        cookie = user.make_secure_val(session_id)
        bottle.response.set_cookie("session", cookie)
        bottle.redirect("/welcome")
    else:
        print "user did not validate"
        return bottle.template("signup", errors)


@bottle.get("/welcome")
def present_welcome():
    # check for a cookie, if present, then extract value

    username = login_check()
    if not username:
        print "welcome: can't identify user...redirecting to signup"
        bottle.redirect("/signup")

    return bottle.template("welcome", {'username': username})


def login_check():
    # connection = pymongo.Connection(connection_string, safe=True)

    cookie = bottle.request.get_cookie("session")

    if cookie == None:
        print "no cookie..."
        return None
    else:
        session_id = user.check_secure_val(cookie)

        if (session_id == None):
            print "no secure session_id"
            return None

        else:
            # look up username record
            session = user.get_session(connection, session_id)
            if not session:
                return None

        return session['username']


@bottle.get('/login')
def present_login():
    return bottle.template("login",
                           dict(username="", password="",
                                login_error=""))


@bottle.post('/login')
def process_login():
    username = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")

    print "user submitted ", username, "pass ", password

    userRecord = {}
    if user.validate_login(connection, username, password, userRecord):
        session_id = user.start_session(connection, username)
        if session_id == -1:
            bottle.redirect("/internal_error")

        cookie = user.make_secure_val(session_id)

        bottle.response.set_cookie("session", cookie)

        bottle.redirect("/welcome")

    else:
        return bottle.template("login",
                               dict(username=cgi.escape(username), password="",
                                    login_error="Invalid Login"))


@bottle.get('/logout')
def process_logout():
    cookie = bottle.request.get_cookie("session")

    if (cookie == None):
        print "no cookie..."
        bottle.redirect("/signup")
    else:
        session_id = user.check_secure_val(cookie)

        if session_id == None:
            print "no secure session_id"
            bottle.redirect("/signup")

        else:
            # remove the session
            user.end_session(connection, session_id)
            print "clearing the cookie"
            bottle.response.set_cookie("session", "")
            bottle.redirect("/signup")


bottle.debug(True)
bottle.run(host='localhost', port=8082)
