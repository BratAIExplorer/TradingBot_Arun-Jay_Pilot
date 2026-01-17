import customtkinter as ctk
from kickstart_gui import StartupTour, TradingGUI
import sys

# Mock settings manager for testing
class MockSettingsManager:
    def get(self, key, default):
        return False # Always say prompts NOT shown
    def set(self, key, value):
        print(f"Setting {key} to {value}")
    def save(self):
        print("Settings saved")

def test_tour():
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.title("Test Startup Tour")
    root.geometry("800x600")
    
    label = ctk.CTkLabel(root, text="Main Window (Behind Tour)", font=("Arial", 20))
    label.pack(pady=50)

    btn = ctk.CTkButton(root, text="Launch Tour", command=lambda: StartupTour(root, lambda: print("Tour Closed")))
    btn.pack(pady=20)
    
    # Auto-launch
    root.after(1000, lambda: StartupTour(root, lambda: print("Tour Closed")))
    
    root.mainloop()

if __name__ == "__main__":
    test_tour()
