from flask import g, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_server import flask_server, db, mail
from flask_server.forms import (
    LoginForm,
    RegistrationForm,
    PostForm,
    UpdateForm,
    ResetPWForm,
    EditProfileForm,
    ForgotPWForm,
)
from flask_server.models import User, Post
from datetime import datetime, timedelta
from functools import wraps

methods = ["GET", "POST"]


@flask_server.route("/send-weekly-newsletter/")
def send_weekly_newsletter():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("send_weekly_newsletter")))
    if not current_user.admin:
        return "Not Authorized!"
    User.send_weekly_newsletter()
    flash("You have successfully sent the newsletter!")
    return redirect(url_for("admin"))


@flask_server.route("/user/<username>/email-subscribe/")
def email_subscribe(username):
    if not current_user.is_authenticated:
        return redirect(
            url_for("login", next=url_for("email_subscribe", username=username))
        )
    try:
        user = User.query.filter_by(username=username).first_or_404()
        user.set_mail_status(True)
        db.session.commit()
    except:
        db.session.rollback()
        user = User.query.filter_by(username=username).first_or_404()
        user.set_mail_status(True)
        db.session.commit()

    flash("You are now signed up for emails!")
    return redirect(url_for("user_profile", username=user.username))


@flask_server.route("/user/<username>/email-unsubscribe/")
def email_unsubscribe(username):
    if not current_user.is_authenticated:
        return redirect(
            url_for("login", next=url_for("email_unsubscribe", username=username))
        )
    try:
        user = User.query.filter_by(username=username).first_or_404()
        user.set_mail_status(False)
        db.session.commit()
    except:
        db.session.rollback()
        user = User.query.filter_by(username=username).first_or_404()
        user.set_mail_status(False)
        db.session.commit()

    flash("You are now unsubscribed from emails!")
    return redirect(url_for("user_profile", username=user.username))


@flask_server.route("/")
def index():
    return redirect(url_for("discover"))


@flask_server.route("/discover")
def discover():
    page = request.args.get("page", 1, type=int)
    try:
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page, flask_server.config["POSTS_PER_PAGE"], False
        )
    except:
        db.session.rollback()
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page, flask_server.config["POSTS_PER_PAGE"], False
        )
    next_url = url_for("discover", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("discover", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "discover.html",
        title="really good music.",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@flask_server.route("/login", methods=methods)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
        except:
            db.session.rollback()
            user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))

        login_user(user, remember=form.remember_me.data)
        user.authenticated = True
        db.session.commit()

        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("feed")
        return redirect(next_page)
    return render_template("login.html", title="Log In", form=form)

@flask_server.route("/success", methods=methods)
def success():
    current_user.poster = True;
    db.session.add(current_user)
    db.session.commit()
    return "Thank You For Signing Up For Posting Privileges!"

@flask_server.route("/feed")
def feed():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("feed")))
    page = request.args.get("page", 1, type=int)
    try:
        posts = current_user.followed_posts().paginate(
            page, flask_server.config["POSTS_PER_PAGE"], False
        )
    except:
        db.session.rollback()
        posts = current_user.followed_posts().paginate(
            page, flask_server.config["POSTS_PER_PAGE"], False
        )

    next_url = url_for("feed", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("feed", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "feed.html",
        title="My Feed",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@flask_server.route("/logout")
def logout():
    current_user.authenticated = False
    db.session.add(current_user)
    db.session.commit()
    logout_user()
    flash("Logged out!")
    return redirect(url_for("discover"))


@flask_server.route("/create", methods=methods)
def create_post():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("create_post")))
    if not current_user.poster:
        return "Not Authorized!"
    form = PostForm()
    time = datetime.utcnow()
    if form.validate_on_submit():
        try:
            Post.create(url=form.url.data, body=form.body.data)
            flash("Congratulations, You Have Successfully Created A Post!")
            return redirect(url_for("feed"))
        except:
            db.session.rollback()
            Post.create(url=form.url.data, body=form.body.data)
            flash("Congratulations, You Have Successfully Created A Post!")
            return redirect(url_for("feed"))
    return render_template("create.html", title="Create Post", form=form)


@flask_server.route("/admin", methods=methods)
def admin():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("admin")))
    if not current_user.admin:
        return "Not Authorized!"

    try:
        users = User.get_users()
        posts = Post.get_posts()
    except:
        db.session.rollback()
        users = User.get_users()
        posts = Post.get_posts()

    return render_template("admin.html", users=users, posts=posts)


@flask_server.route("/post/<int:id>/delete")
def delete_post(id):
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("delete_post", id=id)))

    if current_user.id is not Post.get_post(id).user_id or not current_user.admin:
        return "Not Authorized!"
    try:
        Post.delete(id)
    except:
        db.session.rollback()
        Post.delete(id)
    return redirect(url_for("feed"))


@flask_server.route("/delete/users")
def delete_users():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("delete_users")))
    if not current_user.admin:
        return "Not Authorized!"
    try:
        User.delete_all()
    except:
        db.session.rollback()
        User.delete_all()
    return redirect(url_for("admin"))


@flask_server.route("/delete/user/<username>")
def delete_user(username):
    if not current_user.is_authenticated:
        return redirect(
            url_for("login", next=url_for("delete_user", username=username))
        )
    if not current_user.admin:
        return "Not Authorized!"
    try:
        user = User.query.filter_by(username=username).first_or_404()
        User.delete(user.id)
    except:
        db.session.rollback()
        user = User.query.filter_by(username=username).first_or_404()
        User.delete(user.id)

    return redirect(url_for("admin"))


@flask_server.route("/delete/posts")
def delete_posts():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("delete_posts")))
    if not current_user.admin:
        return "Not Authorized!"
    try:
        Post.delete_all()
    except:
        db.session.rollback()
        Post.delete_all()
    return redirect(url_for("admin"))


@flask_server.route("/post/<int:id>/update", methods=methods)
def update_post(id):
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("update_post", id=id)))
    if (
        current_user.id is not Post.get_post(id).user_id
        or not current_user.poster
        or not current_user.admin
    ):
        return "Not Authorized!"
    try:
        post_to_update = Post.query.get_or_404(id)
    except:
        db.session.rollback()
        post_to_update = Post.query.get_or_404(id)

    form = UpdateForm()
    time = datetime.utcnow()

    if form.validate_on_submit():
        try:
            post_to_update = Post.query.get_or_404(id)
            Post.update(post_to_update.id, form.url.data, form.body.data)
        except:
            db.session.rollback()
            Post.update(post_to_update.id, form.url.data, form.body.data)
        return redirect(url_for("feed"))
    elif request.method == "GET":
        form.body.data = post_to_update.body
        form.url.data = post_to_update.url

    return render_template(
        "update.html", title="Update Post", form=form, post=post_to_update
    )


@flask_server.route("/register", methods=methods)
def register():
    if current_user.is_authenticated:
        return redirect(url_for("feed"))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            print("registering")
            user = User(
                username=form.username.data,
                email=form.email.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, You Are Now A Registered User!")
            return redirect(url_for("login"))
        except:
            db.session.rollback()
            user = User(
                username=form.username.data,
                email=form.email.data,
                profile_picture_url=form.profile_picture_url.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, You Are Now A Registered User!")
            return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@flask_server.route("/reset-pw", methods=methods)
def reset_pw():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("reset_pw")))
    form = ResetPWForm()
    if form.validate_on_submit():
        try:
            user = current_user
            user.set_password(form.new_password.data)
            user.authenticated = False
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, You Have Updated Your Password!")
            logout_user()
            return redirect(url_for("login"))
        except:
            db.session.rollback()
            user = current_user
            user.authenticated = False
            user.set_password(form.new_password.data)
            db.session.add(user)
            db.session.commit()
            flash("Congratulations, You Have Updated Your Password!")
            logout_user()
            return redirect(url_for("login"))
    return render_template("reset-pw.html", title="Reset Password", form=form)


@flask_server.route("/user/<username>")
def user_profile(username):
    if not current_user.is_authenticated:
        return redirect(
            url_for("login", next=url_for("user_profile", username=username))
        )
    page = request.args.get("page", 1, type=int)
    try:
        user = User.query.filter_by(username=username).first_or_404()
        posts = user.posts.order_by(Post.timestamp.desc()).paginate(
            page, flask_server.config["POSTS_PER_PAGE"], False
        )
    except:
        db.session.rollback()
        user = User.query.filter_by(username=username).first_or_404()
        posts = user.posts.order_by(Post.timestamp.desc()).paginate(
            page, flask_server.config["POSTS_PER_PAGE"], False
        )

    next_url = (
        url_for(
            "user_profile",
            title="User Profile",
            username=user.username,
            page=posts.next_num,
        )
        if posts.has_next
        else None
    )
    prev_url = (
        url_for(
            "user_profile",
            title="User Profile",
            username=user.username,
            page=posts.prev_num,
        )
        if posts.has_prev
        else None
    )
    return render_template(
        "user.html",
        title="User Profile",
        user=user,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@flask_server.route("/user/<username>/following")
def following(username):
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("following", username=username)))
    try:
        user = User.query.filter_by(username=username).first_or_404()
        usernames = user.followed_users()
    except:
        db.session.rollback()
        user = User.query.filter_by(username=username).first_or_404()
        usernames = user.followed_users()
    return render_template(
        "following.html", title="Following", user=user, usernames=usernames
    )


@flask_server.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPWForm()
    if form.validate_on_submit():
        try:
            User.forgot_password(email=form.email.data)
        except:
            db.session.rollback()
            User.forgot_password(email=form.email.data)
        flash("An email has been sent with a temporary password")
        return redirect(url_for("login"))
    return render_template("forgot_password.html", title="Forgot Password", form=form)


@flask_server.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("edit_profile")))
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.profile_picture_url = form.profile_picture_url.data
        current_user.twitter = form.twitter.data
        current_user.github = form.github.data
        current_user.instagram = form.instagram.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect("/user/" + current_user.username)
    elif request.method == "GET":
        form.username.data = current_user.username
        form.twitter.data = current_user.twitter
        form.github.data = current_user.github
        form.instagram.data = current_user.instagram
        form.about_me.data = current_user.about_me
        form.profile_picture_url.data = current_user.profile_picture_url
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@flask_server.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()


@flask_server.route("/follow/<username>")
def follow(username):
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("follow", username=username)))
    try:
        user = User.query.filter_by(username=username).first()
    except:
        db.session.rollback()
        user = User.query.filter_by(username=username).first()

    if user is None:
        flash("User {} not found.".format(username))
        return redirect(url_for("feed"))
    if user == current_user:
        flash("You cannot follow yourself!")
        return redirect(url_for("user", username=username))
    current_user.follow(user)
    db.session.commit()
    flash("You are following {}!".format(username))
    return redirect(url_for("user", title="User Profile", username=username))


@flask_server.route("/unfollow/<username>")
def unfollow(username):
    if not current_user.is_authenticated:
        return redirect(url_for("login", next=url_for("unfollow", username=username)))
    try:
        user = User.query.filter_by(username=username).first()
    except:
        db.session.rollback()
        user = User.query.filter_by(username=username).first()

    if user is None:
        flash("User {} not found.".format(username))
        return redirect(url_for("feed"))
    if user == current_user:
        flash("You cannot unfollow yourself!")
        return redirect(url_for("user", title="User Profile", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash("You are not following {}.".format(username))
    return redirect(url_for("user", title="User Profile", username=username))


@flask_server.route("/post/<int:id>")
def show_post(id):
    post = Post.get_post(id)
    return render_template("post.html", title=post.body, post=post,)
