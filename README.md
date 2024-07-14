# EventHub replicator
A simple azure function app designed to replicate messages between multiple eventhubs.

# Configuration
You can setup as many replications as you want. Each replication contains a source and one or many destinations. Each replication will turn into one function in Azure Function App.
You can use whatever plan you want as long as it supports Python.

## Config file schema
The config file is a `YAML` based file with stright forward schema. To enable replication add a secion under `replications:`

Exaple config file:
```YAML
# the file contains the list of replications to be maintained by the function
schema: 1.0
replications:
  - name: "name_of_the_replication"
    source: 
      event_hub_name: "source-eventhub"
      connection: "TheNameOfTheConnection"  # will be used to do os.getenv("TheNameOfTheConnection")
      consumer_group: ""  # optional, default is "$Default".
    destinations: 
      - event_hub_name: "destination-eventhub1"
        connection: "TheNameOfTheConnection"  # will be used to do os.getenv("TheNameOfTheConnection")
      - event_hub_name: "destination-eventhub2"
        connection: "TheNameOfTheConnection"  # will be used to do os.getenv("TheNameOfTheConnection")
```
Above config will create one replication called `name_of_the_replication` thats going to get the messages from `source-eventhub` eventhub using the connection string obtained by `os.getenv("TheNameOfTheConnection")`. Make sure that `TheNameOfTheConnection` is in Function App settings.
The messages will be forwarded to two eventhubs `destination-eventhub1` and `destination-eventhub1` both sharing the same connection string as input.

### ConnectionString
The are mutiple ways the function App can connect to eventhubs. The easiest is to use ConnectionString containing SharedAccessKey. The format then would be:
`TheNameOfConnectionString="Endpoint=sb://<name_of_eh_namespace>.servicebus.windows.net/;SharedAccessKeyName=<nameofkey>;SharedAccessKey=asdzc.,.,.,"`

You can also keep the ConnectionString in KeyVault and enable Azure Function Host to pull that key on init. To do so create KeyVault, add permissions for the Function App to read secrets (via ManagedIdentity) and use:
`TheNameOfConnectionString="@Microsoft.KeyVault(SecretUri=https://xxx-na-vault.vault.azure.net/secrets/mysecret/)"`

# Deployment
You can use terraform to configure the host. You can find example in `terraform` folder.

Later just configure and deploy into azure your favourite way. For example you could use `func`:
```bash
func azure functionapp publish
```



# Development
The provided devcontainer config is sufficient to run the replicator on dev machine. 
Configure normally, put the config file into function_app directory and run 
```bash
func start
```