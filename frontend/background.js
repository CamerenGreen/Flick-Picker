chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "fetchRecommendations") {
        // Fetch recommendations from the backend
        fetch('http://localhost:5000/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ userId: 'sampleUser' })
        })
        .then(response => response.json())
        .then(data => {
            sendResponse({ recommendations: data });
        })
        .catch(error => {
            console.error('Error:', error);
        });
        return true; // Indicates that the response will be sent asynchronously
    }
});