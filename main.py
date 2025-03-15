import sys
import os
import random
import string
import json
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import QUrl, QObject, pyqtSlot, QPoint, QCoreApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineScript
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtGui import QScreen

VERSION = "0.1.0"  # Version constant

class WebBridge(QObject):
    """Bridge class for JavaScript to Python communication"""
    
    def __init__(self):
        super().__init__()
        self.save_file = "clicker_save.json"
    
    @pyqtSlot(str, result=str)
    def save_game(self, game_state):
        """Save game state to file"""
        try:
            with open(self.save_file, 'w') as f:
                f.write(game_state)
            return "Game saved successfully"
        except Exception as e:
            return f"Error saving game: {str(e)}"
    
    @pyqtSlot(result=str)
    def load_game(self):
        """Load game state from file"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    return f.read()
            return "{}"
        except Exception as e:
            return "{}"
            
    @pyqtSlot()
    def show_about(self):
        """Show the About dialog"""
        msg = QMessageBox()
        msg.setWindowTitle("About Byte Clicker")
        msg.setText(f"Byte Clicker v{VERSION}")
        msg.setInformativeText("A fun incremental game about collecting bytes!\n\n"
                              "Click to generate bytes and buy generators to automate your byte production.\n\n"
                              "© 2024 Byte Clicker")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        
    @pyqtSlot()
    def exit_app(self):
        """Exit the application with confirmation"""
        reply = QMessageBox.question(None, 'Exit Confirmation',
                                   'Are you sure you want to exit?\nMake sure to save your game!',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            QCoreApplication.quit()

class WebWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Byte Clicker v{VERSION}")
        
        # Set fixed size 1280x720
        self.setFixedSize(1280, 720)
        
        # Center window on screen
        self.center_window()
        
        # Create WebView
        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)
        
        # Create bridge object
        self.bridge = WebBridge()
        
        # Set up QWebChannel
        self.setup_web_channel()
        
        # Load initial HTML
        self.load_html()
    
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def setup_web_channel(self):
        """Set up the QWebChannel for JavaScript bridge"""
        page = self.web_view.page()
        self.channel = QWebChannel(page)
        page.setWebChannel(self.channel)
        
        script = QWebEngineScript()
        with open('qwebchannel/qwebchannel.js', 'r') as f:
            script.setSourceCode(f.read())
        script.setName("qwebchannel.js")
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setRunsOnSubFrames(True)
        
        page.scripts().insert(script)
        self.channel.registerObject("bridge", self.bridge)
    
    def load_html(self):
        """Load the initial HTML content"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Byte Clicker</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                .container {
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                .main-section {
                    background-color: #2d2d2d;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                }
                .stats-section {
                    background-color: #2d2d2d;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                }
                .click-area {
                    width: 200px;
                    height: 200px;
                    background-color: #4CAF50;
                    border-radius: 50%;
                    margin: 20px auto;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    user-select: none;
                    transition: transform 0.1s;
                }
                .click-area:active {
                    transform: scale(0.95);
                }
                .generator {
                    background-color: #3d3d3d;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    border: 1px solid #4d4d4d;
                }
                .generator:hover:not(.locked) {
                    background-color: #4d4d4d;
                    transform: translateY(-2px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                .generator:active:not(.locked) {
                    transform: translateY(0);
                }
                .generator.locked {
                    background-color: #2a2a2a;
                    color: #666;
                    cursor: not-allowed;
                }
                .generator.affordable {
                    border-color: #4CAF50;
                }
                .generator-name {
                    font-weight: bold;
                    font-size: 1.1em;
                    margin-bottom: 5px;
                }
                .generator-cost {
                    color: #4CAF50;
                }
                .generator-production {
                    color: #888;
                    font-size: 0.9em;
                }
                .generator-unlock-text {
                    color: #666;
                    font-style: italic;
                    font-size: 0.9em;
                    margin-top: 5px;
                }
                .stats {
                    font-size: 18px;
                    margin-bottom: 10px;
                }
                .progress-bar {
                    width: 100%;
                    height: 20px;
                    background-color: #1e1e1e;
                    border-radius: 10px;
                    overflow: hidden;
                    margin-top: 5px;
                }
                .progress-fill {
                    height: 100%;
                    background-color: #4CAF50;
                    width: 0%;
                    transition: width 0.3s;
                }
                .save-button {
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 5px;
                    min-width: 120px;
                }
                .save-button:hover {
                    background-color: #45a049;
                }
                .new-game-button {
                    padding: 10px 20px;
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 5px;
                    min-width: 120px;
                }
                .new-game-button:hover {
                    background-color: #d32f2f;
                }
                .exit-button {
                    padding: 10px 20px;
                    background-color: #757575;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 5px;
                    min-width: 120px;
                }
                .exit-button:hover {
                    background-color: #616161;
                }
                .about-button {
                    padding: 10px 20px;
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 5px;
                    min-width: 120px;
                }
                .about-button:hover {
                    background-color: #1976D2;
                }
                .button-container {
                    display: flex;
                    justify-content: center;
                    gap: 10px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="main-section">
                    <h1>Byte Clicker</h1>
                    <div class="stats">
                        Bytes: <span id="bytes">0</span><br>
                        Bytes per second: <span id="bps">0</span>
                    </div>
                    <div class="click-area" onclick="click_byte()">
                        CLICK
                    </div>
                    <div id="generators"></div>
                </div>
                <div class="stats-section">
                    <div class="button-container">
                        <button class="save-button" onclick="save_game()">Save Game</button>
                        <button class="new-game-button" onclick="new_game()">New Game</button>
                        <button class="exit-button" onclick="exit_app()">Exit</button>
                        <button class="about-button" onclick="show_about()">About</button>
                    </div>
                    <h2>Statistics</h2>
                    <div id="stats"></div>
                </div>
            </div>
            
            <script>
                let game_state = {
                    bytes: 0,
                    total_bytes: 0,
                    clicks: 0,
                    generators: [
                        { id: 0, name: "Auto Clicker", base_cost: 10, cost: 10, count: 0, base_production: 0.1, unlocked: true },
                        { id: 1, name: "Byte Compiler", base_cost: 50, cost: 50, count: 0, base_production: 0.5, unlocked: false },
                        { id: 2, name: "Data Miner", base_cost: 250, cost: 250, count: 0, base_production: 2, unlocked: false },
                        { id: 3, name: "Quantum Computer", base_cost: 1000, cost: 1000, count: 0, base_production: 10, unlocked: false },
                        { id: 4, name: "AI Cluster", base_cost: 5000, cost: 5000, count: 0, base_production: 50, unlocked: false },
                        { id: 5, name: "Quantum Network", base_cost: 25000, cost: 25000, count: 0, base_production: 250, unlocked: false },
                        { id: 6, name: "Digital Dimension", base_cost: 100000, cost: 100000, count: 0, base_production: 1000, unlocked: false }
                    ],
                    last_save: Date.now(),
                    game_start: Date.now()
                };

                // Initialize QWebChannel
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.bridge = channel.objects.bridge;
                    load_game();
                });

                function format_number(num) {
                    if (num >= 1e6) {
                        return (num / 1e6).toFixed(2) + 'M';
                    } else if (num >= 1e3) {
                        return (num / 1e3).toFixed(2) + 'K';
                    }
                    return num.toFixed(2);
                }

                function click_byte() {
                    game_state.bytes += 1 + get_click_multiplier();
                    game_state.total_bytes += 1 + get_click_multiplier();
                    game_state.clicks += 1;
                    update_display();
                    check_unlocks();
                }

                function get_click_multiplier() {
                    return Math.floor(game_state.generators[0].count / 10) * 0.1;
                }

                function get_bytes_per_second() {
                    return game_state.generators.reduce((sum, gen) => 
                        sum + (gen.count * gen.base_production), 0);
                }

                function buy_generator(id) {
                    const generator = game_state.generators[id];
                    if (game_state.bytes >= generator.cost && generator.unlocked) {
                        game_state.bytes -= generator.cost;
                        generator.count += 1;
                        generator.cost = Math.ceil(generator.base_cost * Math.pow(1.15, generator.count));
                        
                        // Visual feedback
                        const element = document.querySelector(`[data-id="${id}"]`);
                        if (element) {
                            element.style.backgroundColor = '#4CAF50';
                            setTimeout(() => {
                                element.style.backgroundColor = '';
                            }, 100);
                        }
                        
                        check_unlocks();
                        update_display();
                    }
                }

                function check_unlocks() {
                    game_state.generators.forEach((gen, index) => {
                        if (!gen.unlocked && index > 0) {
                            const prev_gen = game_state.generators[index - 1];
                            if (prev_gen.count >= 5) {
                                gen.unlocked = true;
                                update_display();
                            }
                        }
                    });
                }

                function update_display() {
                    // Update only the text content of existing elements
                    document.getElementById('bytes').textContent = format_number(game_state.bytes);
                    document.getElementById('bps').textContent = format_number(get_bytes_per_second());
                    
                    // Update stats text
                    document.getElementById('total-bytes').textContent = format_number(game_state.total_bytes);
                    document.getElementById('total-clicks').textContent = game_state.clicks;
                    document.getElementById('click-power').textContent = format_number(1 + get_click_multiplier());
                    document.getElementById('time-played').textContent = format_time(Date.now() - game_state.game_start);
                    
                    // Update generator displays
                    game_state.generators.forEach((gen, id) => {
                        const element = document.querySelector(`[data-id="${id}"]`);
                        if (element) {
                            const affordable = game_state.bytes >= gen.cost;
                            element.classList.toggle('affordable', affordable && gen.unlocked);
                            element.classList.toggle('locked', !gen.unlocked);
                            
                            element.querySelector('.generator-name').textContent = `${gen.name} (${gen.count})`;
                            element.querySelector('.generator-cost').textContent = `Cost: ${format_number(gen.cost)} bytes`;
                            element.querySelector('.generator-production').textContent = 
                                `Producing: ${format_number(gen.count * gen.base_production)} bytes/s`;
                        }
                    });
                }

                function format_time(ms) {
                    const seconds = Math.floor(ms / 1000);
                    const minutes = Math.floor(seconds / 60);
                    const hours = Math.floor(minutes / 60);
                    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
                }

                function game_loop() {
                    const now = Date.now();
                    const delta = (now - game_state.last_update) / 1000;
                    game_state.last_update = now;
                    
                    const production = get_bytes_per_second() * delta;
                    game_state.bytes += production;
                    game_state.total_bytes += production;
                    
                    update_display();
                }

                function new_game() {
                    if (confirm("Are you sure you want to start a new game? This will erase your current progress.")) {
                        const now = Date.now();
                        game_state = {
                            bytes: 0,
                            total_bytes: 0,
                            clicks: 0,
                            generators: [
                                { id: 0, name: "Auto Clicker", base_cost: 10, cost: 10, count: 0, base_production: 0.1, unlocked: true },
                                { id: 1, name: "Byte Compiler", base_cost: 50, cost: 50, count: 0, base_production: 0.5, unlocked: false },
                                { id: 2, name: "Data Miner", base_cost: 250, cost: 250, count: 0, base_production: 2, unlocked: false },
                                { id: 3, name: "Quantum Computer", base_cost: 1000, cost: 1000, count: 0, base_production: 10, unlocked: false },
                                { id: 4, name: "AI Cluster", base_cost: 5000, cost: 5000, count: 0, base_production: 50, unlocked: false },
                                { id: 5, name: "Quantum Network", base_cost: 25000, cost: 25000, count: 0, base_production: 250, unlocked: false },
                                { id: 6, name: "Digital Dimension", base_cost: 100000, cost: 100000, count: 0, base_production: 1000, unlocked: false }
                            ],
                            last_save: now,
                            game_start: now,
                            last_update: now
                        };
                        check_unlocks();
                        update_display();
                        save_game();  // Save the new game state
                    }
                }

                function save_game() {
                    if (window.bridge) {
                        game_state.last_save = Date.now();
                        bridge.save_game(JSON.stringify(game_state))
                            .then(response => {
                                // Show save feedback
                                const saveBtn = document.querySelector('.save-button');
                                saveBtn.textContent = 'Saved!';
                                setTimeout(() => {
                                    saveBtn.textContent = 'Save Game';
                                }, 1000);
                            });
                    }
                }

                function load_game() {
                    if (window.bridge) {
                        bridge.load_game().then(saved_state => {
                            try {
                                const loaded_state = JSON.parse(saved_state);
                                if (Object.keys(loaded_state).length > 0) {
                                    game_state = loaded_state;
                                    game_state.last_update = Date.now();
                                    update_display();
                                    check_unlocks();
                                }
                            } catch (e) {
                                console.error("Error loading game:", e);
                            }
                        });
                    }
                }

                function show_about() {
                    if (window.bridge) {
                        bridge.show_about();
                    }
                }

                function exit_app() {
                    if (window.bridge) {
                        bridge.exit_app();
                    }
                }

                // Initialize game
                game_state.last_update = Date.now();
                
                // Game loop
                setInterval(game_loop, 100);  // Update every 100ms
                setInterval(save_game, 60000);  // Auto-save every minute

                // Initial HTML structure for stats
                document.getElementById('stats').innerHTML = `
                    <div>Total Bytes: <span id="total-bytes">0</span></div>
                    <div>Total Clicks: <span id="total-clicks">0</span></div>
                    <div>Click Power: <span id="click-power">1.00</span></div>
                    <div>Time Played: <span id="time-played">0h 0m 0s</span></div>
                `;

                // Initial HTML structure for generators
                document.getElementById('generators').innerHTML = game_state.generators.map(gen => `
                    <div class="generator ${gen.unlocked ? 'affordable' : 'locked'}" data-id="${gen.id}"
                         onclick="buy_generator(${gen.id})"
                         title="${gen.unlocked ? 'Click to buy' : 'Unlock by buying 5 of previous generator'}">
                        <div class="generator-name">${gen.name} (${gen.count})</div>
                        <div class="generator-cost">Cost: ${format_number(gen.cost)} bytes</div>
                        <div class="generator-production">Producing: ${format_number(gen.count * gen.base_production)} bytes/s</div>
                        ${gen.unlocked ? '' : '<div class="generator-unlock-text">Unlock by buying 5 of previous generator</div>'}
                    </div>
                `).join('');
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html, QUrl("about:blank"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebWindow()
    window.show()
    sys.exit(app.exec())
