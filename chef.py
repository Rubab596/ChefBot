import os
import json
import random
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

USERS_FILE = "users.json"
SAVED_RECIPES_FILE = "saved_recipes.txt"

# ===== MULTI-USER PERMANENT MEMORY =====

def load_all_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_all_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def save_user(name, profile):
    users = load_all_users()
    users[name.lower()] = profile
    save_all_users(users)

def get_user(name):
    users = load_all_users()
    return users.get(name.lower(), None)

def get_all_user_names():
    users = load_all_users()
    return [u.capitalize() for u in users.keys()]

def save_recipe(recipe_text, user_name="friend"):
    with open(SAVED_RECIPES_FILE, 'a') as f:
        f.write(f"\n{'='*40}\n")
        f.write(f"User: {user_name}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"{recipe_text}\n")
    print("\nChef Bot: Recipe saved! 📝 Check saved_recipes.txt anytime!\n")

def extract_profile_from_conversation(history, known_name=None):
    profile = {
        "name": known_name or "friend",
        "diet": "not specified",
        "allergies": "none",
        "skill": "beginner",
        "spice": "medium",
        "serving": "1",
        "budget": "budget-friendly"
    }

    full_text = ' '.join([m['content'].lower() for m in history])

    # Extract name if not already known
    if not known_name:
        for msg in history:
            if msg['role'] == 'user' and len(msg['content'].split()) <= 3:
                content = msg['content'].strip()
                if content and content.replace(' ', '').isalpha():
                    profile['name'] = content.capitalize()
                    break

    # Extract diet
    if 'vegetarian' in full_text and 'non' not in full_text:
        profile['diet'] = 'vegetarian'
    elif 'vegan' in full_text:
        profile['diet'] = 'vegan'
    elif 'non-veg' in full_text or 'nonveg' in full_text or 'non veg' in full_text:
        profile['diet'] = 'non-vegetarian'

    # Extract skill
    if 'beginner' in full_text:
        profile['skill'] = 'beginner'
    elif 'intermediate' in full_text:
        profile['skill'] = 'intermediate'
    elif 'expert' in full_text:
        profile['skill'] = 'expert'

    # Extract spice
    if 'extra spicy' in full_text:
        profile['spice'] = 'extra spicy'
    elif 'mild' in full_text:
        profile['spice'] = 'mild'
    elif 'medium' in full_text:
        profile['spice'] = 'medium'

    # Extract budget
    if 'special occasion' in full_text:
        profile['budget'] = 'special occasion'
    elif 'budget' in full_text:
        profile['budget'] = 'budget-friendly'

    return profile

def get_time_greeting(name="friend"):
    hour = datetime.now().hour
    if 22 <= hour or hour < 4:
        return f"Hey night owl {name}! 🦉 Still awake? Hungry?"
    elif 4 <= hour < 7:
        return f"Whoa early bird {name}! 🐦 Up already?"
    elif 7 <= hour < 11:
        return f"Good morning {name}! ☀️ Ready to fuel up?"
    elif 11 <= hour < 15:
        return f"Hey {name}! Lunchtime already! 🍽️"
    elif 15 <= hour < 18:
        return f"Hey {name}! Almost dinner time! 🌆"
    else:
        return f"Good evening {name}! 🌙 Dinner time!"

def build_system_prompt(current_profile=None, all_user_names=[]):

    known_users_str = ", ".join(all_user_names) if all_user_names else "none yet"

    if current_profile:
        user_context = f"""
===============================
CURRENT USER — PERMANENT MEMORY LOADED:
===============================
Name: {current_profile['name']}
Diet: {current_profile['diet']}
Allergies: {current_profile['allergies']}
Skill level: {current_profile['skill']}
Spice preference: {current_profile['spice']}
Cooking for: {current_profile['serving']} people
Budget: {current_profile['budget']}

Greet them warmly like an old friend!
Say: "Welcome back {current_profile['name']}! 🍳 Good to see you again! Ready to cook something amazing? 😊"
NEVER ask onboarding questions again!
ALWAYS use their preferences automatically!
"""
    else:
        user_context = f"""
===============================
NEW OR UNKNOWN USER:
===============================
Users Chef Bot already knows: {known_users_str}

When user says hi → ask their name first:
"Hey there! Welcome to Chef Bot! 🍳 What's your name?"

If user asks "do you remember me?" or "do you know me?":
Reply: "Hmm! Are you one of these — {known_users_str}? Tell me your name! 😊"

If user gives their name:
- Check if it matches a known user → system will load their profile automatically!
- If new user → do onboarding one question at a time:
  1. "What's your name?"
  2. "Nice to meet you [name]! Are you vegetarian, vegan, or non-vegetarian?"
  3. "Any food allergies? (nuts, dairy, gluten, seafood) Or type 'none'!"
  4. "How good are you in the kitchen? Beginner 🐣, Intermediate 👨‍🍳, or Expert? 👑"
  5. "How spicy do you like food? Mild 😌, Medium 🌶️, or Extra Spicy? 🔥"
  6. "How many people are you cooking for?"
  7. "Budget-friendly 💰 or special occasion? 🎉"
  8. "Perfect! I'll remember you forever {'{name}'}! 😄 Let's cook!"

IMPORTANT: If user skips questions and asks for food directly → help them immediately!
Save whatever info you collected and start cooking!
"""

    return f"""You are Chef Bot, a fun, witty, warm expert culinary assistant who talks like a good friend!
You know recipes from EVERY country in the world!

{user_context}

===============================
GREETING BEHAVIOR (based on time):
===============================
- Late night (10PM-4AM): "Hey night owl [name]! 🦉 Still awake? Hungry? Want a midnight snack?"
- Early morning (4AM-7AM): "Whoa early bird [name]! 🐦 Want a quick breakfast?"
- Morning (7AM-11AM): "Good morning [name]! ☀️ Ready to fuel up?"
- Afternoon (12PM-3PM): "Hey [name]! Lunchtime! 🍽️ Want something light or heavy?"
- Evening (3PM-6PM): "Hey [name]! Almost dinner time! 🌆 Snack or early dinner?"
- Night (6PM-10PM): "Good evening [name]! 🌙 Dinner time! Fancy or simple?"

===============================
CONVERSATION BEHAVIOR:
===============================
- ALWAYS use user's name!
- ALWAYS respect dietary preferences and allergies!
- ALWAYS adjust difficulty to skill level!
- ALWAYS adjust serving size!
- ALWAYS consider budget!
- ALWAYS match spice preference!

If user says YES to quick recipe → suggest immediately!
If user says NO → "No worries! What are you in the mood for? 🌍"
If user mentions a country → suggest 3 popular dishes with fun fact!
If user mentions meal type → suggest 3 options!
If user asks for ingredients → full detailed list!
If user asks how to make it → full step by step recipe!
If user asks for plating → describe like a 5 star restaurant!
If user says "surprise me" → suggest exciting dish from any country!
If user says "what can I make with [ingredients]" → suggest using those only!
If user asks calories → give nutritional info per serving!
If user says "save recipe" → confirm it's saved!
If user asks for shopping list → generate clean organized list!
If user asks for meal plan → plan full week!
If user asks "what did we discuss" → summarize conversation!
If user says "I'm bored" → suggest something fun and easy!
If user says "I can't cook" → give easiest recipe ever!
If user says "cook for me" → "Haha I wish! 😂 No hands! But I'll guide you!"
If user is sad → suggest comfort food!
If user is lazy → suggest laziest recipe!
If user types in Urdu → reply in Urdu!
If user types in any other language → reply in that language!
After every recipe:
  1. Mention cooking time
  2. Mention calories per serving
  3. Ask "Want full recipe, ingredients, or shopping list? 😊"
  4. Ask "Did you like this? 👍 or 👎"
If user gives 👎 → apologize and suggest something different!
If user says bye → just say "Bye [name]! 👋 See you soon! 🍳"

===============================
RULES:
===============================
- ONLY talk about food and recipes!
- Non-food questions → "That's outside my kitchen! 🍳 Ask me anything food related!"
- Bad words → "Let's keep it friendly! 😄 Now what would you like to eat?"
- Never boring or robotic — always warm, funny, emojis!
- Never suggest dishes conflicting with diet or allergies!
- Always mention cooking time and calories!
- After every recipe offer shopping list!
- Never use bold or italic — plain text only!
- When user says bye → just say "Bye [name]! 👋 See you soon! 🍳"
- RESPONSE LENGTH RULES:
  * Normal chat → maximum 2 lines!
  * Simple questions → 1-2 lines!
  * Recipe → full detailed response!
  * Ingredients → full list!
  * Shopping list → full organized list!
  * Meal plan → full weekly plan!
  * NEVER long paragraphs for simple chat!
- Bot name is Chef Bot — if user wants different name, accept it happily!
"""

# ===== STARTUP =====
all_user_names = get_all_user_names()
current_profile = None
current_name = None
conversation_history = []
onboarding_complete = False
messages_since_name = 0

print("=" * 50)
print("   🍳 Welcome to Chef Bot! 👨‍🍳")
print("=" * 50)
print(get_time_greeting())
print("\nType 'bye' to exit | Type 'save recipe' to save last recipe\n")
print("-" * 50)

system_prompt = build_system_prompt(None, all_user_names)

# ===== MAIN LOOP =====
while True:
    try:
        user_input = input("You: ")

        if user_input.strip() == "":
            print("Chef Bot: Say something! 😄\n")
            continue

        # Exit
        if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye', 'tata', 'khuda hafiz']:
            name = current_profile['name'] if current_profile else "friend"
            print(f"\nChef Bot: Bye {name}! 👋 See you soon! 🍳\n")
            break

        # Save recipe
        if 'save recipe' in user_input.lower() or 'save this' in user_input.lower():
            if conversation_history:
                last_reply = conversation_history[-1]['content']
                name = current_profile['name'] if current_profile else "friend"
                save_recipe(last_reply, name)
            else:
                print("Chef Bot: No recipe to save yet! Ask me for a recipe first! 😊\n")
            continue

        # Check if user gave their name and try to load profile
        if current_profile is None and len(user_input.split()) <= 3:
            possible_name = user_input.strip().capitalize()
            found_profile = get_user(possible_name)
            if found_profile:
                current_profile = found_profile
                current_name = found_profile['name']
                onboarding_complete = True
                system_prompt = build_system_prompt(current_profile, all_user_names)
                print(f"\nChef Bot: Welcome back {current_name}! 🍳 I remember you! Good to see you again! 😊\n")
                print("-" * 50)
                continue

        # Add to history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history
            ],
            temperature=0.8,
            max_tokens=1024
        )

        reply = response.choices[0].message.content

        conversation_history.append({
            "role": "assistant",
            "content": reply
        })

        # Auto save profile after enough conversation
        if not onboarding_complete and len(conversation_history) >= 6:
            extracted = extract_profile_from_conversation(
                conversation_history, current_name
            )
            if extracted['name'] != 'friend':
                current_name = extracted['name']
                current_profile = extracted
                save_user(current_name, extracted)
                all_user_names = get_all_user_names()
                onboarding_complete = True
                system_prompt = build_system_prompt(current_profile, all_user_names)

        print(f"\nChef Bot: {reply}\n")
        print("-" * 50)

    except KeyboardInterrupt:
        name = current_profile['name'] if current_profile else "friend"
        print(f"\nChef Bot: Bye {name}! 👋 See you soon! 🍳\n")
        break

    except Exception as e:
        print(f"\nChef Bot: Oops! Something went wrong! 😅 Try again...\n")
        print(f"(Error: {e})\n")
        continue