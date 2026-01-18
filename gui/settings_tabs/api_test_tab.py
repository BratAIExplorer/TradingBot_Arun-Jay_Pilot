#!/usr/bin/env python3
"""
API Test Tab - Run API Integration Tests from GUI
Part of Enhanced Settings GUI for MVP v1.0
"""

import sys
import os
# Add parent directory to path for standalone testing
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import customtkinter as ctk
from tkinter import messagebox
import subprocess
import threading
import os

class APITestTab(ctk.CTkFrame):
    """Tab for running API integration tests"""

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()

    def setup_ui(self):
        """Build the UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="🔌 API Integration Test",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Description
        desc = ctk.CTkLabel(
            self,
            text="Test your mStock API connection without placing real orders",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        desc.pack(pady=(0, 20))

        # Test buttons
        self.create_test_buttons()

        # Output display
        self.create_output_display()

    def create_test_buttons(self):
        """Create test action buttons"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=10)

        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(pady=20)

        # Quick test button
        quick_btn = ctk.CTkButton(
            button_frame,
            text="⚡ Quick Test (30 seconds)",
            width=200,
            height=50,
            font=ctk.CTkFont(size=14),
            fg_color="#3B8ED0",
            command=self.run_quick_test
        )
        quick_btn.pack(side="left", padx=10)

        # Full test button
        full_btn = ctk.CTkButton(
            button_frame,
            text="🔬 Full Test (2-3 minutes)",
            width=200,
            height=50,
            font=ctk.CTkFont(size=14),
            command=self.run_full_test
        )
        full_btn.pack(side="left", padx=10)

        # Export button
        export_btn = ctk.CTkButton(
            button_frame,
            text="💾 Export Results",
            width=150,
            height=50,
            font=ctk.CTkFont(size=12),
            fg_color="gray",
            command=self.export_results
        )
        export_btn.pack(side="left", padx=10)

    def create_output_display(self):
        """Create output text display"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        label = ctk.CTkLabel(
            frame,
            text="Test Output:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        label.pack(pady=10, anchor="w", padx=10)

        # Use scrolled text for output
        self.output_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial message
        self.output_text.insert("1.0", "Click a test button to run API integration tests.\n\n"
                                       "Quick Test: Basic connectivity and authentication\n"
                                       "Full Test: Comprehensive test suite (all 7 tests)\n\n"
                                       "Note: No real orders will be placed!")

    def run_quick_test(self):
        """Run quick API test"""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "Starting Quick Test...\n\n")

        # Run in background thread
        threading.Thread(target=self._run_test, args=("--quick",), daemon=True).start()

    def run_full_test(self):
        """Run full API test"""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "Starting Full Test...\n\n")

        # Run in background thread
        threading.Thread(target=self._run_test, args=(), daemon=True).start()

    def _run_test(self, *args):
        """Run the test (in background thread)"""
        try:
            cmd = ["python", "test_api_integration.py"]
            if args:
                cmd.extend(args)

            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes timeout
            )

            # Display output
            output = result.stdout if result.returncode == 0 else result.stderr

            # Update UI (must be done in main thread)
            self.after(0, self._update_output, output, result.returncode == 0)

        except subprocess.TimeoutExpired:
            self.after(0, self._update_output, "❌ Test timed out after 3 minutes", False)
        except FileNotFoundError:
            self.after(0, self._update_output, "❌ Error: test_api_integration.py not found", False)
        except Exception as e:
            self.after(0, self._update_output, f"❌ Error: {str(e)}", False)

    def _update_output(self, text, success):
        """Update output text (called in main thread)"""
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)

        if success:
            messagebox.showinfo("✅ Test Complete", "API test completed successfully!\n\nCheck the output for details.")
        else:
            messagebox.showerror("❌ Test Failed", "API test encountered errors.\n\nCheck the output for details.")

    def export_results(self):
        """Export test results"""
        if os.path.exists("api_test_results.json"):
            messagebox.showinfo(
                "Results Exported",
                "Test results saved to:\napi_test_results.json\n\n"
                "You can share this file with support if needed."
            )
        else:
            messagebox.showwarning(
                "No Results",
                "No test results found.\n\nRun a test first to generate results."
            )


# Test this tab standalone
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.title("API Test Tab - Test")
    root.geometry("900x600")

    from settings_manager_v2 import SettingsManagerV2
    settings = SettingsManagerV2(settings_file="test_settings.json", auto_migrate=False)

    tab = APITestTab(root, settings)
    tab.pack(fill="both", expand=True)

    root.mainloop()
