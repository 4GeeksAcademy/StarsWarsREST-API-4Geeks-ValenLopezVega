"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from sqlalchemy import select
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorite
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route("/characters", methods=["GET"])
def get_characters():
    characters = db.session.execute(select(Character)).scalars().all()
    return jsonify([character.serialize() for character in characters]), 200


@app.route("/characters/<int:character_id>", methods=["GET"])
def get_one_character(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(character.serialize()), 200


@app.route("/planets", methods=["GET"])
def get_planets():
    planets = db.session.execute(select(Planet)).scalars().all()
    return jsonify([planet.serialize() for planet in planets]), 200


@app.route("/planets/<int:planet_id>", methods=["GET"])
def get_one_planet(planet_id):
    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200


@app.route("/favorite/planet/<int:planet_id>", methods=["POST"])
def add_favorite_planet(planet_id):
    body = request.json

    if not body or 'user_id' not in body:
        return jsonify({"error": "Missing user_id in request body"}), 400

    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"error": "Planet not found"}), 404

    user = db.session.get(User, body['user_id'])
    if user is None:
        return jsonify({"error": "User not found"}), 404

    favorite = Favorite(user_id=body['user_id'], planet_id=planet_id)

    db.session.add(favorite)
    try:
        db.session.commit()
        return jsonify({"message": "Planet saved to favorites"}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500


@app.route("/favorite/character/<int:character_id>", methods=["POST"])
def add_favorite_character(character_id):
    body = request.json

    if not body or 'user_id' not in body:
        return jsonify({"error": "Missing user_id in request body"}), 400

    character = db.session.get(Character, character_id)
    if character is None:
        return jsonify({"error": "Character not found"}), 404

    user = db.session.get(User, body['user_id'])
    if user is None:
        return jsonify({"error": "User not found"}), 404

    favorite = Favorite(user_id=body['user_id'], character_id=character_id)

    db.session.add(favorite)
    try:
        db.session.commit()
        return jsonify({"message": "Character saved to favorites"}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500


@app.route("/favorite/planet/<int:planet_id>", methods=["DELETE"])
def delete_favorite_planet(planet_id):

    body = request.json

    if not body or 'user_id' not in body:
        return jsonify({"error": "Missing user_id in request body"}), 400
    
    user_id = body["user_id"]

    favorite = db.session.execute(
        db.select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.planet_id == planet_id
        )
    ).scalar_one_or_none()

    if favorite is None:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    try:
        db.session.commit()
        return jsonify({"message": "Favorite deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error deleting favorite"}), 500


@app.route("/favorite/character/<int:character_id>", methods=["DELETE"])
def delete_favorite_character(character_id):
 
    body = request.json

    if not body or 'user_id' not in body:
        return jsonify({"error": "Missing user_id in request body"}), 400
    
    user_id = body["user_id"]

    favorite = db.session.execute(
        db.select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.character_id == character_id)
    ).scalar_one_or_none()

    if favorite is None:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    try:
        db.session.commit()
        return jsonify({"message": "Favorite deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error deleting favorite"}), 500


@app.route("/users", methods=["GET"])
def get_users():
    users = db.session.execute(select(User)).scalars().all()
    return jsonify([user.serialize() for user in users]), 200


@app.route("/users/favorites", methods=["GET"])
def get_user_favorites():
    user_id = request.args.get("user_id", type=int)

    if user_id is None:
        return jsonify({"error": "Missing user_id in query"}), 400

    favorites = db.session.execute(
        db.select(Favorite).where(Favorite.user_id == user_id)
    ).scalars().all()

    return jsonify([fav.serialize() for fav in favorites]), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
