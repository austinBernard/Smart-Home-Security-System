import os

def load_password_from_file():
    try:
        with open("password.txt", "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        return None

PASSWORD = load_password_from_file()

def update_password_if_changed(PASSWORD, previous_timestamp):
    current_timestamp = os.path.getmtime("password.txt")
    if current_timestamp > previous_timestamp:
        stored_password = load_password_from_file()
        if stored_password is not None:
            PASSWORD = stored_password
            print("Password updated:", PASSWORD)
        return PASSWORD, current_timestamp
    return PASSWORD, previous_timestamp
