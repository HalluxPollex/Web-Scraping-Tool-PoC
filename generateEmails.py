"""
Random Email Generator Script

This script generates a list of random, realistic-looking Gmail addresses and writes them to a text file.
Useful for testing email validation systems, load testing, or simulating user input.

Key Features:
    • Random username composed of lowercase letters and digits
    • Generates 5000 unique email addresses
    • Saves output to 'random_emails.txt'
"""

try:
    import random
    import string

    def generate_random_email() -> str:
        """Generates a random 10-character Gmail address."""
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f"{username}@gmail.com"

    # Generate 5000 random emails
    emails = [generate_random_email() for _ in range(5000)]

    # Save to file
    with open("random_emails.txt", "w") as f:
        for email in emails:
            f.write(email + "\n")

    print("[+] 5000 random emails saved to random_emails.txt")

except Exception as e:
    print(f"[!] Error: {e}")