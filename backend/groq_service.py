import os
import json
import re

from groq import Groq
from dotenv import load_dotenv


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ==========================================
# EMAIL CLEANING
# ==========================================

def clean_email(email):

    if not email:
        return ""

    email = email.lower().strip()

    email = re.sub(
        r"\s+(at\s+the\s+rate|at\s+therate|at\s+rate|at\s+the\s+red|at\s+the|at)\s+",
        "@",
        email,
        flags=re.IGNORECASE
    )

    email = re.sub(
        r"\s+(dot|period|full\s+stop)\s+",
        ".",
        email,
        flags=re.IGNORECASE
    )

    email = email.replace("the way", "")
    email = email.replace("theweight", "")
    email = email.replace("therate", "@")

    email = email.replace(
        "@thegmail.com",
        "@gmail.com"
    )

    email = email.replace(
        "@thegmail",
        "@gmail"
    )

    email = email.replace(
        "@theweightgmail.com",
        "@gmail.com"
    )

    email = email.replace(
        "@weightgmail.com",
        "@gmail.com"
    )

    email = email.replace(
        "@thewaygmail.com",
        "@gmail.com"
    )

    email = re.sub(
        r"\s+",
        "",
        email
    )

    email = re.sub(
        r"@+",
        "@",
        email
    )

    email = re.sub(
        r"\.{2,}",
        ".",
        email
    )

    return email


# ==========================================
# CITY CLEANING
# ==========================================

def clean_city(city):

    if not city:
        return ""

    city = city.strip()

    city_corrections = {

        "aligard": "Aligarh",
        "aliger": "Aligarh",
        "aligarh": "Aligarh",

        "delhie": "Delhi",
        "delhi": "Delhi",

        "jaipur": "Jaipur",

        "noida": "Noida",

        "gurgaon": "Gurgaon",
        "gurugram": "Gurugram",

        "mumbai": "Mumbai",
        "bombay": "Mumbai",

        "bangalore": "Bangalore",
        "bengaluru": "Bengaluru",

        "lucknow": "Lucknow",
        "kanpur": "Kanpur",
        "agra": "Agra",
        "meerut": "Meerut"
    }

    key = city.lower().strip()

    return city_corrections.get(
        key,
        city
    )


# ==========================================
# EXTRACT PROFILE / VOICE COMMAND
# ==========================================

def extract_profile(transcript):

    prompt = f"""
You are processing a voice command for a User Profile application.

Return ONLY valid JSON.

Return exactly these fields:

action
target_name
target_email
name
email
phone
city
occupation


ACTION RULES:

If the user is creating a new profile:
action = "create"

If the user says update, change or modify:
action = "update"

If the user says delete or remove:
action = "delete"

If the user says show, find or display:
action = "show"


TARGET NAME:

For update, delete and show commands,
extract the name of the user being targeted.

Example:

"Update Anjali's city to Jaipur."

target_name = "Anjali"
city = "Jaipur"

Example:

"Delete Anjali."

target_name = "Anjali"


TARGET EMAIL:

If an email is explicitly used to identify the target,
put it in target_email.

Example:

"Update user with email anjali at gmail dot com.
Change city to Jaipur."

target_email = "anjali@gmail.com"

If no target email is given:
target_email = ""


IMPORTANT UPDATE RULE:

For update commands, return ONLY the fields that
the user wants to change.

Do NOT copy unrelated fields.

Example:

"Update Anjali's city to Jaipur."

Return:

name = ""
email = ""
phone = ""
city = "Jaipur"
occupation = ""


Example:

"Change Anjali's occupation to React Developer."

Return:

name = ""
email = ""
phone = ""
city = ""
occupation = "React Developer"


If the user says:

"Change Anjali's email to anjali123 at gmail dot com."

Return:

email = "anjali123@gmail.com"


EMAIL RULES:

Convert:

at
at the rate
at therate
at rate
at the red
at the

into @.

Convert:

dot
period
full stop

into .

Remove spaces inside email addresses.

Normalize obvious Gmail recognition mistakes.

Examples:

"anjaligupta at gmail dot com"
= "anjaligupta@gmail.com"

"anjaligupta at the rate gmail dot com"
= "anjaligupta@gmail.com"


CITY RULES:

Correct only obvious speech recognition mistakes.

Example:

"Aligard" = "Aligarh"


NAME RULES:

Preserve the name.

Only correct obvious speech recognition mistakes.


PHONE RULES:

Return only phone digits.


OCCUPATION RULES:

Keep occupation as spoken.


CREATE RULE:

For a normal profile creation command,
extract the user's profile information.

Example:

"My name is Anjali Gupta and my email is
anjali at gmail dot com."

action = "create"

target_name = ""

target_email = ""

name = "Anjali Gupta"

email = "anjali@gmail.com"


SHOW RULE:

For:

"Show Anjali."

action = "show"

target_name = "Anjali"

All profile fields should be empty.


DELETE RULE:

For:

"Delete Anjali."

action = "delete"

target_name = "Anjali"

All profile fields should be empty.


GENERAL RULES:

Return JSON only.

Do not return markdown.

Do not add extra fields.

Missing fields must be empty strings.


Transcript:

{transcript}
"""

    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0
        )

        content = (
            response.choices[0]
            .message.content
            .strip()
        )

        print(
            "Groq response:",
            content
        )


        # ==========================================
        # REMOVE MARKDOWN
        # ==========================================

        if content.startswith("```"):

            content = re.sub(
                r"^```(?:json)?\s*",
                "",
                content,
                flags=re.IGNORECASE
            )

            content = re.sub(
                r"\s*```$",
                "",
                content
            )

            content = content.strip()


        # ==========================================
        # PARSE JSON
        # ==========================================

        profile = json.loads(content)


        # ==========================================
        # CLEAN VALUES
        # ==========================================

        return {

            "action": profile.get(
                "action",
                "create"
            ),

            "target_name": profile.get(
                "target_name",
                ""
            ).strip(),

            "target_email": clean_email(
                profile.get(
                    "target_email",
                    ""
                )
            ),

            "name": profile.get(
                "name",
                ""
            ).strip(),

            "email": clean_email(
                profile.get(
                    "email",
                    ""
                )
            ),

            "phone": profile.get(
                "phone",
                ""
            ).strip(),

            "city": clean_city(
                profile.get(
                    "city",
                    ""
                )
            ),

            "occupation": profile.get(
                "occupation",
                ""
            ).strip()
        }


    except Exception as error:

        print(
            "Groq extraction error:",
            error
        )

        return {

            "action": "create",

            "target_name": "",

            "target_email": "",

            "name": "",

            "email": "",

            "phone": "",

            "city": "",

            "occupation": ""
        }