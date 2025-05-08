from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
import os

# Load environment variables from the .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("GENAI_API_KEY")

# Initialize the GenAI client with the API key
client = genai.Client(api_key=api_key)
app = Flask(__name__)

# Simple state tracking
user_context = {"menu": "main", "submenu": None}

main_menu = {
    "1": "Pregnancy Tips",
    "2": "Child Growth Tracker",
    "3": "Immunization Schedule",
    "4": "Emergency Help",
    "5": "Live Chat with Nurse",
    "6": "Health Articles",
    "7": "Book Appointment – Schedule a clinic or doctor visit",
    "8": "Language Options – Switch to Kiswahili",
    "9": "More Services – Family planning, antenatal classes, etc"
}

submenus = {
    "Pregnancy Tips": {
        "1": "1st Trimester (0–12 weeks)",
        "2": "2nd Trimester (13–27 weeks)",
        "3": "3rd Trimester (28–40 weeks)",
        "4": "Nutrition Guide",
        "5": "Danger Signs",
        "6": "Mental Health",
        "7": "FAQs",
        "8": "Go Back"
    },
    "Child Growth Tracker": {
        "1": "Newborn (0–2 months)",
        "2": "Infant (3–12 months)",
        "3": "Toddler (1–3 years)",
        "4": "Go Back"
    },
    "Immunization Schedule": {
        "1": "Birth to 6 months",
        "2": "6–18 months",
        "3": "2–5 years",
        "4": "Go Back"
    },
    "Book Appointment – Schedule a clinic or doctor visit": {
        "1": "Antenatal Visit",
        "2": "Child Health Clinic",
        "3": "Postnatal Checkup",
        "4": "Family Planning",
        "5": "Cancel Appointment",
        "6": "Go Back"
    },
    "Language Options – Switch to Kiswahili": {
        "1": "Switch to Kiswahili",
        "2": "Switch to English",
        "3": "Go Back"
    },
    "More Services – Family planning, antenatal classes, etc": {
        "1": "Family Planning Advice",
        "2": "Antenatal Classes",
        "3": "Nutrition Counseling",
        "4": "Mental Health Support",
        "5": "Go Back"
    }
}

mother_child_keywords = [
    "pregnancy", "child growth", "immunization", "antenatal", "postnatal",
    "family planning", "nutrition", "mental health", "danger signs","Go Back"
]

greetings = ["hi", "hello", "hey", "good morning", "good evening", "howdy", "hola"]  # List of greetings

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "Please enter a message."})

        # Check if the user greeted the bot
        if any(greeting in user_message.lower() for greeting in greetings):
            user_context["menu"] = "main"
            return jsonify({
                "reply": "*Main Menu:*",
                "submenu": list(main_menu.values())
            })

        # Reset to main menu
        if user_message.lower() == "menu":
            user_context["menu"] = "main"
            return jsonify({
                "reply": "*Main Menu:*",
                "submenu": list(main_menu.values())
            })
        # Check if user input matches the mother/child related topics
        # if not any(keyword.lower() in user_message.lower() for keyword in mother_child_keywords):
        #     return jsonify({
        #         "reply": "Sorry, this bot is only for mother and child issues. Please ask questions related to pregnancy, child growth, immunization, family planning, etc."
        #     })

        # Handle main menu
        if user_context["menu"] == "main":
            for key, value in main_menu.items():
                if user_message.lower() == value.lower():
                    user_context["menu"] = value
                    submenu_items = submenus.get(value)
                    if submenu_items:
                        return jsonify({
                            "reply": f"*{value} Submenu:*",
                            "submenu": list(submenu_items.values())
                        })
                    else:
                        # If no submenu, generate reply from Gemini
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=value
                        )
                        reply = response.text
                        user_context["menu"] = "main"
                        return jsonify({"reply": reply, "submenu": list(main_menu.values())})

        # Handle submenu logic
        if user_context["menu"] in submenus:
            current_submenu = submenus[user_context["menu"]]
            for key, value in current_submenu.items():
                if user_message.lower() == value.lower():
                    if "go back" in value.lower():
                        user_context["menu"] = "main"
                        return jsonify({
                            "reply": "*Main Menu:*",
                            "submenu": list(main_menu.values())
                        })
                    else:
                        prompt = f"{user_context['menu']} - {value}"
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=prompt)
                        reply = response.text
                        return jsonify({
                            "reply": reply,
                            "submenu": list(current_submenu.values())
                        })

        if not any(keyword in user_message for keyword in mother_child_keywords):
            return jsonify({
                "reply": "This bot only answers questions related to pregnancy, child growth, immunization, and maternal health. Please select from the main menu."
            })
        # Fallback: Treat message as free input to Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_message
        )
        reply = response.text
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
