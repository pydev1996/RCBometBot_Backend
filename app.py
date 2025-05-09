from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
import os

# Load environment variables from .env
load_dotenv()

# Setup Gemini client
api_key = os.getenv("GENAI_API_KEY")
client = genai.Client(api_key=api_key)

app = Flask(__name__)

# Track user state
user_context = {
    "menu": "main",
    "language": "english"
}

# Main menu and submenus
main_menu = {
   "Pregnancy Tips": {
        "1st Trimester (0–12 weeks)":"",
        "2nd Trimester (13–27 weeks)":"",
        "3rd Trimester (28–40 weeks)":"",
         "Nutrition Guide":"",
        "Danger Signs":"",
        "Mental Health":"",
        "FAQs":"",
        "Go Back":""
    },
    "Child Growth Tracker": {
        "Newborn (0–2 months)": "",
        "Infant (3–12 months)": "",
        "Toddler (1–3 years)": "",
        "Go Back": ""
    },
    "Immunization Schedule": {
        "Birth to 6 months": "",
        "6–18 months": "",
        "2–5 years": "",
        "Go Back": ""
    },
    "Emergency Help": {},
    "Live Chat with Nurse": {},
    "Health Articles": {},
    "Book Appointment – Schedule a clinic or doctor visit": {
        "Antenatal Visit": "",
        "Child Health Clinic": "",
        "Postnatal Checkup": "",
        "Family Planning": "",
        "Cancel Appointment": "",
        "Go Back": ""
    },
    "Language Options – Switch to Kiswahili": {
        "Switch to Kiswahili": "",
        "Switch to English": "",
        "Go Back": ""
    },
    "More Services – Family planning, antenatal classes, etc": {
        "Family Planning Advice": "",
        "Antenatal Classes": "",
        "Nutrition Counseling": "",
        "Mental Health Support": "",
        "Go Back": ""
    }
}

keywords = [
    "pregnancy", "child", "baby", "growth", "immunization", "antenatal", "postnatal",
    "mental health", "nutrition", "family planning", "clinic", "appointment"
]
greetings = ["hi", "hello", "hey", "good morning", "good evening", "howdy", "hola"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        message = request.json.get("message", "").strip()

        if not message:
            return jsonify({"reply": "Please enter a message."})

        # Handle greetings
        if message.lower() in greetings or message.lower() == "menu":
            user_context["menu"] = "main"
            return jsonify({
                "reply": "*Main Menu:*" if user_context["language"] == "english" else "*Menyu Kuu:*",
                "submenu": list(main_menu.keys())
            })

        # Language Switching
        if user_context["menu"] == "Language Options – Switch to Kiswahili":
            if message == "Switch to Kiswahili":
                user_context["language"] = "kiswahili"
                user_context["menu"] = "main"
                return jsonify({
                    "reply": "✅ *Umechagua Kiswahili.*\n\n*Menyu Kuu:*",
                    "submenu": list(main_menu.keys())
                })
            elif message == "Switch to English":
                user_context["language"] = "english"
                user_context["menu"] = "main"
                return jsonify({
                    "reply": "✅ *You have switched to English.*\n\n*Main Menu:*",
                    "submenu": list(main_menu.keys())
                })
            elif message.lower() == "go back":
                user_context["menu"] = "main"
                return jsonify({
                    "reply": "*Main Menu:*",
                    "submenu": list(main_menu.keys())
                })

        # Handle main menu selection
        if user_context["menu"] == "main":
            if message in main_menu:
                submenu = main_menu[message]
                user_context["menu"] = message
                if submenu:
                    return jsonify({
                        "reply": f"*{message} Submenu:*",
                        "submenu": list(submenu.keys())
                    })
                else:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=message
                    )
                    final_reply = response.text
                    if user_context["language"] == "kiswahili":
                        translated = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=f"Translate this into Kiswahili: {final_reply}"
                        )
                        final_reply = translated.text
                    user_context["menu"] = "main"
                    return jsonify({
                        "reply": final_reply,
                        "submenu": list(main_menu.keys())
                    })

        # Submenu selection
        current_menu = user_context["menu"]
        if current_menu in main_menu:
            submenu = main_menu[current_menu]
            if message in submenu:
                if message.lower() == "go back":
                    user_context["menu"] = "main"
                    return jsonify({
                        "reply": "*Main Menu:*",
                        "submenu": list(main_menu.keys())
                    })
                else:
                    prompt = f"{current_menu} - {message}"
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    final_reply = response.text
                    if user_context["language"] == "kiswahili":
                        translated = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=f"Translate this into Kiswahili: {final_reply}"
                        )
                        final_reply = translated.text
                    return jsonify({
                        "reply": final_reply,
                        "submenu": list(submenu.keys())
                    })

        # Health-related free text queries
        if any(keyword in message.lower() for keyword in keywords):
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=message
            )
            final_reply = response.text
            if user_context["language"] == "kiswahili":
                translated = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"Translate this into Kiswahili: {final_reply}"
                )
                final_reply = translated.text
            return jsonify({"reply": final_reply})

        # Fallback
        return jsonify({
            "reply": "Please use the buttons or ask about pregnancy, child health, or related services."
        })

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
