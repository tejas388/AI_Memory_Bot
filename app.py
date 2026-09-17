import os
import sqlite3
import hashlib
import secrets
import time

from dotenv import load_dotenv

from fastapi import FastAPI, Request

from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse
)

from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates

from starlette.middleware.sessions import SessionMiddleware

from mem0 import MemoryClient

from google import genai


load_dotenv()


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

MEM0_API_KEY = os.getenv("MEM0_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SESSION_SECRET = os.getenv("SESSION_SECRET")


if not MEM0_API_KEY:
    raise ValueError(
        "MEM0_API_KEY is missing from .env"
    )


if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing from .env"
    )


if not SESSION_SECRET:
    raise ValueError(
        "SESSION_SECRET is missing from .env"
    )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Memory Chatbot",
    description="Multi-user AI chatbot with long-term memory",
    version="1.0.0"
)


# ============================================================
# SECURE SESSION
# ============================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=False
)


# ============================================================
# STATIC FILES AND TEMPLATES
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


templates = Jinja2Templates(
    directory="templates"
)


# ============================================================
# API CLIENTS
# ============================================================

memory_client = MemoryClient(
    api_key=MEM0_API_KEY
)


gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# DATABASE
# ============================================================

DATABASE = "users.db"


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = sqlite3.connect(DATABASE)

    cursor = connection.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            salt TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL,

            user_message TEXT NOT NULL,

            assistant_message TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    connection.commit()

    connection.close()


initialize_database()


# ============================================================
# GET CURRENT USER FROM SECURE SESSION
# ============================================================

def get_current_user(request: Request):

    username = request.session.get(
        "username"
    )


    if not username:
        return None


    return username.strip().lower()


# ============================================================
# SAVE CONVERSATION
# ============================================================

def save_conversation(
    username,
    user_message,
    assistant_message
):

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO conversations
        (
            username,
            user_message,
            assistant_message
        )
        VALUES (?, ?, ?)
        """,
        (
            username,
            user_message,
            assistant_message
        )
    )


    connection.commit()

    connection.close()


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(
    password,
    salt=None
):

    if salt is None:

        salt = secrets.token_hex(
            16
        )


    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()


    return password_hash, salt


# ============================================================
# PASSWORD VERIFICATION
# ============================================================

def verify_password(
    password,
    stored_hash,
    salt
):

    password_hash, _ = hash_password(
        password,
        salt
    )


    return secrets.compare_digest(
        password_hash,
        stored_hash
    )


# ============================================================
# GEMINI RESPONSE WITH RETRIES
# ============================================================

def generate_gemini_response(
    prompt
):

    max_attempts = 3


    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            print(
                f"Gemini attempt "
                f"{attempt}/{max_attempts}"
            )


            response = (
                gemini_client
                .models
                .generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )
            )


            return response.text


        except Exception as error:

            error_text = str(
                error
            )


            print(
                "Gemini error:"
            )

            print(error)


            if (
                "503" in error_text
                or
                "UNAVAILABLE" in error_text
                or
                "high demand"
                in error_text.lower()
            ):

                if attempt < max_attempts:

                    wait_time = (
                        attempt * 3
                    )


                    print(
                        "Gemini temporarily "
                        "unavailable. "
                        f"Retrying in "
                        f"{wait_time} seconds..."
                    )


                    time.sleep(
                        wait_time
                    )


                    continue


            raise error


    raise Exception(
        "Gemini failed after multiple attempts."
    )


# ============================================================
# HOME / LOGIN PAGE
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "message":
            "AI Memory Chatbot backend is running"
    }


# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
async def register(
    request: Request
):

    try:

        data = await request.json()


    except Exception:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Invalid request."
            }
        )


    username = data.get(
        "username",
        ""
    ).strip().lower()


    password = data.get(
        "password",
        ""
    )


    if not username:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Username cannot be empty."
            }
        )


    if len(username) < 3:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Username must contain "
                    "at least 3 characters."
            }
        )


    if len(password) < 6:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Password must contain "
                    "at least 6 characters."
            }
        )


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
            (
                username,
                password_hash,
                salt
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                password_hash,
                salt
            )
        )


        connection.commit()


    except sqlite3.IntegrityError:

        connection.close()


        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "message":
                    "Username already exists."
            }
        )


    connection.close()


    return {
        "success": True,
        "message":
            "Account created successfully."
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
async def login(
    request: Request
):

    try:

        data = await request.json()


    except Exception:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Invalid request."
            }
        )


    username = data.get(
        "username",
        ""
    ).strip().lower()


    password = data.get(
        "password",
        ""
    )


    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            password_hash,
            salt
        FROM users
        WHERE username = ?
        """,
        (username,)
    )


    user = cursor.fetchone()


    connection.close()


    if user is None:

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message":
                    "Invalid username "
                    "or password."
            }
        )


    stored_hash = user[0]

    salt = user[1]


    if not verify_password(
        password,
        stored_hash,
        salt
    ):

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message":
                    "Invalid username "
                    "or password."
            }
        )


    request.session.clear()


    request.session["username"] = (
        username
    )


    return {
        "success": True,
        "message":
            "Login successful.",
        "username":
            username
    }


# ============================================================
# LOGOUT
# ============================================================

@app.post("/logout")
async def logout(
    request: Request
):

    request.session.clear()


    return {
        "success": True,
        "message":
            "Logged out successfully."
    }


# ============================================================
# CHAT PAGE
# ============================================================

@app.get(
    "/chat",
    response_class=HTMLResponse
)
async def chat_page(
    request: Request
):

    username = get_current_user(
        request
    )


    if not username:

        return RedirectResponse(
            url="/",
            status_code=303
        )


    return templates.TemplateResponse(
        request=request,
        name="chat.html"
    )


# ============================================================
# MEMORIES PAGE
# ============================================================

@app.get(
    "/memories",
    response_class=HTMLResponse
)
async def memories_page(
    request: Request
):

    username = get_current_user(
        request
    )


    if not username:

        return RedirectResponse(
            url="/",
            status_code=303
        )


    return templates.TemplateResponse(
        request=request,
        name="memories.html"
    )


# ============================================================
# HISTORY PAGE
# ============================================================

@app.get(
    "/history",
    response_class=HTMLResponse
)
async def history_page(
    request: Request
):

    username = get_current_user(
        request
    )


    if not username:

        return RedirectResponse(
            url="/",
            status_code=303
        )


    return templates.TemplateResponse(
        request=request,
        name="history.html"
    )


# ============================================================
# GET MEMORIES
# ============================================================

@app.get("/api/memories")
async def get_memories(
    request: Request
):

    username = get_current_user(
        request
    )


    if not username:

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message":
                    "Please log in first."
            }
        )


    try:

        memories = (
            memory_client.get_all(
                filters={
                    "user_id":
                        username
                }
            )
        )


        results = memories.get(
            "results",
            []
        )


        formatted_memories = []


        for memory in results:

            formatted_memories.append(
                {
                    "id":
                        memory.get("id"),

                    "memory":
                        memory.get(
                            "memory",
                            ""
                        )
                }
            )


        return {
            "success": True,
            "memories":
                formatted_memories,
            "count":
                len(formatted_memories)
        }


    except Exception as error:

        print(
            "Memory retrieval error:"
        )

        print(error)


        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message":
                    "Could not load memories."
            }
        )


# ============================================================
# DELETE MEMORY
# ============================================================

@app.delete(
    "/api/memories/{memory_id}"
)
async def delete_memory(
    memory_id: str,
    request: Request
):

    username = get_current_user(
        request
    )


    if not username:

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message":
                    "Please log in first."
            }
        )


    try:

        memories = (
            memory_client.get_all(
                filters={
                    "user_id":
                        username
                }
            )
        )


        results = memories.get(
            "results",
            []
        )


        memory_exists = False


        for memory in results:

            if str(
                memory.get("id")
            ) == str(memory_id):

                memory_exists = True

                break


        if not memory_exists:

            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "message":
                        "You cannot delete "
                        "this memory."
                }
            )


        memory_client.delete(
            memory_id
        )


        return {
            "success": True,
            "message":
                "Memory deleted successfully."
        }


    except Exception as error:

        print(
            "Memory deletion error:"
        )

        print(error)


        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message":
                    "Could not delete memory."
            }
        )


# ============================================================
# GET CONVERSATION HISTORY
# ============================================================

@app.get("/api/history")
async def get_history(
    request: Request
):

    username = get_current_user(
        request
    )


    if not username:

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message":
                    "Please log in first."
            }
        )


    try:

        connection = sqlite3.connect(
            DATABASE
        )

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                id,
                user_message,
                assistant_message,
                created_at
            FROM conversations
            WHERE username = ?
            ORDER BY id DESC
            """,
            (username,)
        )


        rows = cursor.fetchall()


        connection.close()


        conversations = []


        for row in rows:

            conversations.append(
                {
                    "id":
                        row[0],

                    "user_message":
                        row[1],

                    "assistant_message":
                        row[2],

                    "created_at":
                        row[3]
                }
            )


        return {
            "success": True,
            "conversations":
                conversations,
            "count":
                len(conversations)
        }


    except Exception as error:

        print(
            "History retrieval error:"
        )

        print(error)


        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message":
                    "Could not load "
                    "conversation history."
            }
        )


# ============================================================
# CHAT API
# ============================================================

@app.post("/api/chat")
async def chat(
    request: Request
):

    username = get_current_user(
        request
    )


    if not username:

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message":
                    "Please log in first."
            }
        )


    try:

        data = await request.json()


    except Exception:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Invalid request."
            }
        )


    user_message = data.get(
        "message",
        ""
    ).strip()


    if not user_message:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Message cannot be empty."
            }
        )


    # ========================================================
    # SEARCH RELEVANT USER MEMORIES
    # ========================================================

    try:

        memories = (
            memory_client.search(
                user_message,
                filters={
                    "user_id":
                        username
                }
            )
        )


    except Exception as error:

        print(
            "Memory search error:"
        )

        print(error)


        memories = {
            "results": []
        }


    memory_text = ""


    results = memories.get(
        "results",
        []
    )


    for memory in results:

        memory_value = memory.get(
            "memory",
            ""
        )


        if memory_value:

            memory_text += (
                f"- {memory_value}\n"
            )


    if not memory_text:

        memory_text = (
            "No relevant long-term "
            "memories found."
        )


    # ========================================================
    # GEMINI PROMPT
    # ========================================================

    prompt = f"""
You are a helpful AI assistant with long-term memory.

You are talking to user: {username}

Use the relevant memories below when they help
answer the user's message.

Do not mention Mem0 or memory retrieval.

------------------------------------------------------------
USER MEMORIES
------------------------------------------------------------

{memory_text}

------------------------------------------------------------
USER MESSAGE
------------------------------------------------------------

{user_message}

------------------------------------------------------------
INSTRUCTIONS
------------------------------------------------------------

Give a natural, helpful and concise response.

Only treat information as a user fact when it is
supported by the user's message or stored memories.
"""


    # ========================================================
    # GENERATE AI RESPONSE
    # ========================================================

    try:

        assistant_message = (
            generate_gemini_response(
                prompt
            )
        )


    except Exception as error:

        print(
            "Gemini failed after retries:"
        )

        print(error)


        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message":
                    "Gemini is temporarily "
                    "unavailable. "
                    "Please try again."
            }
        )


    # ========================================================
    # SAVE USER MESSAGE TO MEM0
    # ========================================================
    #
    # IMPORTANT:
    #
    # Only the user's message is sent to Mem0.
    #
    # The assistant's generated answer is NOT sent
    # to Mem0. This prevents AI explanations from
    # becoming memories about the user.
    #
    # ========================================================

    try:

        memory_client.add(
            [
                {
                    "role":
                        "user",

                    "content":
                        user_message
                }
            ],
            user_id=username
        )


    except Exception as error:

        print(
            "Memory save error:"
        )

        print(error)


    # ========================================================
    # SAVE CONVERSATION HISTORY
    # ========================================================

    try:

        save_conversation(
            username,
            user_message,
            assistant_message
        )


    except Exception as error:

        print(
            "Conversation save error:"
        )

        print(error)


    # ========================================================
    # RETURN RESPONSE
    # ========================================================

    return {
        "success": True,
        "response":
            assistant_message
    }

# ============================================================
# AUTOMATICALLY OPEN THE WEBSITE WHEN SERVER STARTS
# ============================================================

@app.on_event("startup")
async def open_browser_on_startup():
    import threading
    import webbrowser

    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open("http://127.0.0.1:8000/")

    threading.Thread(
        target=open_browser,
        daemon=True
    ).start()
