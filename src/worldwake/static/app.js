const imageInput = document.querySelector("#seed-image");
const imagePreview = document.querySelector("#image-preview");
const previewMessage = document.querySelector("#preview-message");
const fileName = document.querySelector("#file-name");
const dropZone = document.querySelector(".drop-zone");

// Keep a reference to the current preview URL so it can be cleaned up later.
let previewUrl = null;


function clearExistingPreviewUrl() {
    // Revoke any previous object URL to avoid memory leaks and stale previews.
    if (previewUrl !== null) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
    }
}


function showSelectedImage(selectedFile) {
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
