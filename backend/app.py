from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider
from bson import ObjectId
from flask_cors import CORS
from faster_whisper import WhisperModel
import os
import tempfile
import re

from groq_service import extract_profile
from database import users_collection


# ==========================================
# MONGO JSON PROVIDER
# ==========================================

class MongoJSONProvider(DefaultJSONProvider):

    def default(self, obj):

        if isinstance(obj, ObjectId):
            return str(obj)

        return super().default(obj)


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.json_provider_class = MongoJSONProvider
app.json = MongoJSONProvider(app)

CORS(app)


# ==========================================
# WHISPER MODEL
# ==========================================

print("Whisper model will be loaded when needed...")

model = None


def get_whisper_model():

    global model

    if model is None:

        print("Loading Whisper model...")

        model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded successfully!")

    return model


# ==========================================
# HOME
# ==========================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Voice User Profile API is running"
    })


# ==========================================
# HEALTH
# ==========================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok"
    })


# ==========================================
# GET USERS
# ==========================================

@app.route("/users", methods=["GET"])
def get_users():

    try:

        users = list(
            users_collection.find(
                {},
                {
                    "_id": 0
                }
            )
        )

        return jsonify({

            "success": True,

            "users": users

        })

    except Exception as error:

        print(
            "Get users error:",
            error
        )

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500


# ==========================================
# TRANSCRIBE
# ==========================================

@app.route(
    "/transcribe",
    methods=["POST"]
)
def transcribe():

    if "audio" not in request.files:

        return jsonify({

            "success": False,

            "error":
            "No audio file received"

        }), 400


    audio_file = request.files["audio"]


    if audio_file.filename == "":

        return jsonify({

            "success": False,

            "error":
            "No audio file selected"

        }), 400


    temp_path = None


    try:

        # ==========================================
        # SAVE AUDIO
        # ==========================================

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp:

            audio_file.save(
                temp.name
            )

            temp_path = temp.name


        # ==========================================
        # WHISPER
        # ==========================================

        whisper_model = get_whisper_model()

        segments, info = whisper_model.transcribe(

            temp_path,

            language="en",

            task="transcribe",

            beam_size=1,

            best_of=1,

            temperature=0,

            condition_on_previous_text=False

        )


        transcript = " ".join(
            segment.text for segment in segments
        ).strip()


        print(
            "Whisper transcript:",
            transcript
        )


        # ==========================================
        # GROQ
        # ==========================================

        profile = extract_profile(
            transcript
        )


        print(
            "Extracted profile:",
            profile
        )


        # ==========================================
        # SIMPLE VOICE COMMAND DETECTION
        # ==========================================

        lower_transcript = transcript.lower().strip()


        # ==========================================
        # SHOW COMMAND
        # ==========================================

        if lower_transcript.startswith("show "):

            profile["action"] = "show"

            target_text = re.sub(
                r"^show\s+",
                "",
                transcript,
                flags=re.IGNORECASE
            ).strip()


            target_text = re.sub(
                r"['’]s\s+(?:profile|details?)$",
                "",
                target_text,
                flags=re.IGNORECASE
            ).strip()


            target_text = re.sub(
                r"\s+(?:profile|details?)$",
                "",
                target_text,
                flags=re.IGNORECASE
            ).strip()


            profile["target_name"] = (
                target_text
                .strip()
                .strip(".,!?")
            )


        # ==========================================
        # DELETE / REMOVE COMMAND
        # ==========================================

        elif (
            lower_transcript.startswith("delete ")
            or lower_transcript.startswith("remove ")
        ):

            profile["action"] = "delete"

            target_text = re.sub(
                r"^(?:delete|remove)\s+",
                "",
                transcript,
                flags=re.IGNORECASE
            ).strip()


            target_text = re.sub(
                r"['’]s\s+(?:profile|details?)$",
                "",
                target_text,
                flags=re.IGNORECASE
            ).strip()


            profile["target_name"] = (
                target_text
                .strip()
                .strip(".,!?")
            )


        # ==========================================
        # UPDATE / CHANGE COMMAND
        # ==========================================

        elif (
            lower_transcript.startswith("update ")
            or lower_transcript.startswith("change ")
        ):

            profile["action"] = "update"

            match = re.match(
                r"^(?:update|change)\s+(.+?)(?:['’]s)?\s+(?:name|email|phone|phone\s+number|city|occupation)\s+(?:to|as)\s+",
                transcript,
                flags=re.IGNORECASE
            )


            if match:

                profile["target_name"] = (
                    match.group(1)
                    .strip()
                    .strip("'")
                    .strip(".,!?")
                )


            elif not profile.get("target_name"):

                match = re.match(
                    r"^(?:update|change)\s+([A-Za-z][A-Za-z ]*?)(?:['’]s)?\s+",
                    transcript,
                    flags=re.IGNORECASE
                )


                if match:

                    profile["target_name"] = (
                        match.group(1)
                        .strip()
                        .strip("'")
                        .strip(".,!?")
                    )


        print(
            "Final voice action:",
            profile
        )


        # ==========================================
        # ACTION
        # ==========================================

        action = profile.get(
            "action",
            "create"
        ).lower().strip()


        target_name = profile.get(
            "target_name",
            ""
        ).strip()


        target_email = profile.get(
            "target_email",
            ""
        ).strip().lower()


        # ==========================================
        # CLEAN TRANSCRIPT EMAIL
        # ==========================================

        cleaned_transcript = transcript


        if profile.get("email"):

            email = (
                profile["email"]
                .lower()
                .replace(" ", "")
            )


            cleaned_transcript = re.sub(

                r"((?:my|the)?\s*"
                r"(?:gmail|email)"
                r"\s*(?:id)?"
                r"\s*(?:is)?\s+)"
                r".*?"
                r"(?=\s+(?:my|and|i\s+live|"
                r"i\s+am|my\s+occupation|"
                r"my\s+phone)|$)",

                rf"\1{email}",

                cleaned_transcript,

                flags=re.IGNORECASE
            )


        # ==========================================
        # FIND TARGET USER
        # ==========================================

        target_user = None


        if target_email:

            target_user = users_collection.find_one({

                "email":
                target_email

            })


        elif target_name:

            clean_target_name = (
                target_name
                .strip()
                .strip(".,!?")
            )


            target_user = users_collection.find_one({

                "name": {
                    "$regex":
                    f"^{re.escape(clean_target_name)}(?:\\s+.*)?$",

                    "$options":
                    "i"
                }

            })


        # ==========================================
        # SHOW USER
        # ==========================================

        if action == "show":

            if not target_user:

                return jsonify({

                    "success": False,

                    "action": "show",

                    "error":
                    "User not found.",

                    "transcript":
                    cleaned_transcript,

                    "profile":
                    profile

                }), 404


            user = {

                key: value

                for key, value
                in target_user.items()

                if key != "_id"

            }


            return jsonify({

                "success": True,

                "action": "show",

                "message":
                "User found successfully",

                "user":
                user,

                "transcript":
                cleaned_transcript,

                "profile":
                user

            })


        # ==========================================
        # DELETE USER
        # ==========================================

        if action == "delete":

            if not target_user:

                return jsonify({

                    "success": False,

                    "action": "delete",

                    "error":
                    "User not found.",

                    "transcript":
                    cleaned_transcript,

                    "profile":
                    profile

                }), 404


            users_collection.delete_one({

                "_id":
                target_user["_id"]

            })


            print(
                "User deleted:",
                target_name or target_email
            )


            return jsonify({

                "success": True,

                "action": "delete",

                "message":
                "User deleted successfully",

                "transcript":
                cleaned_transcript,

                "profile":
                profile

            })


        # ==========================================
        # UPDATE USER
        # ==========================================

        if action == "update":

            if not target_user:

                return jsonify({

                    "success": False,

                    "action": "update",

                    "error":
                    "User not found.",

                    "transcript":
                    cleaned_transcript,

                    "profile":
                    profile

                }), 404


            update_data = {}


            if profile.get("name"):

                update_data["name"] = (
                    profile["name"]
                    .strip()
                )


            if profile.get("email"):

                update_data["email"] = (
                    profile["email"]
                    .strip()
                    .lower()
                )


            if profile.get("phone"):

                update_data["phone"] = (
                    profile["phone"]
                    .strip()
                )


            if profile.get("city"):

                update_data["city"] = (
                    profile["city"]
                    .strip()
                )


            if profile.get("occupation"):

                update_data["occupation"] = (
                    profile["occupation"]
                    .strip()
                )


            if not update_data:

                return jsonify({

                    "success": False,

                    "action": "update",

                    "error":
                    "No field was provided to update.",

                    "transcript":
                    cleaned_transcript,

                    "profile":
                    profile

                }), 400


            # ==========================================
            # CHECK DUPLICATE EMAIL
            # ==========================================

            if "email" in update_data:

                duplicate = users_collection.find_one({

                    "email":
                    update_data["email"],

                    "_id": {
                        "$ne":
                        target_user["_id"]
                    }

                })


                if duplicate:

                    return jsonify({

                        "success": False,

                        "action": "update",

                        "error":
                        "Another user already has this email.",

                        "transcript":
                        cleaned_transcript,

                        "profile":
                        profile

                    }), 409


            # ==========================================
            # UPDATE
            # ==========================================

            users_collection.update_one(

                {
                    "_id":
                    target_user["_id"]
                },

                {
                    "$set":
                    update_data
                }

            )


            updated_user = users_collection.find_one(

                {
                    "_id":
                    target_user["_id"]
                },

                {
                    "_id": 0
                }

            )


            print(
                "User updated:",
                update_data
            )


            return jsonify({

                "success": True,

                "action": "update",

                "message":
                "User updated successfully",

                "updated_user":
                updated_user,

                "transcript":
                cleaned_transcript,

                "profile":
                updated_user

            })


        # ==========================================
        # CREATE USER
        # ==========================================

        mongo_profile = {

            "name": profile.get(
                "name",
                ""
            ).strip(),

            "email": profile.get(
                "email",
                ""
            ).strip().lower(),

            "phone": profile.get(
                "phone",
                ""
            ).strip(),

            "city": profile.get(
                "city",
                ""
            ).strip(),

            "occupation": profile.get(
                "occupation",
                ""
            ).strip()

        }


        has_data = any(
            mongo_profile.values()
        )


        if not has_data:

            return jsonify({

                "success": False,

                "error":
                "No profile information detected.",

                "transcript":
                cleaned_transcript,

                "profile":
                profile

            }), 400


        # ==========================================
        # CREATE / EXISTING EMAIL
        # ==========================================

        if mongo_profile["email"]:

            existing_user = users_collection.find_one({

                "email":
                mongo_profile["email"]

            })


            if existing_user:

                users_collection.update_one(

                    {
                        "_id":
                        existing_user["_id"]
                    },

                    {
                        "$set":
                        mongo_profile
                    }

                )

                message = (
                    "Profile updated successfully"
                )

            else:

                users_collection.insert_one(
                    mongo_profile
                )

                message = (
                    "Profile created successfully"
                )

        else:

            users_collection.insert_one(
                mongo_profile
            )

            message = (
                "Profile created successfully"
            )


        # ==========================================
        # RESPONSE
        # ==========================================

        return jsonify({

            "success": True,

            "action": "create",

            "message":
            message,

            "transcript":
            cleaned_transcript,

            "profile":
            mongo_profile

        })


    except Exception as error:

        print(
            "Transcription error:",
            error
        )

        return jsonify({

            "success": False,

            "error":
            str(error)

        }), 500


    finally:

        if (
            temp_path
            and os.path.exists(
                temp_path
            )
        ):

            os.remove(
                temp_path
            )


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )