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
        this.statusText = document.getElementById('statusText');
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
        
        this.currentState.innerHTML = `
// System Status: ${this.connected ? 'Active' : 'Standby'}
// Joint Positions: [${positions}]
// Last Command: ${this.lastCommand}
// Connection: ${status}
        `.trim();
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
            this.statusDot.classList.add('connected');
            this.statusText.textContent = 'CONNECTED';
            this.sendBtn.disabled = false;
            this.lastCommand = 'Connected';
            this.updateSystemState();
            
            console.log('[SYSTEM] Serial connection established');
            
        } catch (error) {
            console.error('[ERROR] Connection failed:', error);
            alert(`Connection failed: ${error.message}`);
        }
    }

    // Close serial port and update UI on disconnect
    disconnect() {
        if (this.port) {
            this.port.close();
            this.port = null;
        }
        
        this.connected = false;
        this.connectBtn.textContent = 'CONNECT';
        this.statusDot.classList.remove('connected');
        this.statusText.textContent = 'DISCONNECTED';
        this.sendBtn.disabled = true;
        this.lastCommand = 'Disconnected';
        this.updateSystemState();
        
        console.log('[SYSTEM] Serial connection terminated');
    }

    // Send servo angles to backend over serial when EXECUTE POSITION is pressed
    async executePosition() {
        if (!this.connected || !this.port) return;
        
        try {
            let command = '';
            for (let i = 0; i < this.numServos; i++) {
                command += `S${i+1} ${this.servoAngles[i]}`;
                if (i < this.numServos - 1) command += ',';
            }
            command += '\n';
            
            const encoder = new TextEncoder();
            const writer = this.port.writable.getWriter();
            
            await writer.write(encoder.encode(command));
            writer.releaseLock();
            
            this.lastCommand = command.trim();
            this.updateSystemState();
            
            console.log(`[COMMAND] ${command.trim()}`);
            
        } catch (error) {
            console.error('[ERROR] Command execution failed:', error);
            alert(`Failed to execute command: ${error.message}`);
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
    }
}

// Initialize controller when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.kukaController = new KukaController(5);
});
