"""
Disclaimer GUI for ARUN Trading Bot
Forces user to accept terms before proceeding.
Refactored for transparency and accessibility (Grand Mam Friendly).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

class DisclaimerGUI:
    def __init__(self, on_accept_callback):
        self.on_accept = on_accept_callback
        self._create_window()
        
    def _create_window(self):
        self.root = tk.Tk()
        self.root.title("⚠️ Important Disclaimer")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 400
        y = (self.root.winfo_screenheight() // 2) - 350
        self.root.geometry(f"+{x}+{y}")
        
        # Style
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass # Fallback to default
            
        self.style.configure("Title.TLabel", font=("Segoe UI", 28, "bold"), foreground="#DC3545")
        self.style.configure("Subtitle.TLabel", font=("Segoe UI", 16))
        self.style.configure("Big.TButton", font=("Segoe UI", 16, "bold"), padding=15)
        
        # Accept Button (High Contrast)
        self.style.configure("Accept.TButton", font=("Segoe UI", 16, "bold"), padding=15, 
                             foreground="white", background="#28A745") # Green
        self.style.map("Accept.TButton",
            foreground=[('active', 'white')],
            background=[('active', '#218838'), ('!disabled', '#28A745')]
        )
        
        # Decline Button
        self.style.configure("Decline.TButton", font=("Segoe UI", 16, "bold"), padding=15, 
                             foreground="white", background="#DC3545") # Red
        self.style.map("Decline.TButton",
            foreground=[('active', 'white')],
            background=[('active', '#C82333'), ('!disabled', '#DC3545')]
        )
        
        # Main container
        self.main_frame = ttk.Frame(self.root, padding=30)
        self.main_frame.pack(fill="both", expand=True)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header_frame, text="⚠️ ARUN TRADING BOT", style="Title.TLabel").pack()
        ttk.Label(header_frame, text="User Responsibility Agreement", style="Subtitle.TLabel").pack(pady=(5, 0))
        
        # --- Scrollable Text Area ---
        text_container = ttk.Frame(self.main_frame)
        text_container.pack(fill="both", expand=True)
        
        self.textbox = tk.Text(text_container, wrap="word", font=("Segoe UI", 14), 
                              padx=20, pady=20, bg="#F8F9FA", fg="#212529", 
                              relief="flat", highlightthickness=1, highlightbackground="#DEE2E6")
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.textbox.yview)
        self.textbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.textbox.pack(side="left", fill="both", expand=True)
        
        disclaimer_text = """
⚠️ CRITICAL WARNING - READ BEFORE PROCEEDING ⚠️

1. NOT FINANCIAL ADVICE
The ARUN Trading Bot is a SOFTWARE TOOL ONLY. It does NOT provide investment, financial, legal, or tax advice. You are solely responsible for:
• Configuring all strategy parameters
• Deciding which stocks to trade
• Determining position sizes and risk levels

2. HIGH RISK - POTENTIAL TOTAL LOSS
Trading stocks and derivatives involves significant risk. You could lose SOME or ALL of your invested capital. Past performance does NOT guarantee future results.

3. USER RESPONSIBILITY & LIABILITY
By using this software, you acknowledge:
• YOU are responsible for all trading decisions
• YOU accept full liability for any profits OR losses
• The developers are NOT liable for any financial losses
• Software bugs, API failures, or connectivity issues may occur

4. SOFTWARE PROVIDED "AS IS"
No warranties of any kind. No guarantees of uptime, accuracy, or profitability.

5. PAPER TRADING FIRST
You MUST test your strategies in "Paper Trading" mode before risking real money.

By clicking "I ACCEPT", you confirm you understand these risks and accept full responsibility for your trading activities.
"""
        self.textbox.insert("1.0", disclaimer_text)
        self.textbox.configure(state="disabled")
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.main_frame)
        nav_frame.pack(fill="x", pady=(20, 0))
        
        self.accept_btn = ttk.Button(nav_frame, text="I ACCEPT & UNDERSTAND RISKS", 
                                    command=self.accept, style="Accept.TButton")
        self.accept_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.decline_btn = ttk.Button(nav_frame, text="DECLINE (EXIT)", 
                                     command=self.decline, style="Decline.TButton")
        self.decline_btn.pack(side="right", fill="x", expand=True)
        
        self.root.mainloop()

    def accept(self):
        self.root.destroy()
        self.on_accept()

    def decline(self):
        sys.exit(0)

if __name__ == "__main__":
    def start_app():
        print("Disclaimer Accepted - Starting App...")
    DisclaimerGUI(start_app)
