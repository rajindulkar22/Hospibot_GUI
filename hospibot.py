#!/usr/bin/env python3
import os
import time
import threading
import tkinter as tk
from tkinter import messagebox
import subprocess
import requests
import queue
import shutil
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
TEAMS_URL = "https://teams.microsoft.com"
USER_DATA_DIR = "/home/hospibot/hospibot_ws/doctortrial/teams_profile_pi"

# --- Global Queues ---
command_queue = queue.Queue()
gui_queue = queue.Queue()

# --- Helper Functions for Window Management ---

def run_xdotool(args):
    """Runs xdotool commands silently."""
    try:
        subprocess.run(["xdotool"] + args, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

def force_cleanup_profile():
    """Kills stuck chrome processes and removes the Profile Lock."""
    print("Cleaning up stuck Chromium processes...")
    try:
        subprocess.run(["pkill", "-f", "chromium"], check=False)
        subprocess.run(["pkill", "-f", "chrome"], check=False)
        time.sleep(1)
    except:
        pass

    lock_file = os.path.join(USER_DATA_DIR, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("Removed stuck lock file (Self-Healing).")
        except Exception as e:
            print(f"Warning: Could not remove lock file: {e}")

def switch_to_pwa():
    """Hides GUI, Shows PWA App, and FORCES Fullscreen."""
    print("Switching to TEAMS PWA...")
    gui_queue.put(("set_view", "browser"))
    time.sleep(0.5)
    run_xdotool(["search", "--class", "chromium", "windowactivate"])
    time.sleep(0.5)
    run_xdotool(["search", "--class", "chromium", "windowstate", "--add", "fullscreen"])

def switch_to_gui():
    """Hides PWA, Shows GUI."""
    print("Switching to GUI...")
    run_xdotool(["search", "--class", "chromium", "windowstate", "--remove", "fullscreen"])
    time.sleep(0.2)
    run_xdotool(["search", "--class", "chromium", "windowminimize"])
    time.sleep(0.2)
    run_xdotool(["search", "--name", "Hospibot Pi", "windowactivate"])
    gui_queue.put(("set_view", "gui"))

def wait_for_network():
    while True:
        try:
            requests.head(TEAMS_URL, timeout=5)
            print("Network is UP.")
            return
        except:
            gui_queue.put(("status", "Waiting for Internet..."))
            time.sleep(5)

# --- BROWSER WORKER ---

def browser_worker():
    wait_for_network()
    force_cleanup_profile()
    
    while True:
        gui_queue.put(("status", "System Loading..."))
        
        try:
            with sync_playwright() as p:
                print("Launching Teams (Auto-Setup Mode)...")
                
                exec_path = "/usr/bin/chromium"
                if not os.path.exists(exec_path):
                    exec_path = "/usr/bin/chromium-browser"

                launch_args = [
                    f"--app={TEAMS_URL}",
                    "--start-fullscreen", 
                    "--no-default-browser-check",
                    "--force-device-scale-factor=0.93",
                    "--use-fake-ui-for-media-stream",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--test-type"
                ]

                context = p.chromium.launch_persistent_context(
                    USER_DATA_DIR,
                    executable_path=exec_path,
                    headless=False,
                    permissions=["camera", "microphone"],
                    viewport={"width": 720, "height": 1280},
                    args=launch_args,
                    ignore_default_args=["--enable-automation"]
                )

                if len(context.pages) > 0:
                    page = context.pages[0]
                else:
                    time.sleep(1)
                    page = context.pages[0]
                
                # --- STARTUP STABILIZATION ---
                print("Stabilizing Window...")
                time.sleep(5)
                for _ in range(3):
                    switch_to_pwa()
                    time.sleep(1)
                
                # --- SMART LOGIN HANDLER ---
                if not _handle_login_flow(page):
                    continue 

                switch_to_gui()
                _internal_reset_ready(page)

                # --- COMMAND LOOP ---
                while True:
                    try:
                        try:
                            cmd = command_queue.get(timeout=1.0)
                            if cmd == "CALL":
                                _internal_perform_call(page)
                            elif cmd == "EXIT":
                                context.close()
                                return
                            command_queue.task_done()
                        except queue.Empty:
                            pass
                        
                        if page.is_closed():
                            raise Exception("App Window closed unexpectedly")
                            
                    except Exception as e:
                        print(f"Worker Loop Error: {e}")
                        break

                context.close()
        
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            print("Running Cleanup and Restarting...")
            force_cleanup_profile() 
            gui_queue.put(("status", "System Recovering..."))
            time.sleep(3)

def _handle_login_flow(page):
    gui_queue.put(("status", "Checking Login..."))
    
    try:
        page.goto("https://teams.microsoft.com", wait_until="domcontentloaded", timeout=60000)
    except: pass

    video_btn_selector = 'button[aria-label*="Video"], [data-tid="video-call-button"]'
    
    try:
        page.wait_for_selector(video_btn_selector, timeout=5000)
        print("Already Logged In.")
        return True
    except:
        pass

    print("First Run / Login Required.")
    gui_queue.put(("status", "Please Log In..."))
    switch_to_pwa() 
    
    try:
        page.click('button:has-text("Use the web app instead")', timeout=3000)
    except: pass

    print("Waiting for user to complete login...")
    for _ in range(150): 
        try:
            if page.locator(video_btn_selector).count() > 0:
                print("Login Detected! Completing setup...")
                return True
        except:
            pass
        time.sleep(2)
    
    print("Login timed out.")
    return False

def _internal_reset_ready(page):
    print("Resetting State...")
    gui_queue.put(("status", "Checking Line..."))
    switch_to_gui()

    video_btn = page.locator('button[aria-label*="Video"], [data-tid="video-call-button"]').first

    try:
        if video_btn.is_visible():
            print("FAST PATH: Button already visible.")
            gui_queue.put(("status", "Ready to Call"))
            gui_queue.put(("btn_state", "ready"))
            return
    except: pass

    print("Cleaning up potential popups...")
    try:
        page.locator('button[aria-label="Close"]').click(timeout=300)
    except: pass
    try:
        page.locator('button:has-text("Dismiss")').click(timeout=300)
    except: pass

    try:
        if video_btn.is_visible():
            print("READY after cleanup.")
            gui_queue.put(("status", "Ready to Call"))
            gui_queue.put(("btn_state", "ready"))
            return
    except: pass

    print("Button missing. (Direct navigation disabled)")
    time.sleep(2)

def _internal_perform_call(page):
    print("EXECUTE CALL...")
    gui_queue.put(("status", "Dialing..."))
    switch_to_pwa()

    try:
        page.locator('button[aria-label*="Video"], [data-tid="video-call-button"]').first.click()
    except Exception:
        try:
            page.keyboard.press("Alt+Shift+V")
        except Exception: pass

    call_active = False
    POLL_INTERVAL = 0.5
    for _ in range(120):
        try:
            join_btn = page.locator('button:has-text("Join now")')
            if join_btn.count() > 0 and join_btn.first.is_visible():
                join_btn.first.click()
                time.sleep(2)

            if (page.locator('button[title="Hang up"]').count() > 0 or 
                page.locator('[data-tid="call-duration"]').count() > 0):
                call_active = True
                break
            if page.get_by_text("Call ended", exact=False).count() > 0:
                break
        except Exception: pass
        time.sleep(POLL_INTERVAL)

    if call_active:
        print("Call Active.")
        gui_queue.put(("status", "Call in Progress"))
        while True:
            time.sleep(POLL_INTERVAL)
            try:
                if page.get_by_text("Call ended", exact=False).count() > 0: break
                if page.get_by_text("Quality of this call", exact=False).count() > 0: break
                if (page.locator('button[title="Hang up"]').count() == 0 and 
                    page.locator('[data-tid="call-duration"]').count() == 0):
                    time.sleep(1)
                    if page.locator('button[title="Hang up"]').count() == 0: break
            except: pass

    print("Call Finished.")
    switch_to_gui()
    gui_queue.put(("status", "Resetting..."))
    try:
        if page.get_by_text("Call ended", exact=False).count() > 0:
             page.locator('button[title="Dismiss"]').click(timeout=1000)
    except: pass
    try:
        page.locator('button[aria-label="Close"]').click(timeout=500)
    except: pass
    _internal_reset_ready(page)

# --- GUI CLASS ---

class HospibotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospibot Pi")
        self.root.configure(bg="#0b132b")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)

        self.frame = tk.Frame(root, bg="#0b132b")
        self.frame.pack(expand=True, fill="both")

        # --- EXIT BUTTON RESTORED HERE ---
        self.exit_btn = tk.Button(root, text="EXIT", font=("Arial", 10), command=self.close_app, bg="red", fg="white")
        self.exit_btn.place(x=0, y=0)
        
        # Escape key kept as backup
        self.root.bind("<Escape>", lambda event: self.close_app())

        tk.Label(self.frame, text="Hospibot: Call Doctor", font=("Helvetica", 30, "bold"), fg="white", bg="#0b132b").pack(pady=60)

        self.status_var = tk.StringVar(value="Initializing Pi System...")
        self.lbl_status = tk.Label(self.frame, textvariable=self.status_var, font=("Helvetica", 16), fg="#aaaaaa", bg="#0b132b")
        
        self.btn = tk.Button(
            self.frame, text="System Loading...", font=("Helvetica", 24, "bold"),
            bg="#333333", fg="white", padx=50, pady=30, relief="raised", bd=5,
            state="disabled", command=self.on_call_click
        )
        self.btn.pack(pady=20)
        self.lbl_status.pack(pady=20)

        self.root.after(100, self.process_gui_queue)
        self.thread = threading.Thread(target=browser_worker, daemon=True)
        self.thread.start()

    def process_gui_queue(self):
        try:
            while True:
                msg_type, msg_data = gui_queue.get_nowait()
                if msg_type == "status": self.status_var.set(msg_data)
                elif msg_type == "btn_state":
                    if msg_data == "ready": self.btn.config(state="normal", bg="#1f4068", text="Start Video Call")
                    elif msg_data == "disabled": self.btn.config(state="disabled", bg="#333333", text="Please Wait...")
                elif msg_type == "set_view":
                    if msg_data == "gui":
                        self.root.deiconify(); self.root.attributes('-fullscreen', True); self.root.attributes('-topmost', True); self.root.lift(); self.root.focus_force()
                    elif msg_data == "browser": self.root.withdraw()
                elif msg_type == "error": messagebox.showerror("Error", msg_data)
                gui_queue.task_done()
        except queue.Empty: pass
        self.root.after(100, self.process_gui_queue)

    def on_call_click(self):
        self.btn.config(state="disabled", text="Calling...")
        self.status_var.set("Connecting...")
        command_queue.put("CALL")

    def close_app(self):
        command_queue.put("EXIT")
        self.root.destroy()

if __name__ == "__main__":
    import traceback
    log_path = os.path.expanduser("~/hospibot_error.log")
    try:
        root = tk.Tk()
        app = HospibotGUI(root)
        root.mainloop()
    except Exception:
        with open(log_path, "w") as f:
            traceback.print_exc(file=f)
        raise
