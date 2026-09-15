document.addEventListener("DOMContentLoaded", () => {

    const dropZone =
        document.getElementById("dropZone");

    const fileInput =
        document.getElementById("id_file");

    const selectedFile =
        document.getElementById("selectedFile");

    if (!dropZone || !fileInput) {
        return;
    }

    function updateFileName() {

        if (!fileInput.files.length) {

            selectedFile.textContent =
                "No file selected";

            return;
        }

        const file =
            fileInput.files[0];

        const sizeMB =
            file.size / (1024 * 1024);

        selectedFile.textContent =
            `${file.name} · ${sizeMB.toFixed(2)} MB`;
    }

    fileInput.addEventListener(
        "change",
        updateFileName
    );


    [
        "dragenter",
        "dragover",
    ].forEach(eventName => {

        dropZone.addEventListener(
            eventName,
            event => {

                event.preventDefault();

                dropZone.classList.add(
                    "dragging"
                );
            }
        );

    });


    [
        "dragleave",
        "drop",
    ].forEach(eventName => {

        dropZone.addEventListener(
            eventName,
            event => {

                event.preventDefault();

                dropZone.classList.remove(
                    "dragging"
                );
            }
        );

    });


    dropZone.addEventListener(
        "drop",
        event => {

            const files =
                event.dataTransfer.files;

            if (!files.length) {
                return;
            }

            fileInput.files = files;

            updateFileName();
        }
    );

});