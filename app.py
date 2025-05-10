from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
import os
import spacy
import subprocess

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


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
nlp = spacy.load("en_core_web_sm")
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
    # "Live Chat with Nurse": {},
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
    # Mother health
    "pregnancy", "prenatal care", "antenatal", "postnatal", "postpartum", "maternal health",
    "labor", "delivery", "childbirth", "c-section", "miscarriage", "stillbirth",
    "breastfeeding", "lactation", "birth plan", "birth control", "contraception",
    "family planning", "maternal nutrition", "prenatal vitamins", "iron supplements",
    "folic acid", "morning sickness", "anemia", "high-risk pregnancy", "gynecology",
    "women's health", "midwife", "doula", "ob-gyn", "maternal mental health",
    "postpartum depression", "maternal checkup", "maternity leave","pregnant",

    # Child health
    "baby", "infant", "toddler", "child development", "child health", "immunization",
    "vaccination", "growth chart", "milestones", "weaning", "formula feeding",
    "pediatrician", "newborn care", "skin-to-skin contact", "colic", "jaundice",
    "diaper rash", "teething", "sleep schedule", "feeding schedule", "child nutrition",
    "stunting", "underweight", "malnutrition", "deworming", "vitamin a", "supplements",
    "oral rehydration", "diarrhea", "fever", "cough", "flu", "measles", "polio",
    "pneumonia", "neonatal care",

    # Health services & support
    "health tips", "clinic", "health facility", "nurse", "doctor", "appointment",
    "vaccination schedule", "growth monitoring", "health worker", "outreach",
    "health records", "checkup", "referral", "emergency care", "ambulance",
    "mobile clinic", "insurance", "nhif", "m-pesa", "hospital", "maternal shelter",
    "anc visits", "pnc visits","breathing", "wheezing", "shortness of breath", "asthma", "respiratory problem",
"chest congestion", "cough", "bronchitis", "pneumonia", "difficulty breathing",# Mother Health
    "pregnancy symptoms", "pregnancy test", "first trimester", "second trimester", "third trimester", "pregnancy complications",
    "high blood pressure", "gestational diabetes", "preeclampsia", "labor pains", "induced labor", "epidural", "natural birth", "home birth",
    "vaginal birth", "birth trauma", "pelvic floor", "postpartum care", "perineal tear", "Kegel exercises", "breast pump",
    "baby blues", "perinatal depression", "parenting support", "postpartum care plan", "maternity clothing", "postpartum fitness",
    "maternity support group", "mental health support", "lactation consultant", "birth recovery", "cesarean recovery",

    # Child Health
    "breastfeeding tips", "exclusive breastfeeding", "baby formula", "breast milk storage", "bottle feeding",
    "baby food", "solid food introduction", "baby-led weaning", "milk allergy", "diapering tips", "baby massage", "infant reflexes",
    "child vaccination schedule", "baby health checkup", "baby sleep patterns", "baby growth monitoring", "baby bonding",
    "toddler tantrums", "toddler behavior", "child speech development", "developmental milestones", "motor skills", "gross motor skills", "fine motor skills",
    "pediatric vaccinations", "baby ear infection", "hand-foot-and-mouth disease", "chickenpox", "diphtheria", "whooping cough", "tuberculosis", "yellow fever",
    "child safety", "babyproofing", "childproofing home", "choking hazard", "car seat safety", "swaddle safety",

    # Health Services & Support
    "maternity ward", "obstetrician", "birth center", "antenatal care package", "health insurance coverage", "telemedicine", "family counseling",
    "child health center", "pediatric clinic", "immunization drive", "nutrition education", "health campaigns", "well-baby visits", "support group for mothers",
    "community health workers", "mobile health unit", "health education", "wellness check", "public health initiatives", "health outreach programs"


]

def nlp_match(message, keywords):
    # Process the message through spaCy NLP model
    doc = nlp(message.lower())

    # Check for keyword matches and named entities
    for keyword in keywords:
        if keyword in message.lower():
            return True

    # Optional: Check if the message contains specific named entities (e.g., pregnancy, healthcare, etc.)
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'GPE', 'PERSON', 'MONEY']:  # You can change this based on your requirements
            return True

    return False

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
        # if any(keyword in message.lower() for keyword in keywords):
        #     response = client.models.generate_content(
        #         model="gemini-2.0-flash",
        #         contents=message
        #     )
        #     final_reply = response.text
        #     if user_context["language"] == "kiswahili":
        #         translated = client.models.generate_content(
        #             model="gemini-2.0-flash",
        #             contents=f"Translate this into Kiswahili: {final_reply}"
        #         )
        #         final_reply = translated.text
        #     return jsonify({"reply": final_reply})

        # # Fallback
        # return jsonify({
        #     "reply": "Please use the buttons or ask about pregnancy, child health, or related services."
        # })
        if nlp_match(message, keywords):
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=message
            )
            final_reply = response.text
            
            # Translate if required
            if user_context["language"] == "kiswahili":
                translated = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"Translate this into Kiswahili: {final_reply}"
                )
                final_reply = translated.text
            
            return jsonify({"reply": final_reply})

        # Fallback if no match is found
        return jsonify({
            "reply": "Please use the buttons or ask about pregnancy, child health, or related services."
        })
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
