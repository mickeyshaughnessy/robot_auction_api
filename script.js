const API_URL = 'http://100.26.236.1:5001';
let authToken = null;

async function makeApiRequest(endpoint, method, data = null) {
    const url = `${API_URL}${endpoint}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const result = await response.json();
        document.getElementById('response').innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        
        if (endpoint === '/login' && response.ok) {
            authToken = result.access_token;
            updateButtonStates();
        }
    } catch (error) {
        document.getElementById('response').innerHTML = `<pre>Error: ${error.message}</pre>`;
    }
}

function updateButtonStates() {
    const authButtons = document.querySelectorAll('button[disabled]');
    authButtons.forEach(button => {
        button.disabled = !authToken;
    });
}

function getEndpointData(button) {
    const endpoint = button.closest('.endpoint');
    const path = endpoint.querySelector('.path').textContent.trim();
    const method = endpoint.querySelector('.method').textContent.trim();
    const inputs = endpoint.querySelectorAll('input');
    const data = {};
    inputs.forEach(input => {
        data[input.id.split('-').pop()] = input.value;
    });
    return { path, method, data };
}

document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', (event) => {
            const { path, method, data } = getEndpointData(event.target);
            makeApiRequest(path, method, Object.keys(data).length ? data : null);
        });
    });
});