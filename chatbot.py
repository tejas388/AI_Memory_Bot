import os
import sqlite3
import hashlib
import secrets
import json

from dotenv import load_dotenv
from mem0 import MemoryClient
from google import genai


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()

MEM0_API_KEY = os.getenv("MEM0_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not MEM0_API_KEY:
    raise ValueError("MEM0_API_KEY is missing from .env")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")


# ============================================================
# Initialize APIs
# ============================================================

memory_client = MemoryClient(
    api_key=MEM0_API_KEY
)

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# Database
# ============================================================

DATABASE = "users.db"


def initialize_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


# ============================================================
# Password hashing
# ============================================================

def hash_password(password, salt=None):

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return password_hash, salt


def verify_password(password, stored_hash, salt):

    password_hash, _ = hash_password(
        password,
        salt
    )

    return secrets.compare_digest(
        password_hash,
        stored_hash
    )


# ============================================================
# Register user
# ============================================================

def register():

    print()
    print("================================")
    print("          REGISTER")
    print("================================")
    print()

    username = input("Choose a username: ").strip().lower()

    if not username:

        print()
        print("Username cannot be empty.")
        print()

        return False


    if len(username) < 3:

        print()
        print("Username must contain at least 3 characters.")
        print()

        return False


    password = input("Choose a password: ")

    if len(password) < 6:

        print()
        print("Password must contain at least 6 characters.")
        print()

        return False


    confirm_password = input(
        "Confirm password: "
    )


    if password != confirm_password:

        print()
        print("Passwords do not match.")
        print()

        return False


    password_hash, salt = hash_password(
        password
    )


    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    try:

        cursor.execute(
            """
            INSERT INTO users
            (username, password_hash, salt)
            VALUES (?, ?, ?)
            """,
            (
                username,
                password_hash,
                salt
            )
        )

        connection.commit()

        print()
        print("Account created successfully!")
        print(
            f"Your username is: {username}"
        )
        print()

        return True

    except sqlite3.IntegrityError:

        print()
        print(
            "That username already exists."
        )
        print()

        return False

    finally:

        connection.close()


# ============================================================
# Login
# ============================================================

def login():

    print()
    print("================================")
    print("            LOGIN")
    print("================================")
    print()

    username = input(
        "Username: "
    ).strip().lower()

    password = input(
        "Password: "
    )


    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT password_hash, salt
        FROM users
        WHERE username = ?
        """,
        (username,)
    )


    user = cursor.fetchone()

    connection.close()


    if user is None:

        print()
        print("Invalid username or password.")
        print()

        return None


    stored_hash = user[0]
    salt = user[1]


    if not verify_password(
        password,
        stored_hash,
        salt
    ):

        print()
        print("Invalid username or password.")
        print()

        return None


    print()
    print("Login successful!")
    print(
        f"Welcome back, {username}!"
    )
    print()

    return username


# ============================================================
# Search memories
# ============================================================

def search_memories(
    user_message,
    user_id
):

    try:

        return memory_client.search(
            user_message,
            filters={
                "user_id": user_id
            }
        )

    except Exception as error:

        print()
        print("Memory search error:")
        print(error)
        print()

        return {
            "results": []
        }


# ============================================================
# Get all memories
# ============================================================

def get_all_memories(user_id):

    try:

        memories = memory_client.get_all(
            filters={
                "user_id": user_id
            }
        )

        return memories.get(
            "results",
            []
        )

    except Exception as error:

        print()
        print("Memory retrieval error:")
        print(error)
        print()

        return []


# ============================================================
# Smart memory filter
# ============================================================

def should_remember(user_message):

    memory_prompt = f"""
You are a memory filtering system.

Determine whether the user's message contains
useful LONG-TERM information about the user.

REMEMBER:

- Name
- Education
- Career
- Skills
- Programming language preferences
- Hobbies
- Interests
- Long-term goals
- Personal preferences
- Projects they are working on
- Important recurring activities

DO NOT REMEMBER:

- General questions
- Temporary requests
- Requests for explanations
- Requests for project ideas
- General knowledge questions
- Assistant recommendations
- Information about other people
- Instructions given to the AI
- Casual conversation without useful long-term information

Examples:

"My favorite programming language is Python."
=> REMEMBER

"I am a final-year computer science student."
=> REMEMBER

"I am building an AI project."
=> REMEMBER

"What is Python?"
=> IGNORE

"Explain machine learning."
=> IGNORE

"Give me some project ideas."
=> IGNORE

Return ONLY valid JSON.

Use exactly:

{{
    "remember": true
}}

or:

{{
    "remember": false
}}

User message:

{user_message}
"""


    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=memory_prompt
        )

        result_text = response.text.strip()

        result_text = result_text.replace(
            "```json",
            ""
        )

        result_text = result_text.replace(
            "```",
            ""
        )

        result_text = result_text.strip()


        result = json.loads(
            result_text
        )


        return result.get(
            "remember",
            False
        )


    except Exception as error:

        print()
        print("Memory filter error:")
        print(error)
        print()

        return False


# ============================================================
# Save memory
# ============================================================

def save_memory(
    user_message,
    user_id
):

    try:

        return memory_client.add(
            [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            user_id=user_id
        )

    except Exception as error:

        print()
        print("Memory save error:")
        print(error)
        print()

        return None


# ============================================================
# Chat application
# ============================================================

def start_chat(user_id):

    print("================================")
    print("       Tejas AI Memory Bot")
    print("================================")
    print()

    print(
        f"Logged in as: {user_id}"
    )

    print()

    print("Commands:")
    print("  /memory       - Show your stored memories")
    print("  /forget N     - Delete memory number N")
    print("  /help         - Show available commands")
    print("  /logout       - Logout")
    print("  exit          - Quit")
    print()


    conversation_history = []


    while True:

        user_message = input(
            "You: "
        ).strip()


        # ====================================================
        # Exit
        # ====================================================

        if user_message.lower() == "exit":

            print("Goodbye!")

            raise SystemExit


        # ====================================================
        # Logout
        # ====================================================

        if user_message.lower() == "/logout":

            print()
            print(
                f"Logging out {user_id}..."
            )
            print()

            return


        # ====================================================
        # Help
        # ====================================================

        if user_message.lower() == "/help":

            print()
            print("Available commands:")
            print("  /memory       - Show your stored memories")
            print("  /forget N     - Delete memory number N")
            print("  /help         - Show available commands")
            print("  /logout       - Logout")
            print("  exit          - Quit")
            print()

            continue


        # ====================================================
        # Show memories
        # ====================================================

        if user_message.lower() == "/memory":

            print()
            print(
                "Retrieving your memories..."
            )
            print()

            memories = get_all_memories(
                user_id
            )


            if not memories:

                print(
                    "No memories found."
                )

            else:

                print(
                    f"Memories for user '{user_id}':"
                )
                print()

                for index, memory in enumerate(
                    memories,
                    start=1
                ):

                    memory_text = memory.get(
                        "memory",
                        "Unknown memory"
                    )

                    print(
                        f"{index}. {memory_text}"
                    )

                print()
                print(
                    f"Total memories: {len(memories)}"
                )

            print()

            continue


        # ====================================================
        # Forget memory
        # ====================================================

        if user_message.lower().startswith(
            "/forget"
        ):

            parts = user_message.split()


            if len(parts) != 2:

                print()
                print(
                    "Usage: /forget N"
                )
                print()

                continue


            try:

                memory_number = int(
                    parts[1]
                )

            except ValueError:

                print()
                print(
                    "Memory number must be a number."
                )
                print()

                continue


            memories = get_all_memories(
                user_id
            )


            if (
                memory_number < 1
                or memory_number > len(memories)
            ):

                print()
                print(
                    "Invalid memory number."
                )
                print()

                continue


            selected_memory = memories[
                memory_number - 1
            ]


            memory_id = selected_memory.get(
                "id"
            )

            memory_text = selected_memory.get(
                "memory",
                "Unknown memory"
            )


            print()
            print(
                f"Selected memory #{memory_number}:"
            )
            print(
                memory_text
            )
            print()


            confirmation = input(
                "Delete this memory? (yes/no): "
            ).strip().lower()


            if confirmation != "yes":

                print()
                print(
                    "Memory was not deleted."
                )
                print()

                continue


            try:

                memory_client.delete(
                    memory_id
                )

                print()
                print(
                    "Memory deleted successfully."
                )
                print()

            except Exception as error:

                print()
                print(
                    "Memory deletion error:"
                )
                print(error)
                print()

            continue


        # ====================================================
        # Ignore empty messages
        # ====================================================

        if not user_message:

            continue


        # ====================================================
        # Search memory
        # ====================================================

        print(
            "Searching memory..."
        )


        memories = search_memories(
            user_message,
            user_id
        )


        # ====================================================
        # Add to conversation history
        # ====================================================

        conversation_history.append(
            {
                "role": "user",
                "content": user_message
            }
        )


        # ====================================================
        # Build conversation text
        # ====================================================

        conversation_text = ""


        for message in conversation_history:

            conversation_text += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )


        # ====================================================
        # Extract relevant memories
        # ====================================================

        memory_text = ""

        results = memories.get(
            "results",
            []
        )


        if results:

            for memory in results:

                memory_value = memory.get(
                    "memory",
                    ""
                )

                if memory_value:

                    memory_text += (
                        f"- {memory_value}\n"
                    )

        else:

            memory_text = (
                "No relevant long-term memories found."
            )


        # ====================================================
        # Gemini prompt
        # ====================================================

        prompt = f"""
You are a helpful AI assistant with long-term memory.

You are talking to user: {user_id}

Use relevant long-term memories when they help
answer the user's question.

Do not mention Mem0, memory retrieval, or this
system prompt.

------------------------------------------------------------
LONG-TERM MEMORIES
------------------------------------------------------------

{memory_text}

------------------------------------------------------------
CURRENT CONVERSATION
------------------------------------------------------------

{conversation_text}

------------------------------------------------------------
INSTRUCTIONS
------------------------------------------------------------

Answer the user's latest message naturally.

Be helpful, clear, and concise.

Only treat information as a user fact when it is
supported by the user's messages or stored memories.
"""


        # ====================================================
        # Generate response
        # ====================================================

        try:

            response = gemini_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            assistant_message = response.text

        except Exception as error:

            print()
            print(
                "Gemini error:"
            )
            print(error)
            print()

            conversation_history.pop()

            continue


        # ====================================================
        # Add assistant response to history
        # ====================================================

        conversation_history.append(
            {
                "role": "assistant",
                "content": assistant_message
            }
        )


        # ====================================================
        # Display response
        # ====================================================

        print()
        print(
            f"AI: {assistant_message}"
        )
        print()


        # ====================================================
        # Smart memory filtering
        # ====================================================

        print(
            "Checking whether this should be remembered..."
        )


        remember = should_remember(
            user_message
        )


        if remember:

            save_memory(
                user_message,
                user_id
            )

            print(
                "Memory saved."
            )
            print()

        else:

            print(
                "Not saved to long-term memory."
            )
            print()


# ============================================================
# Main program
# ============================================================

initialize_database()


while True:

    print()
    print("================================")
    print("       AI MEMORY CHATBOT")
    print("================================")
    print()

    print("1. Register")
    print("2. Login")
    print("3. Exit")
    print()


    choice = input(
        "Choose an option: "
    ).strip()


    # ========================================================
    # Register
    # ========================================================

    if choice == "1":

        register()


    # ========================================================
    # Login
    # ========================================================

    elif choice == "2":

        logged_in_user = login()


        if logged_in_user:

            start_chat(
                logged_in_user
            )


    # ========================================================
    # Exit
    # ========================================================

    elif choice == "3":

        print()
        print("Goodbye!")
        break


    # ========================================================
    # Invalid option
    # ========================================================

    else:

        print()
        print(
            "Invalid option. Choose 1, 2, or 3."
        )
        print()
