"""
First-Run Setup Wizard for ARUN Trading Bot
A simple 3-step wizard to help new users get started safely.

Part of v2.4.0 - Family-Ready UX Sprint
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# Try to import settings manager
try:
    from settings_manager import SettingsManager
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False


class FirstRunWizard:
    """3-step wizard for first-time setup"""
    
    # Suggested stock packs with risk disclaimer
    STOCK_PACKS = {
        "conservative_etfs": {
            "name": "📊 Conservative ETFs",
            "description": "Low-risk index funds that track the market",
            "stocks": [
                {"symbol": "NIFTYBEES", "exchange": "NSE", "quantity": 10},
                {"symbol": "GOLDBEES", "exchange": "NSE", "quantity": 20},
                {"symbol": "BANKBEES", "exchange": "NSE", "quantity": 10},
            ]
        },
        "blue_chips": {
            "name": "💎 Blue Chips",
            "description": "Large, established companies with stable growth",
            "stocks": [
                {"symbol": "RELIANCE", "exchange": "NSE", "quantity": 5},
                {"symbol": "INFY", "exchange": "NSE", "quantity": 10},
                {"symbol": "HDFCBANK", "exchange": "NSE", "quantity": 5},
            ]
        }
    }
    
    RISK_PROFILES = {
        "conservative": {
            "name": "🛡️ Conservative",
            "description": "Lower risk, smaller moves",
            "stop_loss_pct": 3,
            "profit_target_pct": 8,
            "never_sell_at_loss": True
        },
        "moderate": {
            "name": "⚖️ Moderate",
            "description": "Balanced risk and reward",
            "stop_loss_pct": 5,
            "profit_target_pct": 10,
            "never_sell_at_loss": False
        },
        "aggressive": {
            "name": "🔥 Aggressive",
            "description": "Higher risk, larger potential gains",
            "stop_loss_pct": 7,
            "profit_target_pct": 15,
            "never_sell_at_loss": False
        }
    }
    
    def __init__(self, on_complete_callback=None):
        self.on_complete = on_complete_callback
        self.settings = SettingsManager() if SETTINGS_AVAILABLE else None
        self.current_step = 1
        
        # Data collected from wizard
        self.api_key = ""
        self.api_secret = ""
        self.client_code = ""
        self.selected_risk = "moderate"
        self.selected_stocks = []
        
        self._create_window()
        
    def _create_window(self):
        self.root = tk.Toplevel() if hasattr(tk, '_default_root') and tk._default_root else tk.Tk()
        self.root.title("ARUN Setup Wizard")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 400
        y = (self.root.winfo_screenheight() // 2) - 325
        self.root.geometry(f"+{x}+{y}")
        
        # Style
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass # Fallback to default if clam not available
            
        self.style.configure("Title.TLabel", font=("Segoe UI", 28, "bold"))
        self.style.configure("Subtitle.TLabel", font=("Segoe UI", 16))
        self.style.configure("Warning.TLabel", font=("Segoe UI", 14), foreground="#DC3545")
        self.style.configure("Success.TLabel", font=("Segoe UI", 16), foreground="#28A745")
        
        # Consistent Button styles
        self.style.configure("Big.TButton", font=("Segoe UI", 16, "bold"), padding=15)
        
        # Action Button (High Contrast)
        self.style.configure("Action.TButton", font=("Segoe UI", 16, "bold"), padding=15, 
                             foreground="white", background="#01579B") # Dark Blue
        self.style.map("Action.TButton",
            foreground=[('active', 'white'), ('disabled', 'gray')],
            background=[('active', '#0288D1'), ('!disabled', '#01579B')]
        )
        
        # Style for radio and check buttons to ensure they have large text
        self.style.configure("TRadiobutton", font=("Segoe UI", 16))
        self.style.configure("TCheckbutton", font=("Segoe UI", 16))
        
        # Set default font for entries
        self.root.option_add("*Font", "{Segoe UI} 16")
        
        # Main container
        self.main_frame = ttk.Frame(self.root, padding=30)
        self.main_frame.pack(fill="both", expand=True)
        
        # Header with step indicator
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.step_label = ttk.Label(self.header_frame, text="Step 1 of 3", style="Subtitle.TLabel")
        self.step_label.pack(side="right")
        
        self.title_label = ttk.Label(self.header_frame, text="Welcome to ARUN", style="Title.TLabel")
        self.title_label.pack(side="left")
        
        # --- Scrollable Content Area ---
        self.canvas_container = ttk.Frame(self.main_frame)
        self.canvas_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.canvas.yview)
        
        self.content_frame = ttk.Frame(self.canvas)
        self.content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        self.content_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Mousewheel support
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Navigation buttons (Fixed at bottom)
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(fill="x", pady=(20, 0))
        
        self.back_btn = ttk.Button(self.nav_frame, text="← Back", command=self._go_back, style="Big.TButton")
        self.back_btn.pack(side="left")
        
        self.next_btn = ttk.Button(self.nav_frame, text="Next →", command=self._go_next, style="Action.TButton")
        self.next_btn.pack(side="right")
        
        # Show first step
        self._show_step_1()

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        canvas_width = event.width
        self.canvas.itemconfig(self.content_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        try:
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass
        
    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
    def _update_header(self, title, step):
        self.title_label.config(text=title)
        self.step_label.config(text=f"Step {step} of 3")
        self.back_btn.config(state="normal" if step > 1 else "disabled")
        self.next_btn.config(text="Finish ✓" if step == 3 else "Next →")
    
    # ==================== STEP 1: API Credentials ====================
    def _show_step_1(self):
        self._clear_content()
        self._update_header("Connect Your Broker", 1)
        self.current_step = 1
        
        ttk.Label(self.content_frame, text="Enter your mStock API credentials:", 
                  style="Subtitle.TLabel").pack(anchor="w", pady=(0, 20))
        
        # API Key
        ttk.Label(self.content_frame, text="API Key:", style="Subtitle.TLabel").pack(anchor="w")
        self.api_key_entry = ttk.Entry(self.content_frame, width=65, font=("Segoe UI", 16))
        self.api_key_entry.pack(anchor="w", pady=(5, 25))
        self.api_key_entry.insert(0, self.api_key)
        
        # API Secret  
        ttk.Label(self.content_frame, text="API Secret:", style="Subtitle.TLabel").pack(anchor="w")
        self.api_secret_entry = ttk.Entry(self.content_frame, width=65, show="*", font=("Segoe UI", 16))
        self.api_secret_entry.pack(anchor="w", pady=(5, 25))
        self.api_secret_entry.insert(0, self.api_secret)
        
        # Client Code
        ttk.Label(self.content_frame, text="Client Code (e.g., MA1234567):", style="Subtitle.TLabel").pack(anchor="w")
        self.client_code_entry = ttk.Entry(self.content_frame, width=65, font=("Segoe UI", 16))
        self.client_code_entry.pack(anchor="w", pady=(5, 25))
        self.client_code_entry.insert(0, self.client_code)
        
        # Test connection button
        self.test_btn = ttk.Button(self.content_frame, text="🔌 Test Connection", 
                                   command=self._test_connection, style="Big.TButton")
        self.test_btn.pack(anchor="w", pady=(0, 10))
        
        self.connection_status = ttk.Label(self.content_frame, text="", style="Subtitle.TLabel")
        self.connection_status.pack(anchor="w")
        
        # Help text
        ttk.Label(self.content_frame, 
                  text="💡 Get your API credentials from: https://developer.mstock.trade",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(20, 0))
                  
    def _test_connection(self):
        self.connection_status.config(text="Testing...", style="Subtitle.TLabel")
        self.root.update()
        
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            self.connection_status.config(text="❌ Please enter API Key", style="Warning.TLabel")
            return
            
        # Simple connectivity check (we can't fully auth without TOTP)
        try:
            response = requests.get("https://api.mstock.trade/", timeout=5)
            if response.status_code < 500:
                self.connection_status.config(
                    text="✅ mStock API is reachable. Credentials will be validated on first trade.", 
                    style="Success.TLabel"
                )
            else:
                self.connection_status.config(
                    text="⚠️ mStock API returned an error. Check credentials.", 
                    style="Warning.TLabel"
                )
        except Exception as e:
            self.connection_status.config(
                text=f"❌ Connection failed: {str(e)[:50]}", 
                style="Warning.TLabel"
            )
    
    # ==================== STEP 2: Risk Level ====================
    def _show_step_2(self):
        self._clear_content()
        self._update_header("Choose Your Risk Level", 2)
        self.current_step = 2
        
        ttk.Label(self.content_frame, 
                  text="How much risk are you comfortable with?",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(0, 15))
        
        self.risk_var = tk.StringVar(value=self.selected_risk)
        
        for key, profile in self.RISK_PROFILES.items():
            frame = ttk.Frame(self.content_frame)
            frame.pack(fill="x", pady=5)
            
            rb = ttk.Radiobutton(frame, text=profile["name"], 
                                 variable=self.risk_var, value=key)
            rb.pack(side="left")
            
            desc = ttk.Label(frame, text=f"  ({profile['description']})", 
                            style="Subtitle.TLabel")
            desc.pack(side="left")
        
        # Show what each setting means
        info_frame = ttk.LabelFrame(self.content_frame, text="What This Means", padding=15)
        info_frame.pack(fill="x", pady=(25, 0))
        
        ttk.Label(info_frame, text="🛑 Stop Loss: Automatically sell if price drops to limit losses",
                  style="Subtitle.TLabel", wraplength=700).pack(anchor="w")
        ttk.Label(info_frame, text="🎯 Profit Target: Automatically sell when profit goal is reached",
                  style="Subtitle.TLabel", wraplength=700).pack(anchor="w", pady=(10, 0))
        ttk.Label(info_frame, text="🛡️ Never Sell at Loss: Hold until profitable (conservative only)",
                  style="Subtitle.TLabel", wraplength=700).pack(anchor="w", pady=(10, 0))
    
    # ==================== STEP 3: Stock Selection ====================
    def _show_step_3(self):
        self._clear_content()
        self._update_header("Pick Your Stocks", 3)
        self.current_step = 3
        
        ttk.Label(self.content_frame, 
                  text="Choose stocks for ARUN to monitor and trade:",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(0, 10))
        
        # CRITICAL: Risk Disclaimer
        disclaimer_frame = ttk.Frame(self.content_frame)
        disclaimer_frame.pack(fill="x", pady=(0, 15))
        
        disclaimer_text = (
            "⚠️ IMPORTANT: These are suggestions for educational purposes only, "
            "NOT buy/sell signals. All investment decisions are YOUR responsibility. "
            "Past performance does not guarantee future results. You may lose money."
        )
        disclaimer_label = ttk.Label(disclaimer_frame, text=disclaimer_text,
                                     style="Warning.TLabel", wraplength=700)
        disclaimer_label.pack(fill="x", padx=10, pady=10)
        
        # Stock pack options
        self.pack_vars = {}
        
        for key, pack in self.STOCK_PACKS.items():
            pack_frame = ttk.LabelFrame(self.content_frame, text=pack["name"], padding=15)
            pack_frame.pack(fill="x", pady=10)
            
            ttk.Label(pack_frame, text=pack["description"], 
                     style="Subtitle.TLabel").pack(anchor="w")
            
            stock_names = ", ".join([s["symbol"] for s in pack["stocks"]])
            ttk.Label(pack_frame, text=f"Stocks: {stock_names}",
                     style="Subtitle.TLabel").pack(anchor="w", pady=(10, 0))
            
            self.pack_vars[key] = tk.BooleanVar(value=False)
            ttk.Checkbutton(pack_frame, text="Add this pack to my watchlist",
                           variable=self.pack_vars[key], style="TCheckbutton").pack(anchor="w", pady=(10, 0))
        
        # Custom option
        custom_frame = ttk.LabelFrame(self.content_frame, text="✏️ I'll Add My Own", padding=15)
        custom_frame.pack(fill="x", pady=10)
        
        ttk.Label(custom_frame, 
                  text="You can add custom stocks later in the Settings panel.",
                  style="Subtitle.TLabel").pack(anchor="w")
    
    # ==================== Navigation ====================
    def _go_back(self):
        if self.current_step == 2:
            self._show_step_1()
        elif self.current_step == 3:
            self._show_step_2()
            
    def _go_next(self):
        if self.current_step == 1:
            # Save credentials
            self.api_key = self.api_key_entry.get().strip()
            self.api_secret = self.api_secret_entry.get().strip()
            self.client_code = self.client_code_entry.get().strip()
            
            if not self.client_code:
                messagebox.showwarning("Missing Info", "Please enter your Client Code to continue.")
                return
                
            self._show_step_2()
            
        elif self.current_step == 2:
            self.selected_risk = self.risk_var.get()
            self._show_step_3()
            
        elif self.current_step == 3:
            self._finish_wizard()
    
    def _finish_wizard(self):
        """Save all settings and close wizard"""
        try:
            # Collect selected stocks from packs
            self.selected_stocks = []
            for key, var in self.pack_vars.items():
                if var.get():
                    self.selected_stocks.extend(self.STOCK_PACKS[key]["stocks"])
            
            # Get risk profile
            risk_profile = self.RISK_PROFILES[self.selected_risk]
            
            if self.settings:
                # Save broker credentials
                if self.api_key:
                    self.settings.set("broker.api_key", self.api_key)
                if self.api_secret:
                    self.settings.set("broker.api_secret", self.api_secret)
                if self.client_code:
                    self.settings.set("broker.client_code", self.client_code)
                
                # Save risk settings
                self.settings.set("risk_controls.default_stop_loss_pct", risk_profile["stop_loss_pct"])
                self.settings.set("risk_controls.default_profit_target_pct", risk_profile["profit_target_pct"])
                self.settings.set("risk.never_sell_at_loss", risk_profile["never_sell_at_loss"])
                
                # Save selected stocks
                stock_configs = []
                for stock in self.selected_stocks:
                    stock_configs.append({
                        "symbol": stock["symbol"],
                        "exchange": stock["exchange"],
                        "enabled": True,
                        "strategy": "TRADE",
                        "timeframe": "15T",
                        "buy_rsi": 35,
                        "sell_rsi": 65,
                        "quantity": stock.get("quantity", 10),
                        "profit_target_pct": risk_profile["profit_target_pct"]
                    })
                self.settings.set("stocks", stock_configs)
                
                # Mark first run as complete
                self.settings.set("app_settings.first_run_completed", True)
                
                # Save to disk
                self.settings.save()
                
                messagebox.showinfo(
                    "Setup Complete! 🎉",
                    f"ARUN is now configured with:\n\n"
                    f"• {len(self.selected_stocks)} stocks to monitor\n"
                    f"• {self.RISK_PROFILES[self.selected_risk]['name']} risk profile\n"
                    f"• Paper Trading mode (safe to test)\n\n"
                    f"Click 'Start Engine' on the dashboard to begin!"
                )
            else:
                messagebox.showwarning(
                    "Settings Error",
                    "Could not save settings. Please configure manually in Settings panel."
                )
            
            self.root.destroy()
            
            if self.on_complete:
                self.on_complete()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def run(self):
        """Start the wizard"""
        self.root.mainloop()


def should_show_wizard() -> bool:
    """Check if first-run wizard should be displayed"""
    if not SETTINGS_AVAILABLE:
        return False
    
    try:
        settings = SettingsManager()
        
        # 1. Check for manual configuration (Bypass if credentials exist)
        api_key = settings.get("broker.api_key")
        client_code = settings.get("broker.client_code")
        
        if api_key and client_code:
            # User has configured manually or restored settings
            return False
        
        # 2. Check strict first run flag
        first_run_completed = settings.get("app_settings.first_run_completed", False)
        if first_run_completed:
            return False
            
        return True
        
    except Exception:
        return False


def run_wizard_if_needed(on_complete=None):
    """Run wizard if this is first launch"""
    if should_show_wizard():
        wizard = FirstRunWizard(on_complete_callback=on_complete)
        wizard.run()
        return True
    return False


if __name__ == "__main__":
    # Test the wizard standalone
    wizard = FirstRunWizard()
    wizard.run()
