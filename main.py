import os
import sys
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    print("="*40)
    print("      AQI ML ORCHESTRATOR MENU")
    print("="*40)
    print("1. 📊 Train ML Model (Fetch Data & Export rf_model.pkl)")
    print("2. 🚀 Start Live Predictor (Host API on Port 5000)")
    print("3. ❌ Exit")
    print("="*40)

def train_model():
    clear_screen()
    print("Launching Training Pipeline...\n")
    try:
        # We run the training script externally so it executes cleanly
        subprocess.run([sys.executable, "train_model.py"], check=True)
    except subprocess.CalledProcessError:
        print("\n[ERROR] Training script encountered an issue.")
    except Exception as e:
        print(f"\n[ERROR] Could not start training: {e}")
    input("\nPress Enter to return to the main menu...")

def start_predictor():
    clear_screen()
    print("Launching Live Predictor API...")
    print("Press Ctrl+C at any time to halt the server and return here.\n")
    try:
        # We run the flask script externally blocking until Ctrl+C is pressed
        subprocess.run([sys.executable, "live_predictor.py"])
    except KeyboardInterrupt:
        print("\n🛑 Server halted by user.")
    except Exception as e:
        print(f"\n[ERROR] Predictor failed to start: {e}")
    
    print("\nReturning to main menu...")
    input("Press Enter to continue...")

def main():
    while True:
        clear_screen()
        show_menu()
        choice = input("\nSelect an option (1-3): ").strip()

        if choice == '1':
            train_model()
        elif choice == '2':
            start_predictor()
        elif choice == '3':
            clear_screen()
            print("Exiting AQI ML Orchestrator. Goodbye! 👋")
            break
        else:
            print("\nInvalid selection. Please type 1, 2, or 3.")
            input("Press Enter to try again...")

if __name__ == "__main__":
    # Change working directory to ensure it can find the child scripts
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if necessary files exist before launching menu
    if not os.path.exists("live_predictor.py") or not os.path.exists("train_model.py"):
        print("ERROR: Core scripts (live_predictor.py, train_model.py) are missing!")
        print("Please ensure they are in the same directory as main.py.")
        sys.exit(1)
        
    main()
