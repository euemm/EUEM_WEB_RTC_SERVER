#!/usr/bin/env python3
"""
User Management Script for EUEM WebRTC Server
Allows adding and removing users from users.csv file

Usage:
    python manage_users.py add username:password [email]
    python manage_users.py remove username
    python manage_users.py list
"""

import csv
import sys
import os
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

CSV_FILE = "users.csv"
FIELDNAMES = ['username', 'email', 'hashed_password', 'is_active']


def load_users():
    """Load existing users from CSV file"""
    users = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', newline='') as file:
            reader = csv.DictReader(file)
            users = list(reader)
    return users


def save_users(users):
    """Save users to CSV file"""
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(users)


def add_user(credential_string, email=None):
    """Add a new user to the CSV file"""
    # Parse username:password
    parts = credential_string.split(':')
    if len(parts) < 2:
        print("Error: Invalid format. Use username:password")
        print("Example: python manage_users.py add john:mypassword123")
        sys.exit(1)
    
    username = parts[0]
    password = parts[1]
    
    # Use provided email or generate one
    if email is None:
        if len(parts) >= 3:
            email = parts[2]
        else:
            email = f"{username}@example.com"
    
    # Validate username
    if not username or len(username) < 3:
        print("Error: Username must be at least 3 characters long")
        sys.exit(1)
    
    # Validate password
    if not password or len(password) < 6:
        print("Error: Password must be at least 6 characters long")
        sys.exit(1)
    
    # Load existing users
    users = load_users()
    
    # Check if user already exists
    for user in users:
        if user['username'] == username:
            print(f"Error: User '{username}' already exists")
            sys.exit(1)
    
    # Hash the password
    try:
        hashed_password = pwd_context.hash(password)
    except Exception as e:
        print(f"Error hashing password: {e}")
        sys.exit(1)
    
    # Create new user
    new_user = {
        'username': username,
        'email': email,
        'hashed_password': hashed_password,
        'is_active': 'true'
    }
    
    # Add user to list
    users.append(new_user)
    
    # Save to CSV
    save_users(users)
    
    print(f"Successfully added user '{username}' with email '{email}'")


def remove_user(username):
    """Remove a user from the CSV file"""
    if not username:
        print("Error: Username is required")
        sys.exit(1)
    
    # Load existing users
    users = load_users()
    
    # Find and remove user
    initial_count = len(users)
    users = [user for user in users if user['username'] != username]
    
    if len(users) == initial_count:
        print(f"Error: User '{username}' not found")
        sys.exit(1)
    
    # Save updated list
    save_users(users)
    
    print(f"Successfully removed user '{username}'")


def list_users():
    """List all users in the CSV file"""
    users = load_users()
    
    if not users:
        print("No users found in users.csv")
        return
    
    print(f"\nTotal users: {len(users)}")
    print("-" * 60)
    print(f"{'Username':<20} {'Email':<30} {'Active':<10}")
    print("-" * 60)
    
    for user in users:
        username = user['username']
        email = user['email']
        is_active = user.get('is_active', 'true')
        print(f"{username:<20} {email:<30} {is_active:<10}")
    
    print("-" * 60)


def show_usage():
    """Show usage information"""
    print(__doc__)
    print("\nExamples:")
    print("  Add user:    python manage_users.py add john:mypassword123")
    print("  Add user with email: python manage_users.py add john:mypassword123:john@company.com")
    print("  Remove user: python manage_users.py remove john")
    print("  List users:  python manage_users.py list")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'add':
        if len(sys.argv) < 3:
            print("Error: Missing username:password argument")
            show_usage()
            sys.exit(1)
        
        credential_string = sys.argv[2]
        email = sys.argv[3] if len(sys.argv) > 3 else None
        add_user(credential_string, email)
    
    elif command == 'remove':
        if len(sys.argv) < 3:
            print("Error: Missing username argument")
            show_usage()
            sys.exit(1)
        
        username = sys.argv[2]
        remove_user(username)
    
    elif command == 'list':
        list_users()
    
    elif command in ['help', '--help', '-h']:
        show_usage()
    
    else:
        print(f"Error: Unknown command '{command}'")
        show_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()

