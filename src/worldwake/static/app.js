// The upload experience is driven by a handful of DOM references that keep the
// UI logic simple and focused on previewing the selected image.
const imageInput = document.querySelector("#seed-image");
const imagePreview = document.querySelector("#image-preview");
const previewMessage = document.querySelector("#preview-message");
const fileName = document.querySelector("#file-name");
const dropZone = document.querySelector(".drop-zone");

// Keep a reference to the current preview URL so it can be cleaned up later.
let previewUrl = null;


function clearExistingPreviewUrl() {
    // Revoke the previous object URL so the browser does not retain stale blobs
    // in memory after the user picks another image.
    // Revoke any previous object URL to avoid memory leaks and stale previews.
    if (previewUrl !== null) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
    }
}


function showSelectedImage(selectedFile) {
    // Mirror the selected file into the preview panel and keep the UI text in
    // sync with the current upload state.
    clearExistingPreviewUrl();

    if (!selectedFile) {
        imagePreview.hidden = true;
        imagePreview.removeAttribute("src");
        previewMessage.hidden = false;
        fileName.textContent = "The table is empty.";
        return;
    }

    previewUrl = URL.createObjectURL(selectedFile);

    imagePreview.src = previewUrl;
    imagePreview.hidden = false;
    previewMessage.hidden = true;
    fileName.textContent = selectedFile.name;
}


// Update the preview panel whenever the user selects a new image file.
imageInput.addEventListener("change", () => {
    showSelectedImage(imageInput.files[0]);
});

// Give the upload area a small visual response when a file is dragged over it.
["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("is-dragging");
    });
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("is-dragging");
});

dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");

    const droppedFile = event.dataTransfer.files[0];

    if (droppedFile?.type.startsWith("image/")) {
        showSelectedImage(droppedFile);
    } else if (droppedFile) {
        fileName.textContent = "That does not appear to be an image.";
    }
});

// Clean up the temporary preview when the page is unloaded.
window.addEventListener("beforeunload", clearExistingPreviewUrl);

// Account controls connect the browser interface to WorldWake's
// database-backed authentication API.

const authDialog = document.querySelector("#auth-dialog");
const authDialogTitle = document.querySelector("#auth-dialog-title");
const authDialogIntroduction = document.querySelector(
    "#auth-dialog-introduction",
);
const authStatus = document.querySelector("#auth-status");

const loginForm = document.querySelector("#login-form");
const registerForm = document.querySelector("#register-form");
const changePasswordForm = document.querySelector(
    "#change-password-form",
);

const signedOutControls = document.querySelector(
    "#signed-out-controls",
);
const signedInControls = document.querySelector(
    "#signed-in-controls",
);
const accountUsername = document.querySelector(
    "#account-username",
);
const accountMessage = document.querySelector(
    "#account-message",
);

const openLoginButton = document.querySelector("#open-login");
const openRegisterButton = document.querySelector(
    "#open-register",
);
const openAccountButton = document.querySelector(
    "#open-account",
);
const logoutButton = document.querySelector("#logout-button");
const closeAuthDialogButton = document.querySelector(
    "#close-auth-dialog",
);

const authenticationViews = {
    login: {
        form: loginForm,
        title: "Return to WorldWake",
        introduction: (
            "Sign in to continue shaping your worlds."
        ),
    },
    register: {
        form: registerForm,
        title: "Begin your chronicle",
        introduction: (
            "Create an account to preserve the worlds you awaken."
        ),
    },
    changePassword: {
        form: changePasswordForm,
        title: "Change your password",
        introduction: (
            "Replace your password and close every older session."
        ),
    },
};


class ApiError extends Error {
    constructor(message, statusCode) {
        super(message);

        this.name = "ApiError";
        this.statusCode = statusCode;
    }
}


function validationMessage(payload, fallbackMessage) {
    const detail = payload?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail)) {
        const messages = detail
            .map((item) => item?.msg)
            .filter(Boolean);

        if (messages.length > 0) {
            return messages.join(" ");
        }
    }

    return fallbackMessage;
}


async function requestJson(url, options = {}) {
    const headers = new Headers(options.headers || {});

    if (options.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        headers,
    });

    let payload = null;

    if (response.status !== 204) {
        const responseText = await response.text();

        if (responseText) {
            try {
                payload = JSON.parse(responseText);
            } catch {
                payload = null;
            }
        }
    }

    if (!response.ok) {
        throw new ApiError(
            validationMessage(
                payload,
                "WorldWake could not complete that request.",
            ),
            response.status,
        );
    }

    return payload;
}


function readCookie(cookieName) {
    const prefix = `${encodeURIComponent(cookieName)}=`;

    const cookie = document.cookie
        .split("; ")
        .find((entry) => entry.startsWith(prefix));

    if (!cookie) {
        return null;
    }

    return decodeURIComponent(
        cookie.slice(prefix.length),
    );
}


function csrfHeaders() {
    const csrfToken = readCookie("ww_csrf");

    if (!csrfToken) {
        throw new ApiError(
            "Your security token is missing. Sign in again.",
            403,
        );
    }

    return {
        "X-CSRF-Token": csrfToken,
    };
}


function setAccountMessage(message = "", tone = "normal") {
    accountMessage.textContent = message;
    accountMessage.dataset.tone = tone;
}


function setAuthStatus(message = "", tone = "normal") {
    authStatus.textContent = message;
    authStatus.dataset.tone = tone;
}


function setCurrentUser(user) {
    const isSignedIn = user !== null;

    signedOutControls.hidden = isSignedIn;
    signedInControls.hidden = !isSignedIn;

    accountUsername.textContent = (
        isSignedIn
            ? user.username
            : ""
    );
}


function setFormBusy(form, isBusy) {
    const controls = form.querySelectorAll(
        "input, button",
    );

    controls.forEach((control) => {
        control.disabled = isBusy;
    });
}


function showAuthenticationView(viewName) {
    const selectedView = authenticationViews[viewName];

    Object.entries(authenticationViews).forEach(
        ([name, view]) => {
            view.form.hidden = name !== viewName;
        },
    );

    document
        .querySelectorAll("[data-auth-switch]")
        .forEach((switchElement) => {
            switchElement.hidden = (
                switchElement.dataset.authSwitch
                !== viewName
            );
        });

    authDialogTitle.textContent = selectedView.title;
    authDialogIntroduction.textContent = (
        selectedView.introduction
    );

    setAuthStatus();
}


function openAuthenticationDialog(viewName) {
    showAuthenticationView(viewName);

    if (!authDialog.open) {
        authDialog.showModal();
    }

    requestAnimationFrame(() => {
        const firstInput = (
            authenticationViews[viewName]
                .form
                .querySelector("input")
        );

        firstInput?.focus();
    });
}


function completeAuthentication(user, message) {
    setCurrentUser(user);
    setAccountMessage(message);

    loginForm.reset();
    registerForm.reset();
    changePasswordForm.reset();

    authDialog.close();
}


async function loadCurrentUser() {
    try {
        const user = await requestJson(
            "/api/auth/me",
        );

        setCurrentUser(user);
    } catch (error) {
        if (
            error instanceof ApiError
            && error.statusCode === 401
        ) {
            setCurrentUser(null);
            return;
        }

        setCurrentUser(null);
        setAccountMessage(
            "WorldWake could not confirm your session.",
            "error",
        );
    }
}


openLoginButton.addEventListener("click", () => {
    openAuthenticationDialog("login");
});


openRegisterButton.addEventListener("click", () => {
    openAuthenticationDialog("register");
});


openAccountButton.addEventListener("click", () => {
    openAuthenticationDialog("changePassword");
});


closeAuthDialogButton.addEventListener("click", () => {
    authDialog.close();
});


document
    .querySelectorAll("[data-auth-target]")
    .forEach((button) => {
        button.addEventListener("click", () => {
            showAuthenticationView(
                button.dataset.authTarget,
            );
        });
    });


loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(loginForm);

    setFormBusy(loginForm, true);
    setAuthStatus("Opening your chronicle…");

    try {
        const user = await requestJson(
            "/api/auth/login",
            {
                method: "POST",
                body: JSON.stringify({
                    identifier: String(
                        formData.get("identifier") || "",
                    ),
                    password: String(
                        formData.get("password") || "",
                    ),
                }),
            },
        );

        completeAuthentication(
            user,
            `Welcome back, ${user.username}`,
        );
    } catch (error) {
        setAuthStatus(
            error.message,
            "error",
        );
    } finally {
        setFormBusy(loginForm, false);
    }
});


registerForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const formData = new FormData(registerForm);

        setFormBusy(registerForm, true);
        setAuthStatus("Inscribing your account…");

        try {
            const user = await requestJson(
                "/api/auth/register",
                {
                    method: "POST",
                    body: JSON.stringify({
                        username: String(
                            formData.get("username") || "",
                        ),
                        email: String(
                            formData.get("email") || "",
                        ),
                        password: String(
                            formData.get("password") || "",
                        ),
                    }),
                },
            );

            completeAuthentication(
                user,
                `Welcome to WorldWake, ${user.username}`,
            );
        } catch (error) {
            setAuthStatus(
                error.message,
                "error",
            );
        } finally {
            setFormBusy(registerForm, false);
        }
    },
);


changePasswordForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const formData = new FormData(
            changePasswordForm,
        );

        setFormBusy(changePasswordForm, true);
        setAuthStatus("Reforging your password…");

        try {
            const user = await requestJson(
                "/api/auth/change-password",
                {
                    method: "POST",
                    headers: csrfHeaders(),
                    body: JSON.stringify({
                        current_password: String(
                            formData.get(
                                "current_password",
                            ) || "",
                        ),
                        new_password: String(
                            formData.get(
                                "new_password",
                            ) || "",
                        ),
                    }),
                },
            );

            completeAuthentication(
                user,
                (
                    "Password changed. "
                    + "Other sessions were signed out."
                ),
            );
        } catch (error) {
            setAuthStatus(
                error.message,
                "error",
            );
        } finally {
            setFormBusy(
                changePasswordForm,
                false,
            );
        }
    },
);


logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;
    setAccountMessage("Signing out…");

    try {
        await requestJson(
            "/api/auth/logout",
            {
                method: "POST",
                headers: csrfHeaders(),
            },
        );

        setCurrentUser(null);
        setAccountMessage("You have been signed out.");
    } catch (error) {
        setAccountMessage(
            error.message,
            "error",
        );
    } finally {
        logoutButton.disabled = false;
    }
});


loadCurrentUser();