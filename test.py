import json
from netmiko import ConnectHandler

juniper_router = {
    "device_type": "juniper_junos",
    "host": "10.110.60.233",
    "username": "admin",
    "password": "admin123",
    
}

try:
    connection = ConnectHandler(**juniper_router)
    print(f"Connected to {juniper_router['host']}")

    # Disable paging
    connection.send_command("set cli screen-length 0")

    # Run the command in JSON format
    raw_json = connection.send_command(
        "show configuration policy-options | display json",read_timeout= 600
    )

    # Parse JSON string into Python dictionary
    data = json.loads(raw_json)

    # Print the raw JSON nicely
    print("\n=== Full Policy Options in JSON ===")
    print(json.dumps(data, indent=2))

    # Example: Extract all policy statement names
    print("\n=== Policy Statement Names ===")
    policy_statements = data.get("configuration", {}).get("policy-options", {}).get("policy-statement", [])
    for policy in policy_statements:
        print(policy.get("name"))

    connection.disconnect()
    print("\nConnection closed.")

except Exception as e:
    print(f"Error: {e}")
