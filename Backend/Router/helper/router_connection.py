# router_connection.py

from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
from Router.models import Router  # Adjust import to your app name

def connect_to_router(router):
    try:
        connection = ConnectHandler(
            device_type=router.device_type,  # mikrotik_routeros, juniper, etc.
            host=router.ip,
            username=router.ssh_username,
            password=router.ssh_password,
            port=22, 
        )
        return connection
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        raise Exception(f"Connection failed: {str(e)}")


def disconnect_router(connection):
    try:
        connection.disconnect()
    except Exception:
        pass


def send_command_to_router(connection, command):
    try:
        output = connection.send_command(command)
        return output
    except Exception as e:
        return f"Error executing command: {str(e)}"

def send_bulk_commands(connection, commands):
    results = {}
    try:
        output = connection.send_config_set(commands)  # bulk send
    except Exception as e:
        output =  f"Error: {str(e)}"
    return output


    # for cmd in commands:
    #     try:
    #         output = connection.send_command(cmd)
    #         results[cmd] = output
    #     except Exception as e:
    #         results[cmd] = f"Error: {str(e)}"
    # return results
