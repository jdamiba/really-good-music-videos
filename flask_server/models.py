from datetime import datetime, timedelta
from flask_server import flask_server, db, login, mail
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from flask import flash, redirect, url_for, request, render_template
from flask_mail import Mail, Message
import random
import string

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id")),
)


class User(UserMixin, db.Model):
    """ The User database object model.
    
    The Flask-Login extension expects that the class used to represent users implements the following properties and methods:
        a. is_authenticated
            - This property should return True if the user is authenticated, i.e. they have provided valid credentials. (Only authenticated users will fulfill the criteria of login_required.)
        b. is_active
            - This property should return True if this is an active user - in addition to being authenticated, they also have activated their account, not been suspended, or any condition your application has for rejecting an account. Inactive accounts may not log in (without being forced of course).
        c. is_anonymous
            - This property should return True if this is an anonymous user. (Actual users should return False instead.)
        d. get_id()
            - This method must return a unicode that uniquely identifies this user, and can be used to load the user from the user_loader callback. Note that this must be a unicode - if the ID is natively an int or some other type, you will need to convert it to unicode.
        e. These are inherited from the [`UserMixin`](https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin) class.
        f. [`db.Model`](https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/#models) q
    
    1. What does db.relationship() do? That function returns a new property that can do multiple things. In this case we told it to point to the Post class and load multiple of those. How does it know that this will return more than one post? Because SQLAlchemy guesses a useful default from your declaration. If you would want to have a one-to-one relationship you can pass uselist=False to relationship() (this would create a one-to-one relationship).
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    about_me = db.Column(db.String(140))
    twitter = db.Column(db.String(140))
    instagram = db.Column(db.String(140))
    github = db.Column(db.String(140))
    profile_picture_url = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    password_hash = db.Column(db.String(128))
    poster = db.Column(db.Boolean, unique=False, default=False)
    admin = db.Column(db.Boolean, unique=False, default=False)
    receives_mail = db.Column(db.Boolean, unique=False, default=False)
    authenticated = db.Column(db.Boolean, unique=False, default=False)

    posts = db.relationship("Post", backref="author", lazy="dynamic")
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def forgot_password(email):
        user = User.query.filter_by(email=email).first()
        rand_string = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
        )
        user.set_password(rand_string)
        db.session.add(user)
        db.session.commit()
        msg = Message(
            "Your Temporary Password", sender="jdamiba@gmail.com", recipients=[email]
        )
        msg.body = (
            "Your temporary password is: "
            + rand_string
            + ".\n Make sure to reset your password when you log back in!"
        )
        mail.send(msg)
        return

    def __repr__(self):
        return "<User {}>".format(self.username)

    def set_poster(self, status):
        self.poster = status
        return

    def is_poster(self):
        return self.poster

    def set_mail_status(self, status):
        self.receives_mail = status
        return

    def get_mail_status(self):
        return self.receives_mail

    def is_admin(self):
        return self.admin

    def set_admin(self, status):
        self.admin = status
        return

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size
        )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
        return

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
        return

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() == 1

    def followers(self):
        follower_posts = (
            Post.query.join(followers, (followers.c.follower_id == Post.user_id))
            .filter(followers.c.followed_id == self.id)
            .all()
        )

        return set(
            [User.query.filter_by(id=post.user_id).first() for post in follower_posts]
        )

    def followed_users(self):
        followed = (
            Post.query.join(followers, (followers.c.followed_id == Post.user_id))
            .filter(followers.c.follower_id == self.id)
            .all()
        )

        return set([User.query.filter_by(id=post.user_id).first() for post in followed])

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def delete_all():
        if not current_user.admin:
            return "There Was An Error!"

        users = User.get_users()
        for user in users:
            if not user.admin:
                db.session.delete(user)
        db.session.commit()
        return

    def delete(id):
        user = User.query.get_or_404(id)
        if not user.admin:
            db.session.delete(user)
        db.session.commit()
        return redirect(url_for("admin"))

    def get_user(id):
        return User.query.get_or_404(id)

    def get_users():
        return User.query.order_by(User.username).all()

    def get_posts(self):
        return self.posts

    def get_post(id):
        return Post.get_post(id)

    def signed_in(self):
        return self.authenticated

    def send_weekly_newsletter():
        recipients = User.get_users()
        recipients_emails = []
        post_urls = []
        for user in recipients:
            recipients_emails.append(user.email)
            if len(user.get_posts().all()) > 0:
                posts = user.get_posts().all()
                for post in posts:
                    if (datetime.utcnow() - post.timestamp) > timedelta(days=1):
                        post_urls.append(post)
        msg = Message(
            "Joe Damiba's Playlist This Week",
            sender="jdamiba@gmail.com",
            recipients=recipients_emails,
        )
        msg.body = str(post_urls)
        mail.send(msg)
        return


@login.user_loader
def load_user(id):
    """ This function is the glue between Flask-Login and the remote SQL database.
    
    """
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plays = db.Column(db.Integer, default=0)
    url = db.Column(db.String(140))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "\n{} - https://www.youtube.com/watch?v={}\n".format(self.body, self.url)

    def get_plays(self):
        return self.plays

    def increment_play_count(self):
        self.plays += 1
        return

    def delete_all():
        posts = Post.get_posts()
        for post in posts:
            db.session.delete(post)
        db.session.commit()
        return redirect(url_for("index"))

    def delete(id):
        post = Post.get_post(id)
        db.session.delete(post)
        db.session.commit()
        return

    def create(url, body):
        post = Post(user_id=current_user.id, url=url, body=body)
        db.session.add(post)
        db.session.commit()
        return

    def update(id, url, body):
        post = Post.get_post(id)
        post.url = url
        post.body = body
        db.session.add(post)
        db.session.commit()
        return

    def get_post(id):
        return Post.query.get_or_404(id)

    def get_posts():
        return Post.query.order_by(Post.id).all()
