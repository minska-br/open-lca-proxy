# Life Cycle Assessment Api

> This API has the functionality to provide access to Life Cycle Assessment information through the databases provided by the OpenLCA Nexus software.

<p align="center">
  <a href="#installation-and-requirements">Installation and Requirements</a> • 
  <a href="#how-to-run">How to run</a> •  
  <a href="#api-documentation">Api documentation</a> • 
  <a href="#architecture">Architecture</a> • 
  <a href="#license">License</a>
</p>

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development.

## Installation and Requirements

These instructions will get you a copy of the project up and running on your local machine for development. Before we install the application we need these systems and tools configured and installed:

- [Open LCA Nexus](https://www.openlca.org/download/)
- [Python version >= 3](https://www.python.org/downloads/)
- [Aws-cli](https://aws.amazon.com/pt/cli/)
- [Docker](https://docs.docker.com/get-docker/)

It is very easy to install and upload the application. Just follow the steps below and everything will be fine! 🎉

### Application

```
git clone https://github.com/thalees/life-cycle-assessment-api.git
cd life-cycle-assessment-api
```

After accessing the project folder, create and activate your virtual environment
```
virtualenv venv && . venv/bin/activate
```

Install the necessary dependencies:
```
pip3 install -r requirements.txt
```

### SQS

To run the calculation flow it is necessary to go up and configure the infrastructure and create the queue that will be used by the application. To mock AWS services we are using localstack. To run it, just run the command below:
```
docker-compose up -d
```

After the localstack container has successfully uploaded, create the queue in SQS using the `make` command:
```
make create-queue
```

### Open LCA Nexus

OpenLCA or Olca is the system responsible for the data used to calculate the carbon footprint of products. This application must be configured and running on port `8084`. 
> 📢 _The data used for this application were the data available on the [Open LCA](https://www.openlca.org/) website free of charge. We chose the database called [Agribalyse](https://nexus.openlca.org/database/Agribalyse)_.

## How to run

After performing the initial setup, with your virtual environment active, just run the server:
```
uvicorn main:app
```

Your application will be running on `localhost:8000`

## Api documentation

This project has all its endpoints documented in **Postman** as a **shared collection**, to get a copy of its endpoints, just click the link below:

[![Run in Postman](https://run.pstmn.io/button.svg)](https://www.getpostman.com/collections/db463e8924381444ee4e)

If you want to see the documentation on the **swagger**, just click the button below to view:

[![View in Swagger](assets/view-in-swagger-button.svg)](http://localhost:8000/docs)
> 📢 _This button execute the documentation on the endpoint `/doc` in your local environment (localhost)._

## Architecture

**_TODO_**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
<p align="center"><b>Thanks and good tests 🎉</b></p>
<p align="center">
  <img width="100" height="100" alt="bye" src="https://media.giphy.com/media/JO3FKwP5Fwx44uMfDI/giphy.gif">
</p>