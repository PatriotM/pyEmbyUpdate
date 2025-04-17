## Overview 📚

pyEmbyUpdate is a update helper for Emby.

---

## Features ✨

- **Dry-Run Mode:**  
  Allows simulation of update operations (via `--dry-run` or `--debug`) without applying any changes.

---

## Installation 🛠

1. **Install Python:**

    ```bash
    apt-get -y install python3 python3-pip
    ```

2. **Clone the Repository:**

    ```bash
    git clone https://github.com/PatriotM/pyEmbyUpdate.git
    cd pyEmbyUpdate
    ```

3. **Create and Activate a Virtual Environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

  ```bash
Usage ▶️
Run the tool using the comand
The advantage of start.sh is that it starts and stops the virtual environment after running the python application

cd /home/pyEmbyUpdate
./start.sh --debug
```

