"""Simple function to replicate data from one Eventhub to others"""

import logging
from pathlib import Path
from typing import List

import azure.functions as func
import yaml

OUTPUT_PARAM_PREFIX = "outputeventhub"


def eventhub_replicator(inputeventhub: func.EventHubEvent, *outputs: func.Out[str]):
    """
    EventHub trigger function that replicates events from a source event hub to multiple destination event hubs.

    Args:
        inputeventhub (func.EventHubEvent): The input event hub event.
        *outputs (func.Out[str]): Variable number of output bindings for the destination event hubs.
    """
    if not isinstance(inputeventhub, list):
        inputeventhub = [inputeventhub]
    for event in inputeventhub:
        event = event.get_body()
        logging.info("Python EventHub trigger processed an event: %s", event.decode("utf-8")[:140])

        for output in outputs:
            output.set(event)


def create_replicator_function(outputs=1):
    """
    Creates a replicator function with the specified number of output bindings.

    Args:
        outputs (int): The number of output bindings.

    Returns:
        function: The replicator function.
    """
    function_name = f"eventhub_replicator_{outputs}"
    f = locals().get(function_name)
    if not f:
        output_names = [f"{OUTPUT_PARAM_PREFIX}{x}" for x in range(outputs)]
        function_text = f"""def eventhub_replicator_{outputs}(inputeventhub: func.EventHubEvent, {",".join([f"{x}: func.Out[str]" for x in output_names])}):"""
        function_text += "\n"
        function_text += f"""    eventhub_replicator(inputeventhub,{",".join(output_names)})\n"""

        logging.info(f"compiling function: {function_text}")
        exec(function_text)
        f = locals().get(function_name)
        if not f:
            raise Exception(f"unable to compile {function_text}")
    return f


def build_replication_function(name, source, destinations: List[dict]):
    """
    Builds a replication function blueprint with the specified name, source event hub, and destination event hubs.

    Args:
        name (str): The name of the replication function.
        source (dict): The source event hub configuration.
        destinations (List[dict]): The list of destination event hub configurations.

    Returns:
        func.Blueprint: The replication function blueprint.
    """
    blueprint = func.Blueprint()
    replicator_function = create_replicator_function(len(destinations))
    ret = blueprint.function_name(name=name)(replicator_function)
    kwargs = {}
    if "consumer_group" in source:
        kwargs["consumer_group"] = source["consumer_group"]

    ret = blueprint.event_hub_message_trigger(
        arg_name="inputeventhub",
        event_hub_name=source["event_hub_name"],
        connection=source["connection"],
        cardinality="many",
        **kwargs,
    )(ret)
    destination_no = 0
    for destination in destinations:
        ret = blueprint.event_hub_output(
            arg_name=f"{OUTPUT_PARAM_PREFIX}{destination_no}",
            event_hub_name=destination["event_hub_name"],
            connection=destination["connection"],
        )(ret)
        destination_no += 1
    return blueprint


def read_replication_config():
    """
    Reads the replication configuration from the 'replication_config.yaml' file.

    Returns:
        list: A list of replication configurations.
    """
    config_path = Path(__file__).parent / "replications.yaml"
    with config_path.open("r") as f:
        return yaml.safe_load(f)["replications"]


app = func.FunctionApp()
replications = read_replication_config()
replications2 = [
    {
        "name": "first_replication",
        "source": {"event_hub_name": "pep-adx-td-eg-poc", "connection": "pep-adx-td-eg-poc_replicatorpull_EVENTHUB"},
        "destinations": [
            {"event_hub_name": "combined_ehs", "connection": "pep-adx-td-eg-poc_replicatorpull_EVENTHUB"},
            {"event_hub_name": "combined_ehs2", "connection": "pep-adx-td-eg-poc_replicatorpull_EVENTHUB"},
        ],
    }
]
for replication in replications:
    name = replication["name"]
    source = replication["source"]
    destinations = replication["destinations"]
    app.register_functions(build_replication_function(name, source, destinations))

print("done")
