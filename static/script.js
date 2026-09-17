// ============================================================
// AI MEMORY CHATBOT
// ============================================================


// ============================================================
// Login / Register UI
// ============================================================

function showRegister() {

    document
        .getElementById("login-section")
        .classList
        .add("hidden");

    document
        .getElementById("register-section")
        .classList
        .remove("hidden");

}


function showLogin() {

    document
        .getElementById("register-section")
        .classList
        .add("hidden");

    document
        .getElementById("login-section")
        .classList
        .remove("hidden");

}


// ============================================================
// Register
// ============================================================

const registerForm =
    document.getElementById("register-form");


if (registerForm) {

    registerForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const username =
                document
                    .getElementById("register-username")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("register-password")
                    .value;

            const confirmPassword =
                document
                    .getElementById("register-confirm-password")
                    .value;

            const message =
                document
                    .getElementById("register-message");


            if (password !== confirmPassword) {

                message.textContent =
                    "Passwords do not match.";

                return;

            }


            try {

                const response =
                    await fetch(
                        "/register",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                username: username,
                                password: password
                            })
                        }
                    );


                const data =
                    await response.json();


                message.textContent =
                    data.message;


                if (data.success) {

                    registerForm.reset();

                    setTimeout(
                        function() {

                            showLogin();

                            document
                                .getElementById(
                                    "login-username"
                                )
                                .value =
                                username;

                        },
                        1000
                    );

                }

            } catch (error) {

                console.error(error);

                message.textContent =
                    "Unable to connect to server.";

            }

        }
    );

}


// ============================================================
// Login
// ============================================================

const loginForm =
    document.getElementById("login-form");


if (loginForm) {

    loginForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const username =
                document
                    .getElementById("login-username")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("login-password")
                    .value;

            const message =
                document
                    .getElementById("login-message");


            try {

                const response =
                    await fetch(
                        "/login",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                username: username,
                                password: password
                            })
                        }
                    );


                const data =
                    await response.json();


                message.textContent =
                    data.message;


                if (data.success) {

                    /*
                     * Keep username only for displaying
                     * the logged-in user's name.
                     *
                     * Authentication itself is handled
                     * by the secure server-side session.
                     */
                    localStorage.setItem(
                        "username",
                        data.username
                    );

                    message.textContent =
                        "Login successful!";


                    setTimeout(
                        function() {

                            window.location.href =
                                "/chat";

                        },
                        500
                    );

                }

            } catch (error) {

                console.error(error);

                message.textContent =
                    "Unable to connect to server.";

            }

        }
    );

}


// ============================================================
// Logged-in username
// ============================================================

let username =
    localStorage.getItem("username");


const loggedUserElement =
    document.getElementById("logged-user");


if (
    loggedUserElement &&
    username
) {

    loggedUserElement.textContent =
        "Logged in as: " + username;

}


// ============================================================
// Chat elements
// ============================================================

const chatForm =
    document.getElementById("chat-form");

const messageInput =
    document.getElementById("message-input");

const chatMessages =
    document.getElementById("chat-messages");

const sendButton =
    document.getElementById("send-button");


// ============================================================
// Add chat message
// ============================================================

function addMessage(message, type) {

    if (!chatMessages) {
        return;
    }


    const welcomeMessage =
        document.querySelector(".welcome-message");


    if (welcomeMessage) {
        welcomeMessage.remove();
    }


    const row =
        document.createElement("div");


    row.classList.add(
        "message-row",
        type
    );


    const bubble =
        document.createElement("div");


    bubble.classList.add(
        "message-bubble"
    );


    bubble.textContent =
        message;


    row.appendChild(bubble);

    chatMessages.appendChild(row);


    chatMessages.scrollTop =
        chatMessages.scrollHeight;

}


// ============================================================
// Typing indicator
// ============================================================

function addTypingMessage() {

    if (!chatMessages) {
        return;
    }


    const row =
        document.createElement("div");


    row.classList.add(
        "message-row",
        "ai"
    );


    const bubble =
        document.createElement("div");


    bubble.classList.add(
        "message-bubble",
        "typing"
    );


    bubble.id =
        "typing-message";


    bubble.textContent =
        "AI is thinking...";


    row.appendChild(bubble);

    chatMessages.appendChild(row);


    chatMessages.scrollTop =
        chatMessages.scrollHeight;

}


function removeTypingMessage() {

    const typingMessage =
        document.getElementById(
            "typing-message"
        );


    if (typingMessage) {

        typingMessage
            .parentElement
            .remove();

    }

}


// ============================================================
// Handle unauthorized session
// ============================================================

function handleUnauthorized() {

    localStorage.removeItem("username");

    window.location.href = "/";

}


// ============================================================
// Chat
// ============================================================

if (chatForm) {

    chatForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const message =
                messageInput.value.trim();


            if (!message) {
                return;
            }


            if (!username) {

                alert(
                    "You are not logged in."
                );

                window.location.href =
                    "/";

                return;

            }


            addMessage(
                message,
                "user"
            );


            messageInput.value = "";

            sendButton.disabled = true;

            messageInput.disabled = true;


            addTypingMessage();


            try {

                /*
                 * SECURITY:
                 * Do NOT send username.
                 *
                 * The backend gets the username
                 * from the secure session.
                 */
                const response =
                    await fetch(
                        "/api/chat",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                message: message
                            })
                        }
                    );


                const data =
                    await response.json();


                removeTypingMessage();


                if (response.status === 401) {

                    handleUnauthorized();

                    return;

                }


                if (!response.ok) {

                    addMessage(
                        data.message ||
                        "Something went wrong.",
                        "ai"
                    );

                    return;

                }


                addMessage(
                    data.response,
                    "ai"
                );


            } catch (error) {

                console.error(
                    "Chat error:",
                    error
                );


                removeTypingMessage();


                addMessage(
                    "Unable to connect to the AI server.",
                    "ai"
                );


            } finally {

                sendButton.disabled = false;

                messageInput.disabled = false;

                messageInput.focus();

            }

        }
    );

}


// ============================================================
// Open Memories
// ============================================================

function openMemories() {

    window.location.href =
        "/memories";

}


// ============================================================
// Open Chat
// ============================================================

function openChat() {

    window.location.href =
        "/chat";

}


// ============================================================
// Load Memories
// ============================================================

async function loadMemories() {

    const memoryList =
        document.getElementById(
            "memory-list"
        );


    const memoryCount =
        document.getElementById(
            "memory-count"
        );


    if (!memoryList) {
        return;
    }


    if (!username) {

        window.location.href =
            "/";

        return;

    }


    memoryList.innerHTML =
        `
        <div class="memory-loading">
            Loading your memories...
        </div>
        `;


    try {

        /*
         * SECURITY:
         * No username is sent.
         *
         * The backend determines the
         * current user from the session.
         */
        const response =
            await fetch(
                "/api/memories"
            );


        const data =
            await response.json();


        if (response.status === 401) {

            handleUnauthorized();

            return;

        }


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Unable to load memories."
            );

        }


        memoryCount.textContent =
            data.count +
            (
                data.count === 1
                    ? " memory saved"
                    : " memories saved"
            );


        memoryList.innerHTML = "";


        if (
            !data.memories ||
            data.memories.length === 0
        ) {

            memoryList.innerHTML =
                `
                <div class="no-memories">

                    <div class="no-memories-icon">
                        🧠
                    </div>

                    <h3>
                        No memories yet
                    </h3>

                    <p>
                        Start chatting with your AI assistant
                        and it will remember useful information.
                    </p>

                </div>
                `;

            return;

        }


        data.memories.forEach(
            function(memory) {

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "memory-card";


                const content =
                    document.createElement(
                        "div"
                    );


                content.className =
                    "memory-content";


                const icon =
                    document.createElement(
                        "div"
                    );


                icon.className =
                    "memory-icon";


                icon.textContent =
                    "🧠";


                const text =
                    document.createElement(
                        "div"
                    );


                text.className =
                    "memory-text";


                text.textContent =
                    memory.memory;


                content.appendChild(icon);

                content.appendChild(text);


                const deleteButton =
                    document.createElement(
                        "button"
                    );


                deleteButton.className =
                    "delete-memory-button";


                deleteButton.textContent =
                    "🗑️ Delete";


                deleteButton.onclick =
                    function() {

                        deleteMemory(
                            memory.id
                        );

                    };


                card.appendChild(content);

                card.appendChild(deleteButton);


                memoryList.appendChild(card);

            }
        );


    } catch (error) {

        console.error(
            "Memory loading error:",
            error
        );


        memoryList.innerHTML =
            `
            <div class="no-memories">

                <div class="no-memories-icon">
                    ⚠️
                </div>

                <p>
                    Unable to load your memories.
                </p>

                <p>
                    Please refresh the page.
                </p>

            </div>
            `;

    }

}


// ============================================================
// Delete Memory
// ============================================================

async function deleteMemory(memoryId) {

    if (!username) {

        window.location.href =
            "/";

        return;

    }


    const confirmed =
        confirm(
            "Are you sure you want to delete this memory?"
        );


    if (!confirmed) {
        return;
    }


    try {

        /*
         * SECURITY:
         * No username is sent.
         *
         * The backend verifies that the
         * memory belongs to the session user.
         */
        const response =
            await fetch(
                "/api/memories/" +
                encodeURIComponent(memoryId),
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (response.status === 401) {

            handleUnauthorized();

            return;

        }


        if (!response.ok) {

            alert(
                data.message ||
                "Could not delete memory."
            );

            return;

        }


        await loadMemories();


    } catch (error) {

        console.error(
            "Memory deletion error:",
            error
        );


        alert(
            "Unable to connect to server."
        );

    }

}


// ============================================================
// Automatically load memories
// ============================================================

if (
    window.location.pathname ===
    "/memories"
) {

    loadMemories();

}


// ============================================================
// Logout
// ============================================================

async function logout() {

    try {

        /*
         * Tell the backend to destroy
         * the secure server-side session.
         */
        await fetch(
            "/logout",
            {
                method: "POST"
            }
        );

    } catch (error) {

        console.error(
            "Logout error:",
            error
        );

    } finally {

        localStorage.removeItem(
            "username"
        );

        window.location.href =
            "/";

    }

}


// ============================================================
// Conversation History
// ============================================================

function openHistory() {

    window.location.href =
        "/history";

}


// ============================================================
// Load Conversation History
// ============================================================

async function loadHistory() {

    const historyList =
        document.getElementById(
            "history-list"
        );


    const historyCount =
        document.getElementById(
            "history-count"
        );


    if (!historyList) {
        return;
    }


    if (!username) {

        window.location.href =
            "/";

        return;

    }


    historyList.innerHTML =
        `
        <div class="memory-loading">
            Loading your conversation history...
        </div>
        `;


    try {

        /*
         * SECURITY:
         * No username is sent.
         *
         * The backend gets the username
         * from the secure session.
         */
        const response =
            await fetch(
                "/api/history"
            );


        const data =
            await response.json();


        if (response.status === 401) {

            handleUnauthorized();

            return;

        }


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Unable to load history."
            );

        }


        historyCount.textContent =
            data.count +
            (
                data.count === 1
                    ? " conversation"
                    : " conversations"
            );


        historyList.innerHTML = "";


        if (
            !data.conversations ||
            data.conversations.length === 0
        ) {

            historyList.innerHTML =
                `
                <div class="no-memories">

                    <div class="no-memories-icon">
                        💭
                    </div>

                    <h3>
                        No conversations yet
                    </h3>

                    <p>
                        Start chatting with your AI
                        assistant to build your
                        conversation history.
                    </p>

                </div>
                `;

            return;

        }


        data.conversations.forEach(
            function(conversation) {

                const card =
                    document.createElement("div");


                card.className =
                    "history-card";


                const date =
                    document.createElement("div");


                date.className =
                    "history-date";


                date.textContent =
                    conversation.created_at;


                const userSection =
                    document.createElement("div");


                userSection.className =
                    "history-message user-history";


                const userLabel =
                    document.createElement("strong");


                userLabel.textContent =
                    "You";


                const userText =
                    document.createElement("p");


                userText.textContent =
                    conversation.user_message;


                userSection.appendChild(
                    userLabel
                );


                userSection.appendChild(
                    userText
                );


                const aiSection =
                    document.createElement("div");


                aiSection.className =
                    "history-message ai-history";


                const aiLabel =
                    document.createElement("strong");


                aiLabel.textContent =
                    "AI Assistant";


                const aiText =
                    document.createElement("p");


                aiText.textContent =
                    conversation.assistant_message;


                aiSection.appendChild(
                    aiLabel
                );


                aiSection.appendChild(
                    aiText
                );


                card.appendChild(date);

                card.appendChild(
                    userSection
                );

                card.appendChild(
                    aiSection
                );


                historyList.appendChild(card);

            }
        );


    } catch (error) {

        console.error(
            "History loading error:",
            error
        );


        historyList.innerHTML =
            `
            <div class="no-memories">

                <div class="no-memories-icon">
                    ⚠️
                </div>

                <h3>
                    Unable to load history
                </h3>

                <p>
                    Please refresh the page
                    and try again.
                </p>

            </div>
            `;

    }

}


// ============================================================
// Automatically load history page
// ============================================================

if (
    window.location.pathname ===
    "/history"
) {

    loadHistory();

}
