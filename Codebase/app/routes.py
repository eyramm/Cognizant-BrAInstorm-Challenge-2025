from flask import Blueprint, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/echo")
def echo():
    payload = request.args.get("message", "Hello from Flask API")
    return jsonify({"message": payload})
