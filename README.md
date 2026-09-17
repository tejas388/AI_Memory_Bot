# 🧠 AI Memory Assistant

A multi-user AI chatbot with long-term personalized memory, secure authentication, conversation history, and an interactive memory dashboard.

The application combines **FastAPI**, **Google Gemini**, **Mem0**, and **SQLite** to create a personal AI assistant that can remember useful information about individual users across conversations.

---

## 🚀 Features

### 🤖 AI Chat

- Natural-language conversations with Google Gemini
- Fast AI responses using Gemini Flash
- Automatic retry handling for temporary Gemini availability issues
- Clean and responsive chat interface

### 🧠 Long-Term Memory

- Uses Mem0 Cloud for persistent AI memory
- Stores useful information about individual users
- Retrieves relevant memories when answering questions
- Prevents AI-generated explanations from being stored as user facts
- Users can view their stored memories
- Users can delete individual memories

### 👥 Multi-User Support

- Multiple users can register and use the application
- Each user has an isolated memory space
- Conversation history is separated by username
- One user cannot access another user's memories through the application

### 🔐 Authentication & Security

- User registration and login
- Password hashing using PBKDF2-HMAC-SHA256
- Secure server-side sessions using Starlette SessionMiddleware
- Protected Chat, Memories, and History pages
- Secure logout
- Backend does not trust usernames supplied by the browser for data access
- API keys stored in environment variables
- Local database excluded from Git

### 🧠 Memory Dashboard

- View all saved memories
- Display total memory count
- Delete individual memories
- Refresh memories without reloading the page

### 💭 Conversation History

- Stores user and AI messages in SQLite
- Displays previous conversations
- Shows conversation timestamps
- History is isolated between users

### 🎨 User Interface

- Clean modern interface
- Responsive design
- Chat message animations
- AI typing indicator
- Hover effects
- Custom scrollbars
- Mobile-friendly layout

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | Web framework and API |
| Google Gemini | AI response generation |
| Mem0 | Long-term AI memory |
| SQLite | User accounts and conversation history |
| HTML | Frontend structure |
| CSS | Frontend styling |
| JavaScript | Frontend interaction |
| Jinja2 | HTML templates |
| Starlette Sessions | Secure server-side sessions |
| Uvicorn | Application server |

---

## 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │       Browser       │
                         │  HTML/CSS/JavaScript│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │      Backend        │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐  ┌────────────────┐  ┌───────────────┐
        │ Google Gemini  │  │   Mem0 Cloud   │  │    SQLite     │
        │   AI Model     │  │ Long-term Memory│  │ Users/History │
        └────────────────┘  └────────────────┘  └─────────────    


🧠 How the Memory System Works

The application uses Mem0 to provide long-term personalized memory.

When a user sends a message:

                    User Message
                         │
                         ▼
                  FastAPI Backend
                         │
                         ▼
                  Mem0 Memory Search
                         │
                         ▼
              Relevant User Memories
                         │
                         ▼
                   Gemini Prompt
                         │
                         ▼
                  Google Gemini
                         │
                         ▼
                    AI Response
                         │
             ┌───────────┴───────────┐
             │                       │
             ▼                       ▼
       SQLite History            User Message
       saved for later         sent to Mem0 for
                                  memory extraction


Memory Retrieval

When a user asks a question, the backend searches Mem0 using the current user message.

Relevant memories are included in the Gemini prompt so the assistant can provide more personalized responses.


Memory Creation

Only the user's message is sent to Mem0 for memory creation.

The assistant's generated response is intentionally not sent to Mem0.

This prevents AI-generated explanations from being stored as facts about the user.

For example:

User:

Remember that I am preparing for software engineering placements.

                    ↓

                 Mem0

                    ↓

User is preparing for software engineering placements.



However, an AI explanation such as:

Artificial Intelligence is a broad field of computer science...

is not intentionally stored as a personal fact about the user.




🔐 Security Architecture

The application uses server-side session-based authentication.

             Username + Password
                      │
                      ▼
              Password Verification
                      │
                      ▼
             Server-Side Session
                      │
                      ▼
               Session Cookie
                      │
                      ▼
             Protected API Request
                      │
                      ▼
             Backend Identifies User
                      │
                      ▼
       User-Specific Memory / History



Authentication

Passwords are hashed using:

PBKDF2-HMAC-SHA256

A unique salt is generated for each user.


Session Security

After successful login, the backend creates a server-side session containing the authenticated username.

Protected routes verify this session before returning user-specific information.



User Isolation

The backend obtains the username from the authenticated session instead of trusting a username sent by the browser.

This ensures that changing a username parameter in a browser request does not allow access to another user's memories or history.



API Key Protection

API keys are stored in:

.env

The .env file is excluded from Git using .gitignore.

A safe .env.example file is provided for configuration.



📁 Project Structure
my-mem0-chatbot/
│
├── app.py
├── chatbot.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── users.db
│
├── static/
│   ├── script.js
│   └── style.css
│
└── templates/
    ├── login.html
    ├── chat.html
    ├── memories.html
    └── history.h


Important Files
File	                 Purpose
app.py                  	Main FastAPI backend
chatbot.py              	Existing chatbot-related code
requirements.txt	        Python dependencies
.env.example    	        Environment variable template
.gitignore              	Prevents secrets/local files from being committed
users.db                	Local SQLite database
static/script.js        	Frontend functionality
static/style.css        	Application styling
templates/login.html     	Login and registration interface
templates/chat.html     	Chat interface
templates/memories.html  	Memory dashboard
templates/history.html	        Conversation history

users.db and .env are intentionally excluded from Git using .gitignore.


⚙️ Installation

1. Clone the Repository
git clone <your-repository-url>
cd my-mem0-chatbot

2. Create a Virtual Environment
python3 -m venv .venv

3. Activate the Virtual Environment

macOS/Linux:

source .venv/bin/activate

Windows:

.venv\Scripts\activate

4. Install Dependencies
pip install -r requirements.txt


🔑 Environment Configuration

Create a .env file in the project root:

MEM0_API_KEY=your_mem0_api_key
GEMINI_API_KEY=your_gemini_api_key
SESSION_SECRET=your_secure_random_secret

Do not commit the actual .env file.

The repository includes .env.example as a safe configuration template.


▶️ Run the Application

Start the FastAPI server:

uvicorn app:app --reload

Open the application in your browser:

http://127.0.0.1:8000


📌 Main Routes
Route                  	Purpose
/                       	Login/Register
/chat                      	AI Chat
/memories                  	Memory Dashboard
/history                  	Conversation History
/health                  	Backend health check
/register               	Registration API
/login                   	Login API
/logout                 	Logout API
/api/chat                	Chat API
/api/memories             	Memory retrieval API
/api/history            	History retrieval API



🧪 Testing

The application has been tested for:

User registration
User login
Password verification
Secure logout
Protected routes
Gemini AI responses
Long-term memory creation
Memory retrieval
Memory deletion
Conversation history
Multi-user memory isolation
Session-based authentication
Frontend/backend integration
Prevention of AI explanations being stored as user memories



🔒 Git Security

The following files and directories are excluded from version control:

.env
users.db
*.db
.venv/
__pycache__/

This prevents API keys, local user data, and Python environment files from being accidentally committed.




🔮 Future Enhancements

Possible future improvements include:

Streaming AI responses
Voice-based interaction
Memory categories and tags
Memory editing
Searchable conversation history
Conversation deletion
User profile management
Password reset
Email verification
Production deployment
HTTPS configuration
Rate limiting
Advanced AI model selection
Analytics dashboard



🎓 Project Purpose

This project demonstrates how modern AI applications can combine:

Large Language Models
Long-term AI memory
Secure authentication
Database storage
REST APIs
Responsive web interfaces
Multi-user architecture

The project goes beyond a simple stateless chatbot by providing personalized responses based on information remembered from previous interactions.




👨‍💻 Author

Tejas C K

Computer Science Student

Interests
Artificial Intelligence
Machine Learning
Python
Software Development
AI Applications
Hackathons
Technical Projects



⭐ Acknowledgements

Built using:

FastAPI
Google Gemini
Mem0
SQLite
Python
