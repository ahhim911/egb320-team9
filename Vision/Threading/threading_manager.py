import threading

class ThreadingManager:
    @staticmethod
    def run_parallel_processing(tasks):
        threads = []
        for task in tasks:
            thread = threading.Thread(target=task['function'], args=task['args'])
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
