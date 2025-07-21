"""
Main entry point for the email verification tool.

This script orchestrates the overall workflow: parsing CLI arguments, initializing the shared queue, 
spawning a producer thread to feed emails, and launching a pool of worker threads for parallel processing. 
It manages the lifecycle of the entire scraping/verification task, gracefully handling thread coordination, 
error logging, and optional result output to a JSON file.

Workflow:
    1. Parse CLI arguments (input file, number of workers, etc.)
    2. Start a producer thread to enqueue emails from file.
    3. Launch a pool of workers that:
        - Fetch emails from the shared queue
        - Use independent sessions and proxies
        - Store the results with thread-safe locking
    4. Wait until queue is drained and all workers are finished.
    5. Print and optionally save results to disk.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import logging
import time
import json

from cli.main import parse_args, setup_logging
from core import email_producer, worker


def main():
    start_time = time.time()
    
    # Parse command-line arguments
    args = parse_args()
    setup_logging(args.verbosity)

    # Create a thread-safe queue for email addresses
    email_q: queue.Queue[str] = queue.Queue(maxsize=5000)

    # Start producer thread to load emails into the queue
    prod = threading.Thread(
        name="producer",
        target=email_producer,
        args=(args.file, email_q),
        daemon=True,
    )
    prod.start()
    logging.info("Producer started reading email file")

    # Shared dictionary for results and a lock for thread-safe access
    results: dict[str, str] = {}
    results_lock = threading.Lock()

    # Launch worker threads using a thread pool
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(
                worker,
                email_q,
                worker_id,
                args.emails_per_worker,
                results,
                results_lock,
            )
            for worker_id in range(1, args.workers + 1)
        ]

        # Optional: Wait for producer to finish reading file
        # prod.join()
        # logging.info("Producer finished reading file")

        # Wait until the email queue is fully processed
        logging.info("Waiting for email queue to fully drain...")
        email_q.join()
        logging.info("Email queue join complete (all tasks marked done)")

        # Wait for all worker threads to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Worker raised an exception: {e}")

    end_time = time.time()

    # Print runtime statistics
    print(f"Total emails checked: {len(results)}")
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

    # Save results if output file was specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logging.info(f"Saved results to {args.output}")
    else:
        logging.info("No output file requested. Skipping JSON export.")

    logging.info("All emails processed; shutting down.")

if __name__ == "__main__":
    main()