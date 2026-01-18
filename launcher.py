#!/usr/bin/env python3
"""
Convenient launcher for Plant Taxonomy Database tools.

Provides easy access to all database tools and GUI.
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def show_menu():
    """Show main menu."""
    print("\n" + "="*70)
    print(" "*20 + "PLANT TAXONOMY DATABASE")
    print("="*70)
    print("\nAvailable Tools:")
    print("\n  [1] Populate Database - Add diverse plant species")
    print("  [2] Launch GUI - Browse and visualize taxonomy")
    print("  [3] Enhanced Demo - Test data sources with fallback")
    print("  [4] Test Offline - Verify installation")
    print("  [5] Interactive Mode - Command-line interface")
    print("\n  [Q] Quit")
    print("\n" + "="*70)
    

def run_populate():
    """Run database population script."""
    print("\n" + "🌱"*35)
    print("DATABASE POPULATION")
    print("🌱"*35)
    print("\nOptions:")
    print("  [1] Quick test (10 species)")
    print("  [2] Standard (all ~33 species)")
    print("  [3] Custom")
    print("  [B] Back")
    
    choice = input("\nChoice: ").strip().upper()
    
    if choice == 'B':
        return
    elif choice == '1':
        cmd = [sys.executable, str(SCRIPT_DIR / "populate_database.py"), 
               "--db", "test_populated.db", "--max", "10"]
    elif choice == '2':
        cmd = [sys.executable, str(SCRIPT_DIR / "populate_database.py"),
               "--db", "plants_populated.db"]
    elif choice == '3':
        db = input("Database filename [plants.db]: ").strip() or "plants.db"
        max_species = input("Max species (blank for all): ").strip()
        cmd = [sys.executable, str(SCRIPT_DIR / "populate_database.py"),
               "--db", db]
        if max_species:
            cmd.extend(["--max", max_species])
    else:
        print("Invalid choice")
        return
    
    print("\nStarting population...")
    subprocess.run(cmd)
    
    input("\nPress Enter to continue...")


def run_gui():
    """Launch GUI."""
    print("\n" + "🖥️ "*35)
    print("LAUNCHING GUI")
    print("🖥️ "*35)
    
    # Find existing databases
    db_files = list(SCRIPT_DIR.glob("*.db"))
    
    if db_files:
        print("\nAvailable databases:")
        for i, db in enumerate(db_files, 1):
            size = db.stat().st_size / 1024
            print(f"  [{i}] {db.name} ({size:.1f} KB)")
        print(f"  [{len(db_files) + 1}] Open different file")
        print("  [B] Back")
        
        choice = input("\nChoice: ").strip().upper()
        
        if choice == 'B':
            return
        elif choice.isdigit() and 1 <= int(choice) <= len(db_files):
            db_path = str(db_files[int(choice) - 1])
            cmd = [sys.executable, str(SCRIPT_DIR / "taxonomy_gui.py"), db_path]
        else:
            cmd = [sys.executable, str(SCRIPT_DIR / "taxonomy_gui.py")]
    else:
        print("\nNo databases found. GUI will start with no database loaded.")
        print("Use File → Open Database to load a database.")
        input("\nPress Enter to continue...")
        cmd = [sys.executable, str(SCRIPT_DIR / "taxonomy_gui.py")]
    
    subprocess.run(cmd)


def run_demo():
    """Run enhanced demo."""
    print("\n" + "🔬"*35)
    print("ENHANCED DEMO")
    print("🔬"*35)
    print("\nOptions:")
    print("  [1] Standard demo")
    print("  [2] Verbose demo (detailed logging)")
    print("  [3] Interactive mode")
    print("  [B] Back")
    
    choice = input("\nChoice: ").strip().upper()
    
    if choice == 'B':
        return
    elif choice == '1':
        cmd = [sys.executable, str(SCRIPT_DIR / "demo_enhanced.py")]
    elif choice == '2':
        cmd = [sys.executable, str(SCRIPT_DIR / "demo_enhanced.py"), "--verbose"]
    elif choice == '3':
        cmd = [sys.executable, str(SCRIPT_DIR / "demo_enhanced.py"), "--interactive"]
    else:
        print("Invalid choice")
        return
    
    subprocess.run(cmd)
    input("\nPress Enter to continue...")


def run_offline_test():
    """Run offline tests."""
    print("\n" + "🧪"*35)
    print("OFFLINE TESTS")
    print("🧪"*35)
    print("\nRunning offline verification tests...\n")
    
    cmd = [sys.executable, str(SCRIPT_DIR / "test_offline.py")]
    subprocess.run(cmd)
    
    input("\nPress Enter to continue...")


def main():
    """Main menu loop."""
    while True:
        show_menu()
        choice = input("\nChoice: ").strip().upper()
        
        if choice == '1':
            run_populate()
        elif choice == '2':
            run_gui()
        elif choice == '3':
            run_demo()
        elif choice == '4':
            run_offline_test()
        elif choice == '5':
            cmd = [sys.executable, str(SCRIPT_DIR / "demo_enhanced.py"), "--interactive"]
            subprocess.run(cmd)
        elif choice == 'Q':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
