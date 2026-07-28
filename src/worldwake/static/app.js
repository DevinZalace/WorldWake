const imageInput = document.querySelector("#seed-image");
const imagePreview = document.querySelector("#image-preview");
const previewMessage = document.querySelector("#preview-message");
const fileName = document.querySelector("#file-name");

// Keep a reference to the current preview URL so it can be cleaned up later.
let previewUrl = null;


function clearExistingPreviewUrl() {
    // Revoke any previous object URL to avoid memory leaks and stale previews.
    if (previewUrl !== null) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
    }
}


// Update the preview panel whenever the user selects a new image file.
imageInput.addEventListener("change", () => {
    clearExistingPreviewUrl();

    const selectedFile = imageInput.files[0];

    if (!selectedFile) {
        imagePreview.hidden = true;
        imagePreview.removeAttribute("src");
        previewMessage.hidden = false;
        fileName.textContent = "No image selected.";
        return;
    }

    previewUrl = URL.createObjectURL(selectedFile);

    imagePreview.src = previewUrl;
    imagePreview.hidden = false;
    previewMessage.hidden = true;
    fileName.textContent = selectedFile.name;
});


// Clean up the temporary preview when the page is unloaded.
window.addEventListener("beforeunload", clearExistingPreviewUrl);