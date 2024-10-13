import logging
from collections import deque
from Vision.main_vision import Vision as VisionClass
from Vision.Camera.camera import Camera
import time
from threading import Thread, Event

# Step 1: Configure the logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG (you can change this to INFO or WARNING)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Outputs to the console
        logging.FileHandler("test_vision.log", mode='a')  # Outputs to a log file
    ]
)

logger = logging.getLogger(__name__)  # Create a logger for this file

def main():
    
    logger.info("Initializing Vision system for testing.")

    camera = Camera()
    Vision = VisionClass(camera)
    stop_event = Event()  # Create an event to signal threads to stop

    # Start the camera's live feed in a separate thread
    live_thread = Thread(target=Vision.camera.live_feed, args=(stop_event,))
    live_thread.start()

    Vision.start("/home/edmond/egb320-team9/Videos/row2_exit_backward.mp4")  # Start the vision processing

    # Initial state setup
    current_state = 'SEARCH_FOR_ITEM'
    item_width = Vision.item_to_size('Mug')
    Vision.update_item(item_width)
    Vision.update_requested_objects(current_state)  # Set the initial state
    logger.info(f"Set requested objects state to: {current_state}")

    fps_history = deque(maxlen=10)  # Store the last 10 FPS values
    time.sleep(1)

    try:
        while True:
            now = time.time()  # Get the current time

            Vision.process_image()  # Process a single frame

            # Access the attributes of the data
            data = Vision.objectRB
            logger.debug(f"Processed data: {data}")

            elapsed = time.time() - now  # Measure the time taken to process one frame
            fps = 1.0 / elapsed
            if fps < 100:
                fps_history.append(fps)

                # Calculate the running average FPS
                avg_fps = sum(fps_history) / len(fps_history)
                logger.info(f'Elapsed Time: {elapsed:.3f}, Running Average FPS: {avg_fps:.2f}')

    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt received. Shutting down, please wait 2 seconds...")
    finally:
        stop_event.set()  # Signal the live feed thread to stop
        live_thread.join()  # Ensure the thread finishes
        #Vision.camera.close()  # Clean up the camera resources
        Vision.stop()  # Clean up the camera and Vision system resources
        logger.info("Vision system shut down gracefully.")

if __name__ == "__main__":
    main()
