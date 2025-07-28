document.getElementById('encodeForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(this);

    fetch('/encode', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'hidden_data_image.png';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

        // Clear the inputs except for the picture image
        document.getElementById('encodeForm').reset();
    })
    .catch(error => console.error('Error:', error));
});

document.getElementById('decodeForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData(this);

    fetch('/decode', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Wrong password or image is not encoded') {
            alert('Wrong password or image is not encoded');
        } else if (data.error) {
            document.getElementById('decodedMessage').innerText = data.error;
        } else {
            document.getElementById('decodedMessage').innerText = 'Decoded Message: ' + data.decodedMessage;
        }

        // Clear the inputs except for the picture image
        document.getElementById('decodeForm').reset();
    })
    .catch(error => console.error('Error:', error));
});
