document.getElementById('fetchRecommendations').addEventListener('click', () => {
    chrome.runtime.sendMessage({action: "fetchRecommendations"}, (response) => {
        const recommendationsDiv = document.getElementById('recommendations');
        recommendationsDiv.innerHTML = '';
        response.recommendations.forEach(item => {
            const div = document.createElement('div');
            div.textContent = item.name;
            recommendationsDiv.appendChild(div);
        });
    });
});