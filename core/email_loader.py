# core/email_loader.py

"""
Module: email_loader
--------------------

This module provides a utility function for reading email addresses from a plain text file 
and queuing them for concurrent processing. It is designed to support a producer-consumer 
architecture, typically used with thread pools or worker queues.

Functionality:
- Reads email addresses line-by-line from a file.
- Strips leading/trailing whitespace.
- Skips empty lines.
- Enqueues valid email addresses into a thread-safe queue for downstream processing.

This is commonly used in high-throughput applications where multiple worker threads 
consume emails from a shared queue to perform validation, availability checks, or similar tasks.

Example:
    from core.email_loader import email_producer
    from queue import Queue

    q = Queue()
    email_producer('emails.txt', q)

Expected Input File Format:
    - One email address per line.
    - Empty or whitespace-only lines are ignored.
"""

def email_producer(email_file, q):
    """
    Reads email addresses from the given file and puts them into the provided queue.

    Args:
        email_file (str): Path to the text file containing email addresses.
        q (Queue): A thread-safe queue to enqueue email addresses for processing.

    Notes:
        - Strips whitespace from each line.
        - Ignores empty lines.
        - Intended for use with concurrent consumers (e.g., threads or processes).
    """
    with open(email_file, 'r') as f:
        for line in f:
            email = line.strip()
            if email:
                q.put(email)