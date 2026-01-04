#!/usr/bin/env python3

from flask import request, session, jsonify, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from server.config import app, db, api
from models import User, Recipe


class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        bio = data.get("bio")
        image_url = data.get("image_url")

        if not username:
            return make_response(jsonify({"error": "Username is required"}), 422)

        user = User(username=username, bio=bio, image_url=image_url)
        user.password_hash = password

        try:
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            return make_response(jsonify(user.to_dict()), 201)
        except IntegrityError:
            return make_response(jsonify({"error": "Username already exists"}), 422)


class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            if user:
                return make_response(jsonify(user.to_dict()), 200)
        return make_response(jsonify({"error": "Unauthorized"}), 401)


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter(User.username == username).first()
        if user and user.authenticate(password):
            session["user_id"] = user.id
            return make_response(jsonify(user.to_dict()), 200)
        return make_response(jsonify({"error": "Invalid username or password"}), 401)


class Logout(Resource):
    def delete(self):
        user_id = session.get("user_id")
        if user_id:
            session["user_id"] = None
            return make_response(jsonify({}), 204)
        return make_response(jsonify({"error": "Unauthorized"}), 401)


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        recipes = Recipe.query.filter(Recipe.user_id == user_id).all()
        return make_response(jsonify([recipe.to_dict() for recipe in recipes]), 200)

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes_to_complete = data.get("minutes_to_complete")

        if not title or not instructions:
            return make_response(
                jsonify({"error": "Title and instructions are required"}), 422
            )

        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id,
            )
            db.session.add(recipe)
            db.session.commit()
            return make_response(jsonify(recipe.to_dict()), 201)
        except (IntegrityError, ValueError) as e:
            return make_response(jsonify({"error": str(e)}), 422)


try:
    api.add_resource(Signup, "/signup", endpoint="signup")
    api.add_resource(CheckSession, "/check_session", endpoint="check_session")
    api.add_resource(Login, "/login", endpoint="login")
    api.add_resource(Logout, "/logout", endpoint="logout")
    api.add_resource(RecipeIndex, "/recipes", endpoint="recipes")
except ValueError:
    pass


if __name__ == "__main__":
    app.run(port=5555, debug=True)
