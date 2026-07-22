const API_BASE = "https://ainow-backend.onrender.com/api/v1";
let apexChartInstance = null;
let currentTicker = "MTNCOM";

// -------------------------------------------------------------------
// 1. Fetch & Render Top KPI Metrics
// -------------------------------------------------------------------
async function loadMetrics() {
    try {
        const response = await fetch(`${API_BASE}/metrics`);
        if (!response.ok) throw new Error("Metrics endpoint error");
        
        const data = await response.json();

        // Target dynamic HTML element IDs
        if (document.getElementById("kpi-market-avg")) {
            document.getElementById("kpi-market-avg").innerText = `₦${data.market_close_avg}`;
        }
        if (document.getElementById("kpi-asi-index")) {
            document.getElementById("kpi-asi-index").innerText = data.synthetic_asi.toLocaleString();
        }
        if (document.getElementById("kpi-market-return")) {
            const returnElem = document.getElementById("kpi-market-return");
            returnElem.innerText = `${data.market_return_pct}%`;
            returnElem.className = data.market_return_pct >= 0 ? "text-green-500" : "text-red-500";
        }
    } catch (error) {
        console.error("Error loading market metrics:", error);
    }
}

// -------------------------------------------------------------------
// 2. Fetch & Render Predictions Watchlist Table
// -------------------------------------------------------------------
async function loadTickersTable(searchQuery = "") {
    try {
        const url = searchQuery 
            ? `${API_BASE}/tickers?search=${encodeURIComponent(searchQuery)}`
            : `${API_BASE}/tickers`;
            
        const response = await fetch(url);
        if (!response.ok) throw new Error("Tickers endpoint error");
        
        const tickers = await response.json();
        const tbody = document.getElementById("ticker-table-body");
        if (!tbody) return;

        if (tickers.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">No matching tickers found.</td></tr>`;
            return;
        }

        tbody.innerHTML = tickers.map(item => {
            const isBullish = item.prediction === 1;
            const badgeClass = isBullish ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800";
            const changeClass = item.change_pct >= 0 ? "text-green-600" : "text-red-600";

            return `
                <tr onclick="selectTicker('${item.ticker}')" class="hover:bg-slate-700 cursor-pointer transition-colors">
                    <td class="font-bold py-3 px-4">${item.ticker}</td>
                    <td class="py-3 px-4">₦${item.close_price.toFixed(2)}</td>
                    <td class="py-3 px-4 ${changeClass}">${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%</td>
                    <td class="py-3 px-4">${item.rsi_14.toFixed(1)}</td>
                    <td class="py-3 px-4">₦${item.sma_10.toFixed(2)}</td>
                    <td class="py-3 px-4">
                        <span class="px-2 py-1 rounded text-xs font-semibold ${badgeClass}">
                            ${item.prediction_label} (${item.confidence}%)
                        </span>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (error) {
        console.error("Error loading watchlist table:", error);
    }
}

// -------------------------------------------------------------------
// 3. Fetch & Render ApexCharts Candlestick Chart
// -------------------------------------------------------------------
async function loadCandlestickChart(ticker) {
    try {
        const response = await fetch(`${API_BASE}/chart/${ticker}`);
        if (!response.ok) throw new Error(`Chart data error for ${ticker}`);
        
        const chartData = await response.json();

        const formattedSeries = chartData.series.map(candle => ({
            x: new Date(candle.x),
            y: candle.y // [Open, High, Low, Close]
        }));

        const options = {
            series: [{
                name: `${ticker} Price`,
                data: formattedSeries
            }],
            chart: {
                type: 'candlestick',
                height: 380,
                background: 'transparent',
                toolbar: { show: true }
            },
            title: {
                text: `${ticker} Daily Price Action (OHLC)`,
                align: 'left',
                style: { color: '#94a3b8', fontSize: '14px' }
            },
            xaxis: {
                type: 'datetime',
                labels: { style: { colors: '#94a3b8' } }
            },
            yaxis: {
                tooltip: { enabled: true },
                labels: { style: { colors: '#94a3b8' } }
            },
            grid: { borderColor: '#334155' }
        };

        const chartContainer = document.querySelector("#apex-chart");
        if (!chartContainer) return;

        if (apexChartInstance) {
            apexChartInstance.updateOptions({
                title: { text: `${ticker} Daily Price Action (OHLC)` }
            });
            apexChartInstance.updateSeries([{ name: `${ticker} Price`, data: formattedSeries }]);
        } else {
            apexChartInstance = new ApexCharts(chartContainer, options);
            apexChartInstance.render();
        }
        
        currentTicker = ticker;
    } catch (error) {
        console.error(`Error rendering chart for ${ticker}:`, error);
    }
}

// Helper to handle table row clicks
function selectTicker(ticker) {
    loadCandlestickChart(ticker);
}

// -------------------------------------------------------------------
// 4. Initialize Event Listeners on Load
// -------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    // Initial loads
    loadMetrics();
    loadTickersTable();
    loadCandlestickChart(currentTicker);

    // Search bar event listener
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            loadTickersTable(e.target.value.trim());
        });
    }
});

// Helper function for authorized API calls
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem("jwt_access_token");
    
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        console.warn("Unauthorized access. Redirecting to login...");
        // Handle token expiration or unauthenticated state here
    }

    return response;
}

// Example Login Function
async function loginUser(username, password) {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch("https://ainow-backend.onrender.com/api/v1/auth/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
    });

    if (!response.ok) throw new Error("Login failed");

    const data = await response.json();
    localStorage.setItem("jwt_access_token", data.access_token);
    console.log("Logged in successfully!");
}

// Refactored watchlist loader using fetchWithAuth
async function loadTickersTable(searchQuery = "") {
    try {
        const url = searchQuery 
            ? `${API_BASE}/tickers?search=${encodeURIComponent(searchQuery)}`
            : `${API_BASE}/tickers`;
            
        const response = await fetchWithAuth(url);
        if (!response.ok) throw new Error("Tickers endpoint error");

        const tickers = await response.json();
        // Render table logic...
    } catch (error) {
        console.error("Error loading watchlist:", error);
    }
}


let socket = null;

function connectWebSocket() {
    // Convert HTTP URL to WS URL
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/ticks`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("⚡ Connected to Live Market WebSocket stream.");
        updateConnectionStatus(true);
    };

    socket.onmessage = (event) => {
        const tick = JSON.parse(event.data);
        console.log("📈 Real-time tick received:", tick);
        
        // Dynamically update UI
        updateTickerBadge(tick);
    };

    socket.onclose = () => {
        console.warn("⚠️ WebSocket disconnected. Retrying in 3 seconds...");
        updateConnectionStatus(false);
        setTimeout(connectWebSocket, 3000); // Reconnect automatically
    };

    socket.onerror = (error) => {
        console.error("WebSocket Error:", error);
        socket.close();
    };
}

function updateTickerBadge(tick) {
    const tickerRow = document.getElementById(`ticker-${tick.ticker}`);
    if (!tickerRow) return;

    // Update Price with visual pulse indicator
    const priceElem = tickerRow.querySelector(".ticker-price");
    if (priceElem) {
        priceElem.textContent = `₦${tick.price.toFixed(2)}`;
        
        // Flash green for gain, red for loss
        const flashClass = tick.change >= 0 ? "bg-green-100" : "bg-red-100";
        priceElem.classList.add(flashClass);
        setTimeout(() => priceElem.classList.remove(flashClass), 1000);
    }
}

function updateConnectionStatus(isConnected) {
    const statusDot = document.getElementById("ws-status-dot");
    if (statusDot) {
        statusDot.className = isConnected 
            ? "w-3 h-3 rounded-full bg-green-500 animate-pulse" 
            : "w-3 h-3 rounded-full bg-red-500";
    }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    connectWebSocket();
});