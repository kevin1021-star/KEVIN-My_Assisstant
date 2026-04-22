/**
 * KEVIN HUD v2 - Component Library
 * Handles modular UI elements with Stark-Tech aesthetics.
 */

class CircularGauge {
    constructor(id, label, color = 'var(--accent)') {
        this.id = id;
        this.label = label;
        this.color = color;
        this.container = document.getElementById(id);
        if (this.container) this.render();
    }

    render() {
        const radius = 45;
        const circ = 2 * Math.PI * radius;
        this.container.innerHTML = `
            <div class="gauge-wrapper" style="position: relative; width: 100px; height: 100px;">
                <svg viewBox="0 0 100 100" style="transform: rotate(-90deg); width: 100%; height: 100%;">
                    <circle cx="50" cy="50" r="${radius}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4" />
                    <circle id="${this.id}-fill" cx="50" cy="50" r="${radius}" fill="none" 
                            stroke="${this.color}" stroke-width="4" 
                            stroke-dasharray="${circ}" stroke-dashoffset="${circ}"
                            style="transition: stroke-dashoffset 0.5s ease; filter: drop-shadow(0 0 5px ${this.color});" />
                </svg>
                <div class="gauge-info" style="position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <span id="${this.id}-value" class="eyebrow" style="font-size: 1rem; color: #fff;">0%</span>
                    <span class="eyebrow" style="font-size: 0.5rem; opacity: 0.6;">${this.label}</span>
                </div>
            </div>
        `;
        this.fill = document.getElementById(`${this.id}-fill`);
        this.valueText = document.getElementById(`${this.id}-value`);
        this.circ = circ;
    }

    update(value) {
        if (!this.fill || !this.valueText) return;
        const offset = this.circ - (value / 100) * this.circ;
        this.fill.strokeDashoffset = offset;
        this.valueText.textContent = `${Math.round(value)}%`;
    }
}

class IntelligenceFeed {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    append(role, text) {
        if (!this.container) return;
        const msg = document.createElement("div");
        msg.className = `msg ${role} glass-panel animate-in`;
        msg.style.padding = "10px";
        msg.style.marginBottom = "10px";
        msg.style.borderLeft = `3px solid ${role === 'user' ? 'var(--secondary)' : 'var(--accent)'}`;
        
        msg.innerHTML = `
            <div class="eyebrow" style="font-size: 0.5rem; margin-bottom: 5px;">[${role.toUpperCase()}_ID_${Math.floor(Math.random()*999)}]</div>
            <p style="margin: 0; font-size: 0.85rem; line-height: 1.4;">${text}</p>
        `;
        
        this.container.appendChild(msg);
        this.container.scrollTop = this.container.scrollHeight;
    }
}

window.HUD = {
    CircularGauge,
    IntelligenceFeed
};
