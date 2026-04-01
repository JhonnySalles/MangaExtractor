import sys
import os

# Add the src directory to the path to allow imports from manga_extractor
# When running as 'python -m src.manga_extractor.main', this might not be needed
# but it's good for direct execution if necessary.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from manga_extractor.gui.window import main

if __name__ == "__main__":
    main()
