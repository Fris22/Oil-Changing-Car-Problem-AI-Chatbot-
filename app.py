from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from fuzzywuzzy import fuzz

app = Flask(__name__)

# Configure Flask Session
app.secret_key = "your_secret_key"  # Replace with a strong secret key
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data on the server
Session(app)

# Define the vehicle oil issues dataset
vehicle_oil_issues_dataset = [
    {
        "issue": "Knocking or Ticking Noise",
        "keywords": ["knocking sound", "ticking engine", "low oil", "poor lubrication", "viscosity loss", "air in oil"],
        "prompt": "Do you notice the noise only at certain speeds, or does it happen continuously?",
        "expected_keywords": ["certain speeds", "continuously"],
        "guided_response": {
            "certain speeds": "This might be related to specific operating conditions. Check the oil viscosity and ensure it's within the recommended range.",
            "continuously": "Continuous noise could indicate poor lubrication or oil contamination. Consider an immediate oil change and inspection."
        }
    },
    {
        "issue": "Squealing Noise",
        "keywords": ["squealing noise", "metal friction", "belt issue", "old oil", "lubrication problem"],
        "prompt": "Does the squealing stop after a few seconds, or does it continue as you drive?",
        "expected_keywords": ["stops after a few seconds", "continues while driving"],
        "guided_response": {
            "stops after a few seconds": "The issue might be related to initial startup friction. Verify the oil's quality and replace it if needed.",
            "continues while driving": "Persistent squealing could indicate a more severe lubrication issue or mechanical wear. Inspect belts and change the oil."
        }
    },
    {
        "issue": "Oil Pressure Warning",
        "keywords": ["oil pressure warning", "blocked oil filter", "pressure sensor fault", "low oil pressure"],
        "prompt": "Has your oil been changed recently, and do you know if the filter was checked?",
        "expected_keywords": ["recently changed", "not changed", "filter checked", "filter not checked"],
        "guided_response": {
            "recently changed": "Ensure that the correct oil type and filter were used during the last change.",
            "not changed": "Low oil pressure may result from overdue oil changes. Replace the oil and filter immediately.",
            "filter checked": "If the filter was checked, the issue might lie with the oil pump or pressure sensor.",
            "filter not checked": "Blocked or faulty filters can cause low pressure. Replace the filter and monitor the system."
        }
    },
    {
        "issue": "Low Oil Level Warning",
        "keywords": ["low oil level", "oil leak", "excessive oil use", "worn seals"],
        "prompt": "Have you noticed any oil spots where you park your vehicle?",
        "expected_keywords": ["yes", "no"],
        "guided_response": {
            "yes": "Oil spots suggest a leak. Inspect seals and gaskets, and refill oil as necessary.",
            "no": "If no leaks are visible, excessive consumption might be due to worn internal components. Check the oil regularly."
        }
    },
    {
        "issue": "Check Engine Light",
        "keywords": ["check engine light", "oil quality", "engine heat", "oil breakdown"],
        "prompt": "Have you experienced any recent performance issues like loss of power or poor fuel efficiency?",
        "expected_keywords": ["loss of power", "poor fuel efficiency", "no issues"],
        "guided_response": {
            "loss of power": "The oil may not be performing well under heat. Check the oil's quality and consider replacing it.",
            "poor fuel efficiency": "Poor efficiency might indicate that the engine is under strain. Check the oil and filter.",
            "no issues": "Check engine light could still indicate oil sensor problems or impending maintenance needs."
        }
    },
    {
        "issue": "Burning Smell",
        "keywords": ["burning oil smell", "oil leak on hot parts", "oil burning", "engine smell"],
        "prompt": "Does the smell appear stronger when the engine heats up or when you come to a stop?",
        "expected_keywords": ["engine heats up", "when stopping"],
        "guided_response": {
            "engine heats up": "Burning oil on hot engine parts might indicate a leak. Inspect seals and gaskets.",
            "when stopping": "This could be a sign of oil dripping onto components. Check for leaks and fix them immediately."
        }
    },
    {
        "issue": "Blue Smoke",
        "keywords": ["blue smoke", "piston wear", "oil in combustion", "engine rebuild"],
        "prompt": "Does the blue smoke come from the exhaust only on startup, or does it persist while driving?",
        "expected_keywords": ["on startup", "while driving"],
        "guided_response": {
            "on startup": "This might be caused by valve seals allowing oil into the combustion chamber. Inspect seals.",
            "while driving": "Persistent blue smoke could indicate piston wear or other serious issues. Seek a professional evaluation."
        }
    },
    {
        "issue": "White Smoke",
        "keywords": ["white smoke", "coolant in engine", "head gasket failure", "coolant levels"],
        "prompt": "Is there any loss of coolant in your radiator, or have you had to refill it frequently?",
        "expected_keywords": ["coolant loss", "no coolant loss"],
        "guided_response": {
            "coolant loss": "White smoke along with coolant loss could indicate a head gasket issue. Inspect immediately.",
            "no coolant loss": "White smoke might be due to water vapor. Monitor for recurring symptoms or seek advice."
        }
    },
    {
        "issue": "Dark, Sludgy Oil",
        "keywords": ["dark oil", "sludgy oil", "contaminants in oil", "oil change interval"],
        "prompt": "Has the oil not been changed in over the recommended interval?",
        "expected_keywords": ["overdue", "on schedule"],
        "guided_response": {
            "overdue": "Dark, sludgy oil indicates overdue changes. Replace the oil and filter immediately.",
            "on schedule": "Sludgy oil despite regular changes might indicate internal contamination. Have the engine inspected."
        }
    },
    {
        "issue": "Milky Oil",
        "keywords": ["milky oil", "coolant leak", "oil contamination", "head gasket issue"],
        "prompt": "Have you noticed a drop in coolant levels, or is the radiator fluid lower than usual?",
        "expected_keywords": ["coolant drop", "no coolant drop"],
        "guided_response": {
            "coolant drop": "Milky oil with coolant loss likely indicates a coolant leak. Inspect the head gasket.",
            "no coolant drop": "Milky oil without coolant loss might suggest moisture contamination. Replace the oil and monitor."
        }
    },

    {
        "issue": "Oil Leak Under Vehicle",
        "keywords": ["oil leak", "oil dripping", "gasket failure", "oil pan issue"],
        "prompt": "Can you see any visible oil puddle or spot under your parked vehicle?",
        "expected_keywords": ["yes", "no"],
        "guided_response": {
            "yes": "Visible oil puddles indicate a significant leak. Inspect the oil pan, gaskets, and seals.",
            "no": "If no leaks are visible, monitor the oil level closely for gradual loss."
        }
    },
    {
        "issue": "Sluggish Acceleration",
        "keywords": ["sluggish acceleration", "old oil", "engine resistance", "oil change"],
        "prompt": "Is the engine generally harder to accelerate, or does it happen only when the engine is cold?",
        "expected_keywords": ["harder generally", "only when cold"],
        "guided_response": {
            "harder generally": "Consistent sluggishness could indicate thick or old oil. Replace the oil and filter.",
            "only when cold": "Cold start sluggishness might be normal but can improve with the correct oil grade."
        }
    },
    {
        "issue": "Overheating",
        "keywords": ["overheating", "thick oil", "insufficient lubrication", "oil change needed"],
        "prompt": "Does overheating happen when driving at high speeds or while idling?",
        "expected_keywords": ["high speeds", "while idling"],
        "guided_response": {
            "high speeds": "High-speed overheating might indicate oil breakdown. Check and replace the oil.",
            "while idling": "Idling overheating could point to poor cooling or thick oil. Check both systems."
        }
    },
    {
        "issue": "Off-Road/Dusty Conditions",
        "keywords": ["off-road oil", "dusty conditions", "heavy-duty filter", "oil change frequently"],
        "prompt": "Do you drive in dusty or rough conditions often, and when was the last oil change?",
        "expected_keywords": ["drive often", "last change unknown", "last change recent"],
        "guided_response": {
            "drive often": "Frequent off-road driving requires high-quality oil and more frequent changes. Replace the oil.",
            "last change unknown": "If the last change is unknown, replace the oil and start a regular schedule.",
            "last change recent": "If recently changed, use heavy-duty filters for off-road conditions."
        }
    },
    {
        "issue": "High-Speed Driving",
        "keywords": ["high speed", "oil breakdown", "engine heat", "performance synthetic oil"],
        "prompt": "Does the engine run at high RPMs frequently, such as on highways or during acceleration?",
        "expected_keywords": ["frequently", "rarely"],
        "guided_response": {
            "frequently": "Frequent high RPMs require synthetic oil for better performance and protection.",
            "rarely": "If high RPMs are rare, ensure oil grade matches vehicle specifications."
        }
    },
    {
        "issue": "Valve Train Noise",
        "keywords": ["valve noise", "poor lubrication", "engine ticking", "oil change needed"],
        "prompt": "Is the ticking noise mostly noticeable at idle, or is it present when you accelerate as well?",
        "expected_keywords": ["at idle", "when accelerating"],
        "guided_response": {
            "at idle": "Noise at idle might indicate low oil pressure. Inspect the oil and change if necessary.",
            "when accelerating": "Acceleration noise suggests poor lubrication. Replace the oil and inspect further."
        }
    },
    {
        "issue": "Carbon Buildup on Valves",
        "keywords": ["carbon buildup", "valve residue", "oil burning", "use cleaner additives"],
        "prompt": "Have you had the engine inspected recently, and are there signs of residue on the valves?",
        "expected_keywords": ["inspected", "not inspected"],
        "guided_response": {
            "inspected": "If inspected and residue is present, use cleaner additives or seek professional cleaning.",
            "not inspected": "Have the engine inspected for carbon buildup and consider preventive maintenance."
        }
    },
    {
        "issue": "Oil Consumption",
        "keywords": ["excessive oil use", "oil consumption", "frequent refills", "oil burns quickly"],
        "prompt": "How often do you find yourself adding oil between scheduled oil changes?",
        "expected_keywords": ["frequently", "rarely"],
        "guided_response": {
            "frequently": "Frequent refills suggest excessive consumption. Inspect for leaks or worn components.",
            "rarely": "If rare, monitor the oil levels regularly and ensure proper maintenance."
        }
    },
    {
        "issue": "Oil Smell Inside Car",
        "keywords": ["oil smell in cabin", "oil fumes", "smell inside car", "ventilation issue"],
        "prompt": "Do you smell the oil mostly when the car is idling or while driving?",
        "expected_keywords": ["when idling", "while driving"],
        "guided_response": {
            "when idling": "Oil smell at idle might indicate a leak or ventilation issue. Inspect the system.",
            "while driving": "Smell while driving could suggest oil fumes entering the cabin. Check for leaks."
        }
    },
    {
        "issue": "Oil Foaming",
        "keywords": ["foamy oil", "air in oil", "oil contamination", "oil bubbles"],
        "prompt": "Have you observed any foam on the dipstick when checking the oil?",
        "expected_keywords": ["yes", "no"],
        "guided_response": {
            "yes": "Foamy oil indicates air contamination. Replace the oil and check for potential entry points.",
            "no": "If no foam is visible, monitor oil levels and check during routine maintenance."
        }
    }
]


# Initialize conversation state within session
def initialize_session():
    session['conversation_state'] = {
        "current_issue": None,
        "follow_up_needed": False,
        "possible_matches": []
    }

# Refined function for more accurate matching with direct keyword match and fuzzy matching
def find_possible_matches(user_input):
    user_input_lower = user_input.lower()
    matches = []

    for entry in vehicle_oil_issues_dataset:
        total_match_score = 0
        matched_keywords = 0

        # Direct keyword match
        for keyword in entry["keywords"]:
            if keyword.lower() in user_input_lower:
                matches.append((entry, 100, 1))  # Perfect score for direct match
                break
        else:
            # Fuzzy matching fallback
            for keyword in entry["keywords"]:
                score = fuzz.ratio(user_input_lower, keyword.lower())
                if score > 60:  # Fuzzy match threshold
                    total_match_score += score
                    matched_keywords += 1

            if matched_keywords > 0:
                avg_score = total_match_score / matched_keywords
                matches.append((entry, avg_score, matched_keywords))

    matches.sort(key=lambda x: (x[1], x[2]), reverse=True)  # Sort by score and match count
    return matches

# Get chatbot response based on user input
def get_chatbot_response(user_input):
    if 'conversation_state' not in session:
        initialize_session()
    
    conversation_state = session['conversation_state']

    user_input_lower = user_input.lower()

    # Reset state if the user ends the conversation
    if "thank you" in user_input_lower or "problem solved" in user_input_lower:
        initialize_session()
        return "You're welcome! If you have more questions, feel free to ask anytime."

    # Handle user selection from multiple matches
    if conversation_state["possible_matches"]:
        try:
            selected_number = int(user_input.strip()) - 1
            if 0 <= selected_number < len(conversation_state["possible_matches"]):
                selected_issue = conversation_state["possible_matches"][selected_number]
                conversation_state["current_issue"] = selected_issue
                conversation_state["possible_matches"] = []
                conversation_state["follow_up_needed"] = True
                session.modified = True
                return f"You selected: {selected_issue['issue']}. {selected_issue['prompt']}"
            else:
                return "Please select a valid number from the list of issues."
        except ValueError:
            return "I didn't understand that. Please reply with the number of the issue you're experiencing."

    # Find possible matches if no issue is currently selected
    if not conversation_state["current_issue"]:
        matches = find_possible_matches(user_input)
        if not matches:
            return "I'm not sure about the issue. Could you provide more details? Common symptoms include noises, warning lights, or leaks."

        if len(matches) == 1:
            selected_issue = matches[0][0]
            conversation_state["current_issue"] = selected_issue
            conversation_state["follow_up_needed"] = True
            session.modified = True
            return f"I think it might be {selected_issue['issue']}. {selected_issue['prompt']}"

        conversation_state["possible_matches"] = [match[0] for match in matches]
        session.modified = True
        response = "I found multiple possible issues based on your description:\n"
        for i, match in enumerate(matches, start=1):
            response += f"{i}. {match[0]['issue']} - Keywords: {', '.join(match[0]['keywords'])}\n"
        response += "\nPlease reply with the number corresponding to the issue you're experiencing."
        return response

    # Handle follow-up responses for a specific issue
    if conversation_state["follow_up_needed"]:
        current_issue = conversation_state["current_issue"]
        for expected_keyword in current_issue["expected_keywords"]:
            if expected_keyword in user_input_lower:
                response = current_issue["guided_response"].get(expected_keyword, "I didn't understand that response.")
                initialize_session()  # Reset conversation state after resolving issue
                return response

        return f"Could you clarify further? {current_issue['prompt']}"

    return "I'm sorry, I couldn't understand your input. Could you provide more details?"

# Route to render the homepage (chatbot interface)
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle chat requests
@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form['user_input']
    response = get_chatbot_response(user_input)
    return jsonify({"response": response})

# Route to start a new chat session
@app.route('/new_chat', methods=['POST'])
def new_chat():
    session.clear()  # Clear session to reset conversation
    initialize_session()  # Reinitialize state
    return jsonify({"message": "New chat session started."})

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)