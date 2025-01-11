import random
import requests
import json
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Object, Solved

main_bp = Blueprint('main', __name__)


def send_sms(phone_number, otp_code):
    send_sms_data = {
        "code": "f1mrhsfmwtc3yjl",
        "sender": "+983000505",
        "recipient": phone_number,
        "variable": {
            "verification-code": f"{otp_code}"
        }
    }
    send_sms_req = requests.post(
        url=f"{'https://api2.ippanel.com/api/v1'}/sms/pattern/normal/send",
        data=json.dumps(send_sms_data),
        headers={
            'Content-Type': 'application/json',
            'apikey': "8wRCaGMHUvF_1nb2-3gifE3bvWeuwLPkPcpjoqx9Z_Y="
        }
    )
    if send_sms_req.json()['status'] == 'OK':
        return True


@main_bp.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    phone_number = data.get('phone_number')

    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    user = User.query.filter_by(phone_number=phone_number).first()

    if not user:
        user = User(phone_number=phone_number)
        db.session.add(user)

    otp_code = f"{random.randint(1000, 9999)}"
    user.otp_code = otp_code
    db.session.commit()

    send_sms(phone_number, otp_code)

    return jsonify({"message": "OTP sent successfully"}), 200


@main_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    phone_number = data.get('phone_number')
    otp_code = data.get('otp_code')

    if not phone_number or not otp_code:
        return jsonify({"error": "Phone number and OTP are required"}), 400

    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.otp_code != otp_code:
        return jsonify({"error": "Invalid OTP"}), 400

    user.otp_code = None
    user.otp_created_at = None
    db.session.commit()

    return jsonify({"message": "Login successful"}), 200


@main_bp.route('/object/create', methods=['POST'])
def create_object():
    try:
        # Parse input data
        data = request.get_json()
        name = data.get('name')
        limit = data.get('limit')

        # Validate input
        if not name or not limit:
            return jsonify({'error': 'Name and limit are required.'}), 400

        # Check if the object already exists
        existing_object = Object.query.filter_by(name=name).first()
        if existing_object:
            return jsonify({'error': 'Object with this name already exists.'}), 400

        # Create a new object
        new_object = Object(name=name, limit=limit, solved_count=0)
        db.session.add(new_object)
        db.session.commit()

        return jsonify({'message': 'Object created successfully.'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/object/update/<int:object_id>', methods=['PUT'])
def update_object(object_id):
    data = request.get_json()
    new_limit = data.get('limit')

    # Query
    obj = Object.query.get(object_id)
    if not obj:
        return jsonify({"error": "Object not found"}), 404

    # Update limit
    obj.limit = new_limit
    db.session.commit()

    return jsonify({"message": "Object updated successfully",
                    "object": {"id": obj.id, "name": obj.name, "new_limit": obj.limit}}), 200


@main_bp.route('/object/list', methods=['GET'])
def list_object():
    try:
        objects = Object.query.all()
        result = [
            {
                "id": obj.id,
                "name": obj.name,
                "limit": obj.limit,
                "solved_count": obj.solved_count
            }
            for obj in objects
        ]
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/solved', methods=['POST'])
def solve():
    try:
        # Parse input data
        data = request.get_json()
        phone_number = data.get('phone_number')
        object_id = data.get('object_id')

        # Validate input
        if not phone_number or not object_id:
            return jsonify({'error': 'Phone number and object ID are required.'}), 400

        # Fetch user
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            return jsonify({'error': 'User not found.'}), 404

        # Fetch object
        obj = Object.query.filter_by(id=object_id).first()
        if not obj:
            return jsonify({'error': 'Object not found.'}), 404

        # Check existing solve
        existing_solve = Solved.query.filter_by(user_id=user.id, object_id=obj.id).first()
        if existing_solve:
            return jsonify({"message": "This object has already been solved by this user"}), 200

        # Check if limit is reached
        if obj.solved_count >= obj.limit:
            return jsonify({'error': 'Object limit reached.'}), 400

        # Create a new Solved record
        solved = Solved(user_id=user.id, object_id=obj.id)
        db.session.add(solved)

        # Increment solved_count for the object
        obj.solved_count += 1
        db.session.commit()

        return jsonify({'message': 'Solve added successfully.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/solves/filter/separate', methods=['GET'])
def get_solves():
    target_names = ["6", "7", "8"]
    result = {}

    for name in target_names:
        obj = Object.query.filter_by(name=name).first()
        if obj:
            solves = (
                Solved.query
                .filter_by(object_id=obj.id)
                .order_by(Solved.date_time.asc())
                .all()
            )
            result[name] = [
                {
                    "user_phone_number": s.user.phone_number,
                    "date_time": s.date_time.strftime("%Y-%m-%d %H:%M:%S")
                }
                for s in solves
            ]
        else:
            result[name] = []

    return jsonify(result), 200
