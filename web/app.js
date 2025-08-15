class WebSocketOrderManager {
    constructor(symbols = ['BTCUSDT', 'ETHUSDT']) {
        this.symbols = symbols;
        this.socket = null;
        this.orderUpdates = {};
        
        this.connect();
    }

    connect() {
        const streams = this.symbols.map(sym => ${sym.toLowerCase()}@executionReport).join('/');
        const websocketUrl = wss://stream.binance.com:9443/ws/;

        this.socket = new WebSocket(websocketUrl);

        this.socket.onopen = () => {
            console.log('Order WebSocket Connected');
            this.updateConnectionStatus('connected');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.processOrderUpdate(data);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            this.updateConnectionStatus('error');
        };

        this.socket.onclose = () => {
            console.log('Order WebSocket Disconnected');
            this.updateConnectionStatus('disconnected');
            
            setTimeout(() => this.connect(), 5000);
        };
    }

    processOrderUpdate(data) {
        if (data.e === 'executionReport') {
            const orderUpdate = {
                symbol: data.s,
                side: data.S,
                orderType: data.o,
                status: data.X,
                price: data.p,
                quantity: data.q,
                timestamp: data.T
            };

            this.updateTradesTable(orderUpdate);
            this.updatePerformanceMetrics(orderUpdate);
        }
    }

    updateTradesTable(orderUpdate) {
        const tradesTableBody = document.getElementById('trades-tbody');
        if (tradesTableBody) {
            const newRow = tradesTableBody.insertRow(0);
            newRow.innerHTML = 
                <td></td>
                <td></td>
                <td class="trade-side-"></td>
                <td></td>
                <td></td>
            ;
        }
    }

    updatePerformanceMetrics(orderUpdate) {
        console.log('Performance update:', orderUpdate);
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('websocket-status');
        if (statusElement) {
            statusElement.textContent = WebSocket: ;
            statusElement.className = status-;
        }
    }
}

// Modify existing initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    const orderWebSocket = new WebSocketOrderManager();
});
