import subprocess

def get_paired_devices():
    """
    This function will get the list of paired Bletooth devices on Linux.

    Args: 
        None

    Returns:
        list(touple): list of paired devices like (bt_name, mac)
    """

    bt_list = []
    try:
        result = subprocess.run(['bluetoothctl', 'devices'], 
                               capture_output=True, text=True, check=True)
        result = result.stdout.strip()
        result = result.split("\n")
        for bt in result:
            bt_name = ""
            bt_mac = ""
            bt_details = bt.split(" ")
            if len(bt_details) >= 3:
                bt_name = bt_details[2]
                bt_mac = bt_details[1]
            elif len(bt_details) == 2:
                bt_name = bt_details[1]
                bt_mac = bt_details[0]
            if bt_name != "" and bt_mac != "": # a mac ID check to be implemented
                bt_list.append((bt_name, bt_mac))
    except FileNotFoundError:
        print("Error: bluetoothctl not found. Please install bluez.")
    except Exception as e:
       print(f"Error executing bluetoothctl: {e}")
    return bt_list

