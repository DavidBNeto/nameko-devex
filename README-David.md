# Nameko Examples
![Airship Ltd](airship.png)
## Airship Ltd
Buying and selling quality airships since 2012

## Prerequisites of setting up Development Environment

* [Pycharm](https://www.jetbrains.com/pycharm/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
* [Anaconda](https://www.anaconda.com/download)

## Setup

### Setting up environment

* Create conda environment
```ps1
$ conda env create -f environment_dev.yml
```
* To activate environment
```ps1
$ conda activate nameko-devex

// all commands after activation will have the right binaries references. You must always be in this environment to run and debug this project
```
* To deactivate environment
```ps1
$ conda deactivate nameko-devex
```
* To install the required dependencies
```ps1
$ .\install_requirements.ps1
```

### Start services locally
* Activate conda environment using `conda activate nameko-devex`
* Start backing services as docker containers
```ps1
$ (nameko-devex) .\dev_run_backingsvcs.ps1

// This will run rabbitmq, postgres and redis
```

* Start a nameko services 
```ps1
$ (nameko-devex) .\dev_run.ps1 ${service name}

// where service name is either gateway.service or orders.service or products.service
// instead of being able to run all services in a single script, the .ps1 file only lets you run one at each time
```

* Smoke test
```ps1
$ (nameko-devex) .\test\nex-smoketest.ps1 local
```

* Performance test
```ps1
$ (nameko-devex) .\dev_pytest.ps1
```

Important notes:
- The performance of the performance test starts degrading as the test goes on due to the schemas that require serialization, mainly in the list-orders method. One solution to this performance issue would be the creation of a much simplified schema related to a table that contains order_id, order_details_id and product_id
- The performance of the delete-product method was sacrificed in order to maintain data consistency, since it deletes the orders that have that product-id. If not done so, get-order and list-orders would be much more prone to error 
- Some indexes were added to the database. Its creation was added to the migrations initial shema
- I apologize in advance, I don't have an environment to test the .sh scripts, so I rely heavily on .ps1 scripts