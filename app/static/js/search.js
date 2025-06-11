document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = e.target.query.value.trim();
    
    if (!query) {
        alert("Please enter a search term");
        return;
    }

    const loading = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    
    loading.style.display = 'block';
    resultsDiv.innerHTML = '';
    
    try {
        const response = await fetch(`/search?t=${Date.now()}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `query=${encodeURIComponent(query)}`
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        resultsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    } finally {
        loading.style.display = 'none';
    }
});

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    if (data.total_matches === 0) {
        resultsDiv.innerHTML = `<p class="text-gray-600 italic">No results found for "${data.query}"</p>`;
        return;
    }

    const header = document.createElement('div');
    header.innerHTML = `
        <h2 class="text-xl font-bold text-gray-800 mb-1">${data.total_matches} results for "${data.query}"</h2>
        <p class="text-sm text-gray-500 mb-4">Last updated: ${new Date(data.timestamp).toLocaleString()}</p>
    `;
    resultsDiv.appendChild(header);

    const allKeys = Object.keys(data.results[0].row_data);

    // Table container for horizontal scroll
    const scrollWrapper = document.createElement('div');
    scrollWrapper.className = 'overflow-x-auto rounded-lg shadow ring-1 ring-gray-300';

    const table = document.createElement('table');
    table.className = 'min-w-full border-collapse bg-white text-sm text-left';

    // Header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr class="bg-gray-100 text-gray-700 border-b border-gray-300">
            ${allKeys.map(key => `<th class="px-4 py-2 border-r font-semibold">${key}</th>`).join('')}
        </tr>
    `;
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    data.results.forEach(result => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-blue-50 border-b border-gray-200';

        allKeys.forEach(key => {
            const cellValue = result.row_data[key] ?? '';
            const isMatch = result.matched_columns.hasOwnProperty(key);
            const td = document.createElement('td');
            td.className = 'px-4 py-2 border-r whitespace-nowrap';

            td.innerHTML = isMatch
                ? `<span class="bg-yellow-200 text-blue-900 font-semibold px-1 rounded">${highlightMatch(cellValue, data.query)}</span>`
                : cellValue;

            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    scrollWrapper.appendChild(table);
    resultsDiv.appendChild(scrollWrapper);
}


function highlightMatch(text, query) {
    if (text === null || text === undefined) return '';
    const safeText = String(text);
    const safeQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(safeQuery, 'gi');
    return safeText.replace(regex, match => `<span class="match">${match}</span>`);
}
