import time
import argparse
import urllib

import requests



def parse_args():
    """
    Parse command line arguments.

    These arguments can be passed to the service via the API. When posting to an endpoint, use the `args` parameter.
    E.g.: requests.post("http://localhost/api/service_local", json={"args" : ['--my_arg', "my_value"]})
    """
    cli = argparse.ArgumentParser()
    # These arguments are added by the DMI Service Manager in order for the service to, if desired, provide status updates which will be logged in the DMI Service Manager database.
    cli.add_argument("--database_key", "-k", default="", help="DMI Service Manager database key to provide status updates.")
    cli.add_argument("--dmi_sm_server", "-s", default="", help="DMI Service Manager server address to provide status updates.")

    return cli.parse_args()


if __name__ == "__main__":
    # "start up"
    print("Starting service...")
    args = parse_args()

    # run
    for i in range(10):
        message = f"Running iteration {i}"
        print(message)
        time.sleep(5)
        requests.post(f"{args.dmi_sm_server}/status_update/?key={args.database_key}&status=running&message={urllib.parse.quote_plus(message)}")

    # "shut down"
    print("Shutting down service...")
