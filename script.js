const API_URL = 'http://100.26.236.1:5001';

async function makeApiRequest(endpoint, method, data = null) {
    const url = `${API_URL}${endpoint}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const result = await response.json();
        document.getElementById('response').innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
    } catch (error) {
        document.getElementById('response').innerHTML = `<pre>Error: ${error.message}</pre>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('button:not([disabled])');
    buttons.forEach(button => {
        button.addEventListener('click', (event) => {
            const endpoint = event.target.closest('.endpoint').querySelector('.path').textContent.trim();
            const method = event.target.closest('.endpoint').querySelector('.method').textContent.trim();
            
            let data = null;
            if (method === 'POST') {
                const inputs = event.target.closest('.endpoint').querySelectorAll('input');
                data = {};
                inputs.forEach(input => {
                    data[input.id.split('-').pop()] = input.value;
                });
            }

            makeApiRequest(endpoint, method, data);
        });
    });
});