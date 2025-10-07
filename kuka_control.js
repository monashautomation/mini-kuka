// kuka_control.js
// JavaScript for KUKA Arm Control Station

class KukaController {
    constructor(numServos = 5) {
        this.numServos = numServos;
        this.port = null;
        this.connected = false;
        this.servoAngles = Array(numServos).fill(90);
        this.lastCommand = 'None';
        this.init();
    }

    init() {
        this.initElements();
        this.setupEventListeners();
        this.checkWebSerialSupport();
        this.renderServoCards();
        this.updateSystemState();
    }

    // Set up all main UI element references
    initElements() {
        this.connectBtn = document.getElementById('connectBtn');
        this.statusDot = document.getElementById('statusDot');
        // prefer new header/system ids; fall back if old id exists
        this.statusText = document.getElementById('headerStatusText') || document.getElementById('statusText');
        this.sendBtn = document.getElementById('sendBtn');
        this.servoGrid = document.getElementById('servoGrid');
        this.currentState = document.getElementById('currentState');
    }

    // Attach event listeners for connect and send buttons
    setupEventListeners() {
        this.connectBtn.addEventListener('click', () => this.toggleConnection());
        this.sendBtn.addEventListener('click', () => this.executePosition());
    }

    // Warn if browser does not support Web Serial API
    checkWebSerialSupport() {
        if (!('serial' in navigator)) {
            alert('Web Serial API not supported. Use Chrome/Edge with HTTPS.');
        }
    }

    // Render servo control cards for each joint
    renderServoCards() {
        this.servoGrid.innerHTML = '';
        for (let i = 0; i < this.numServos; i++) {
            const servoCard = this.createServoCard(i + 1);
            this.servoGrid.appendChild(servoCard);
        }
        this.attachServoListeners();
    }

    // Create a single servo control card (slider + input + label)
    createServoCard(servoNum) {
        const card = document.createElement('div');
        card.className = 'servo-card';
        // Panel names corresponding to the image labels
        const names = ['Base', 'Joint 1', 'Joint 2', 'Joint 3', 'Gripper'];
        const label = names[servoNum - 1] || `Joint ${servoNum}`;
        card.innerHTML = `
            <div class="servo-header">
                <div class="servo-label">${label}</div>
                <div class="servo-value" id="value${servoNum}">90°</div>
            </div>
            <div class="servo-controls">
                <input type="range" class="servo-slider" id="slider${servoNum}" min="0" max="180" value="90">
                <input type="number" class="servo-input" id="input${servoNum}" min="0" max="180" value="90">
            </div>
            <div class="degree-labels">
                <span>0°</span>
                <span>180°</span>
            </div>
        `;
        return card;
    }

    // Attach listeners to all servo sliders and inputs
    attachServoListeners() {
        for (let i = 1; i <= this.numServos; i++) {
            const slider = document.getElementById(`slider${i}`);
            const input = document.getElementById(`input${i}`);
            
            slider.addEventListener('input', () => this.updateFromSlider(i));
            input.addEventListener('input', () => this.updateFromInput(i));
        }
    }

    // When slider is moved, update value and UI
    updateFromSlider(servoNum) {
        const slider = document.getElementById(`slider${servoNum}`);
        const input = document.getElementById(`input${servoNum}`);
        const value = document.getElementById(`value${servoNum}`);
        
        const angle = parseInt(slider.value);
        this.servoAngles[servoNum - 1] = angle;
        input.value = angle;
        value.textContent = `${angle}°`;
        this.updateSystemState();
    }

    // When input is changed, update value and UI
    updateFromInput(servoNum) {
        const slider = document.getElementById(`slider${servoNum}`);
        const input = document.getElementById(`input${servoNum}`);
        const value = document.getElementById(`value${servoNum}`);
        
        const angle = parseInt(input.value);
        if (angle >= 0 && angle <= 180) {
            this.servoAngles[servoNum - 1] = angle;
            slider.value = angle;
            value.textContent = `${angle}°`;
            this.updateSystemState();
        }
    }

    // Update the system state display (status, positions, last command)
    updateSystemState() {
        const status = this.connected ? 'Online' : 'Offline';
        const positions = this.servoAngles.map(angle => `${angle}°`).join(', ');
        
        // If the page provides an updateSystemStateUI helper (we added it to the HTML), use that
        if (window.updateSystemStateUI) {
            const uiStatus = this.connected ? 'Active' : 'Standby';
            window.updateSystemStateUI(uiStatus, `[${positions}]`, this.lastCommand, status);
            return;
        }

        // Fallback: write a simple textual block
        if (this.currentState) {
            this.currentState.innerHTML = `\n// System Status: ${this.connected ? 'Active' : 'Standby'}\n// Joint Positions: [${positions}]\n// Last Command: ${this.lastCommand}\n// Connection: ${status}`.trim();
        }
    }

    // Toggle serial connection (connect/disconnect)
    async toggleConnection() {
        if (!this.connected) {
            await this.connect();
        } else {
            this.disconnect();
        }
    }

    // Open serial port and update UI on connect
    async connect() {
        try {
            this.port = await navigator.serial.requestPort();
            await this.port.open({ baudRate: 9600 });
            
            this.connected = true;
            this.connectBtn.textContent = 'DISCONNECT';
            if (this.statusDot) this.statusDot.classList.add('connected');
            // Prefer using page helper so we don't rely on specific element ids
            if (window.setConnectionStatus) {
                window.setConnectionStatus(true);
            } else {
                if (this.statusText) this.statusText.textContent = 'CONNECTED';
                if (this.sendBtn) this.sendBtn.disabled = false;
            }
             this.lastCommand = 'Connected';
             this.updateSystemState();
             
             console.log('[SYSTEM] Serial connection established');

            // Start a background read loop to show incoming Pico replies
            this.startReading();
             
         } catch (error) {
             console.error('[ERROR] Connection failed:', error);
             alert(`Connection failed: ${error.message}`);
         }
     }

    // Start reading incoming serial data and display in serial log
    async startReading() {
        if (!this.port || !this.port.readable) return;
        try {
            const textDecoder = new TextDecoderStream();
            this.readableStreamClosed = this.port.readable.pipeTo(textDecoder.writable);
            const reader = textDecoder.readable.getReader();
            this._reader = reader;
            while (this.connected) {
                const { value, done } = await reader.read();
                if (done) break;
                if (value) {
                    // incoming data may contain multiple lines; split and append
                    const lines = value.split(/\r?\n/).filter(l => l.trim().length);
                    for (const line of lines) {
                        this.appendSerialLog(line);
                    }
                }
            }
        } catch (e) {
            console.error('Read loop error:', e);
        }
    }

    // Append a line to the serial log area in the UI
    appendSerialLog(text) {
        try {
            const pre = document.getElementById('serialLog');
            if (!pre) return;
            const now = new Date().toLocaleTimeString();
            pre.textContent += `[${now}] ${text}\n`;
            pre.scrollTop = pre.scrollHeight;
        } catch (e) {
            console.error('Failed to append serial log', e);
        }
    }

     // Close serial port and update UI on disconnect
     disconnect() {
         if (this.port) {
             // close reader if running
             try { if (this._reader) { this._reader.cancel(); this._reader.releaseLock(); } } catch (e) {}
             try { if (this.readableStreamClosed) { this.readableStreamClosed.catch(()=>{}); } } catch (e) {}
             try { this.port.close(); } catch (e) {}
             this.port = null;
         }
         
         this.connected = false;
         this.connectBtn.textContent = 'CONNECT';
         if (this.statusDot) this.statusDot.classList.remove('connected');
         if (window.setConnectionStatus) {
             window.setConnectionStatus(false);
         } else {
             if (this.statusText) this.statusText.textContent = 'DISCONNECTED';
             if (this.sendBtn) this.sendBtn.disabled = true;
         }
         this.lastCommand = 'Disconnected';
         this.updateSystemState();
         
         console.log('[SYSTEM] Serial connection terminated');
     }

    // Send servo angles to backend over serial when EXECUTE POSITION is pressed
    async executePosition() {
        if (!this.connected || !this.port) return;
        
        // Prevent rapid repeat
        if (this._sending) return;
        this._sending = true;
        if (this.sendBtn) this.sendBtn.disabled = true;
        
        try {
            let command = '';
            for (let i = 0; i < this.numServos; i++) {
                command += `S${i+1} ${this.servoAngles[i]}`;
                if (i < this.numServos - 1) command += ',';
            }
            command += '\n';
            
            const encoder = new TextEncoder();
            const writer = this.port.writable.getWriter();
            try {
                await writer.write(encoder.encode(command));
            } finally {
                try { writer.releaseLock(); } catch (e) { /* ignore */ }
            }
            
            this.lastCommand = command.trim();
            this.updateSystemState();
            
            console.log(`[COMMAND] ${command.trim()}`);
            
        } catch (error) {
            console.error('[ERROR] Command execution failed:', error);
            alert(`Failed to execute command: ${error.message}`);
        } finally {
            // small cooldown
            setTimeout(() => {
                this._sending = false;
                if (this.sendBtn && this.connected) this.sendBtn.disabled = false;
            }, 300);
        }
    }
}

// Focus the correct servo input when a joint marker is clicked
window.focusServoInput = function(jointNum) {
    const input = document.getElementById(`input${jointNum}`);
    if (input) {
        input.focus();
        input.scrollIntoView({behavior: 'smooth', block: 'center'});
        input.select();
    }
}

// Reset all servos to 90 degrees (home position)
window.resetAllServos = function() {
    if (window.kukaController) {
        for (let i = 1; i <= window.kukaController.numServos; i++) {
            document.getElementById(`slider${i}`).value = 90;
            document.getElementById(`input${i}`).value = 90;
            document.getElementById(`value${i}`).textContent = '90°';
            window.kukaController.servoAngles[i - 1] = 90;
        }
        window.kukaController.updateSystemState();
        console.log('[SYSTEM] All joints reset to home position');
        // Also send the new home positions to the Pico if connected
        if (window.kukaController && window.kukaController.connected) {
            try { window.kukaController.executePosition(); } catch (e) { console.error('Failed to send home positions', e); }
        }
    }
}

// Initialize controller when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.kukaController = new KukaController(5);
});
