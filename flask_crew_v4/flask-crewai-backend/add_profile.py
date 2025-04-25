import os
import sys
from utils import add_github_profile

def main():
    """Add a GitHub profile to the database"""
    if len(sys.argv) < 2:
        print("Usage: python add_profile.py <github_username>")
        return
    
    username = sys.argv[1]
    print(f"Adding GitHub profile for {username}...")
    
    result = add_github_profile(username)
    
    if result["success"]:
        print(f"Successfully added profile with ID: {result['profile_id']}")
    else:
        print(f"Error adding profile: {result['error']}")

if __name__ == "__main__":
    main()
