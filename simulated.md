Registering Inventory Plugin
This document guides you through registering and testing a developed SpaceONE plugin.

1. Environment Setup 
Before registering the plugin, the following environment setup is required.

1) Endpoint Configuration 

vi ~/.spaceone/environments/local.yml
restart ↺
1-1) To register an Inventory plugin, you need gRPC endpoints for Identity, Inventory, and Repository services.


spacectl config endpoint add identity grpc://localhost:8083
spacectl config endpoint add inventory grpc://localhost:8084
spacectl config endpoint add repository grpc://localhost:8085
restart ↺
The added service endpoints are as follows:

~/.spaceone/environments/local.yml
api_key: eyJ...
endpoints:
  plugin: grpc://localhost:50051
  identity: grpc://localhost:8083
  inventory: grpc://localhost:8084
  repository: grpc://localhost:8085

2) Port Forwarding 
Port forwarding allows gRPC communication with each microservice in the local environment.


kubectl port-forward svc/identity -n cloudforet 8083:50051 --address=0.0.0.0 &
kubectl port-forward svc/inventory -n cloudforet 8084:50051 --address=0.0.0.0 &
kubectl port-forward svc/repository -n cloudforet 8085:50051 --address=0.0.0.0 &
If issues occur, you can close the ports with the following command:

kill $(ps aux | grep 'kubectl port-forward' | awk '{print $2}')


2-1) Now that you’ve completed port forwarding for all 6 microservices, let’s check the available API list once.

spacectl api-resources
restart ↺
For more detailed API information, please refer to Cloudforet API .

2. Repository Registration 
1) Repository Check 
You can confirm that Managed Repository exists. Managed Repository is the default repository provided by SpaceONE. Create a new repository for registering the plugin on your local machine.


spacectl list repository.Repository
restart ↺
 repository_id   | name               | repository_type   | created_at
-----------------+--------------------+-------------------+--------------------------
 repo-managed    | Managed Repository | managed           | 2024-07-15T04:14:07.640Z

 Count: 1 / 1

2) Repository Registration 
register_repository.yaml
---
repository_type: local
name: Local Repository

spacectl exec register repository.Repository -f register_repository.yaml
restart ↺
2-2) Now, if you check the repository again, you can see that Local Repository has been registered. The repository_id is generated as a hash value.

The repository_id value is different for each user.

spacectl list repository.Repository
restart ↺
 repository_id     | name               | repository_type   | created_at
-------------------+--------------------+-------------------+--------------------------
 repo-managed      | Managed Repository | managed           | 2024-07-15T04:14:07.640Z
 repo-16a1409f9992 | Local Repository   | local             | 2024-07-25T16:22:58.162Z

 Count: 2 / 2

3. Schema Creation 
Schema provides templates for entering Secret Data in SpaceONE Console.

1) Schema Check 
Before creating a schema for Local Repository, check what schemas exist in Managed Repository.

spacectl list repository.Schema -p repository_id=repo-managed --minimal
restart ↺
Now, let’s create a new schema for Local Repository.

2) Schema Creation 
2-1) If you check the schema for the repository_id generated, you can see that there is no schema created yet.


spacectl list repository.Schema -p repository_id=repo-16a1409f9992
restart ↺
NO DATA

2-2) The YAML specification for creating a new schema in Local Repository is as follows.

create_schema.yaml
---
name: portfolio_investment_schema
service_type: secret.credentials
schema:
  properties:
    investment_type:
      minLength: 4.0
      title: Investment Type
      type: string
  required:
    - investment_type
  type: object
labels:
  - Investment
tags:
  description: Investment Credentials

spacectl exec create repository.Schema -f create_schema.yaml
restart ↺
4. Provider Creation 
As mentioned in Service Account, SpaceONE provides 3 CSPs (AWS, Azure, GCP) by default.

Since the plugin developed in the example collects data based on price standards, it is a bit different from CSP. However, the default Provider is the resource indicating where the collected data comes from.

That is, if data exists, you can group the data by what type of Provider.

1) Provider Check 
You can check the current registered providers, which are the default providers AWS, Azure, Google Cloud.


spacectl list identity.Provider --minimal
restart ↺
 provider     | name         |   order
--------------+--------------+---------
 aws          | AWS          |       1
 google_cloud | Google Cloud |       2
 azure        | Azure        |       3

 Count: 3 / 3

2) Provider Creation 
First, let’s create a YAML specification needed to register a Provider.

create_provider.yaml
---
provider: portfolio
name: Portfolio
tags:
  icon: https://www.svgrepo.com/show/195329/mortgage-insurance.svg
  label: Portfolio
template:
  service_account:
    schema:
      properties:
        amount:
          minLength: 4.0
          title: Asset
          type: string
      required:
        - amount
      type: object
capability:
  supported_schema:
    - portfolio_investment_schema
metadata:
  view:
    layouts:
      help:service_account:create:
        name: Creation Help
        options:
          markdown:
            en: "# Getting Started with Portfolio

              Easily manage and track your assets through Portfolio.

              ## Portfolio Type

              Please enter the type of asset. (e.g., savings account, stocks, cryptocurrency)
              "
            ko: "# Portfolio 시작 가이드

              Portfolio를 통해 자산을 쉽게 관리하고 추적하세요.

              ##  Portfolio 타입

              어떤 종류의 자산인지 입력해주세요. (적금, 주식, 암호 화폐 등)
              "

spacectl exec create identity.Provider -f create_provider.yaml
restart ↺
2-3) If you check the provider again, you can see that portfolio has been added.


spacectl list identity.Provider --minimal
restart ↺
 provider     | name         |   order
--------------+--------------+---------
 aws          | AWS          |       1
 google_cloud | Google Cloud |       2
 azure        | Azure        |       3
 portfolio    | Portfolio    |      10

 Count: 4 / 4

2-4) And in the cloud service, you can also see a provider named ‘Portfolio’.

5. Service Account Creation 
SpaceONE Service Account functions as follows:

Through Service Account and Project resources, you can group collected resources from the outside and manage them.
Service Account means the collection unit of the plugin.
For example, if there is a Provider named Investment, you can create Service Accounts under Investment, and manage them by grouping them with the Portfolio project created in Project Creation.

Click the Portfolio item in Service Account and click the [+ Add] button to create a Service Account.

You can see the YAML specification as it is in the create_provider.yaml file.

Add the Service Account for the example developed, entering the name and asset as in the YAML specification. Fill in the rest of the information.

The name (name) is a default value.
The asset is the value defined in template > service_account > schema > properties > amount in create_provider.yaml.
Select the Portfolio project group in the project.


Service Account must be specified for at least 1 project to be created.
Click [Add] to create the Investment Service Account.

The Investment Service Account is created correctly.



6. Plugin Registration 
Registering an Inventory plugin allows you to view the data collected by the plugin in SpaceONE. At this time, you use the Collector resource.

1) Collector Resource Check 
Currently, there is no collector (Collector) registered in the provider of Local Repository.


spacectl list inventory.Collector
restart ↺
NO DATA

1-1) If you check in the console UI, you can see that there is no collector.

1-2) If you click the Create Collector, you can see that there is no collector in the ‘Investment’ provider that you registered in Local Repository.



2) setup.py Writing 
2-1) Create a VERSION file.


echo 0.0.1 >> src/VERSION
restart ↺
2-2) Write a Python package list for plugin execution.

vi pkg/pip_requirements.txt
restart ↺
pkg/pip_requirements.txt
spaceone-api
pre-commit
pycoingecko
grpcio

2-3) Write setup.py file.

#
#   Copyright 2020 The SpaceONE Authors.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from setuptools import find_packages, setup

with open("VERSION", "r") as f:
    VERSION = f.read().strip()
    f.close()

setup(
    name="plugin-portfolio-inven-collector",
    version=VERSION,
    description="SpaceONE Portfolio Inventory Collector Plugin",
    long_description="",
    url="https://www.spaceone.dev/",
    author="MEGAZONE SpaceONE Team",
    author_email="admin@spaceone.dev",
    license="Apache License 2.0",
    packages=find_packages(),
    install_requires=[
        "spaceone-api",
        "pycoingecko",
    ],
    package_data={
        "plugin": ["metadata/**/*.yaml"],
    },
    zip_safe=False,
)

3) Dockerfile Writing and Image Building 
First, you need to build an image using Dockerfile to register the plugin.

3-1) Write Dockerfile.

Dockerfile
FROM cloudforet/python-core:2.0

ENV PYTHONUNBUFFERED 1
ENV SPACEONE_PORT 50051
ENV SERVER_TYPE grpc
ENV PKG_DIR /tmp/pkg
ENV SRC_DIR /tmp/src

RUN apt update && apt upgrade -y

COPY pkg/*.txt ${PKG_DIR}/

RUN pip install --upgrade pip && \
    pip install --upgrade -r ${PKG_DIR}/pip_requirements.txt && \
    pip install --upgrade --pre spaceone-inventory

COPY src ${SRC_DIR}
WORKDIR ${SRC_DIR}
RUN python3 setup.py install && rm -rf /tmp/*

EXPOSE ${SPACEONE_PORT}

ENTRYPOINT ["spaceone"]
CMD ["run", "plugin-server", "plugin"]

3-2) Build an image. Enter your Docker Hub ID in quasarhub.


docker build -t quasarhub/plugin-portfolio-inven-collector:0.0.1 .
restart ↺

3-3) Check the image to see if it is built correctly.


docker images
restart ↺
REPOSITORY                                                       TAG       IMAGE ID       CREATED         SIZE
quasarhub/plugin-portfolio-inven-collector                           0.0.1     4a0d97d31d80   1 minutes ago   956MB

3-4) If you input docker run, you can see that it outputs as follows, indicating normal operation.


docker run quasarhub/plugin-portfolio-inven-collector:0.0.1
restart ↺
...

2024-07-25T17:31:01.154Z [DEBUG]       (server.py:69) Loaded Services:
	 - spaceone.api.inventory.plugin.Collector
	 - spaceone.api.inventory.plugin.Job
	 - grpc.health.v1.Health
	 - spaceone.api.core.v1.ServerInfo
2024-07-25T17:31:01.155Z [INFO]       (server.py:73) Start gRPC Server (plugin): port=50051, max_workers=100

3-5) If you follow the guide correctly, the final directory structure is as follows.

4) Push Image to Docker Hub Registry 
4-1) Enter your Docker Hub Username and Password.


docker login
Username:
Password:
restart ↺
4-2) If you push the image, you can see that the image is uploaded correctly to Docker Hub.


docker push quasarhub/plugin-portfolio-inven-collector:0.0.1
restart ↺


5) Registered Plugin Check 
If you check the current registered plugin, you can see that it is as follows. All of these are plugins provided by SpaceONE by default. Now, let’s register the plugin developed in the example.


spacectl list repository.Plugin --minimal
restart ↺
 plugin_id                                | name                                      | image                                               | state   | service_type             | registry_type   | provider
------------------------------------------+-------------------------------------------+-----------------------------------------------------+---------+--------------------------+-----------------+--------------
 plugin-api-direct-mon-webhook            | API Direct                                | spaceone/plugin-api-direct-mon-webhook              | ENABLED | monitoring.Webhook       | DOCKER_HUB      |
 plugin-aws-cloud-service-inven-collector | AWS Cloud Service Collector               | spaceone/plugin-aws-cloud-service-inven-collector   | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-aws-cloudtrail-mon-datasource     | AWS CloudTail Log DataSource              | spaceone/plugin-aws-cloudtrail-mon-datasource       | ENABLED | monitoring.DataSource    | DOCKER_HUB      | aws
 plugin-aws-cloudwatch-mon-datasource     | AWS CloudWatch Metric DataSource          | spaceone/plugin-aws-cloudwatch-mon-datasource       | ENABLED | monitoring.DataSource    | DOCKER_HUB      | aws
 plugin-aws-cost-explorer-cost-datasource | AWS Cost Explorer Data Source             | spaceone/plugin-aws-cost-explorer-cost-datasource   | ENABLED | cost_analysis.DataSource | DOCKER_HUB      | aws
 plugin-aws-ec2-inven-collector           | AWS EC2 Collector                         | spaceone/plugin-aws-ec2-inven-collector             | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-aws-phd-inven-collector           | AWS Personal Health Dashboard Collector   | spaceone/plugin-aws-phd-inven-collector             | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-aws-sns-monitoring-webhook        | AWS SNS                                   | spaceone/plugin-aws-sns-mon-webhook                 | ENABLED | monitoring.Webhook       | DOCKER_HUB      | aws
 plugin-aws-ta-inven-collector            | AWS Trusted Advisor Collector             | spaceone/plugin-aws-trusted-advisor-inven-collector | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-azure-activity-log-mon-datasource | Azure Activity Log DataSource             | spaceone/plugin-azure-activity-log-mon-datasource   | ENABLED | monitoring.DataSource    | DOCKER_HUB      | azure
 plugin-azure-cost-mgmt-cost-datasource   | Azure Cost Management Data Source         | spaceone/plugin-azure-cost-mgmt-cost-datasource     | ENABLED | cost_analysis.DataSource | DOCKER_HUB      | azure
 plugin-azure-inven-collector             | Azure Collector                           | spaceone/plugin-azure-inven-collector               | ENABLED | inventory.Collector      | DOCKER_HUB      | azure
 plugin-azure-monitor-mon-datasource      | Azure Monitoring Metric DataSource        | spaceone/plugin-azure-monitor-mon-datasource        | ENABLED | monitoring.DataSource    | DOCKER_HUB      | azure
 plugin-email-noti-protocol               | Email Notification Protocol               | spaceone/plugin-email-noti-protocol                 | ENABLED | notification.Protocol    | DOCKER_HUB      | email
 plugin-google-cloud-inven-collector      | Google Cloud Collector                    | spaceone/plugin-google-cloud-inven-collector        | ENABLED | inventory.Collector      | DOCKER_HUB      | google_cloud
 plugin-google-cloud-log-mon-datasource   | Google Cloud Log DataSource               | spaceone/plugin-google-cloud-log-mon-datasource     | ENABLED | monitoring.DataSource    | DOCKER_HUB      | google_cloud
 plugin-google-monitoring-mon-webhook     | Google Cloud Monitoring                   | spaceone/plugin-google-monitoring-mon-webhook       | ENABLED | monitoring.Webhook       | DOCKER_HUB      | google_cloud
 plugin-google-stackdriver-mon-datasource | Google Cloud Monitoring Metric DataSource | spaceone/plugin-google-stackdriver-mon-datasource   | ENABLED | monitoring.DataSource    | DOCKER_HUB      | google_cloud
 plugin-grafana-mon-webhook               | Grafana                                   | spaceone/plugin-grafana-mon-webhook                 | ENABLED | monitoring.Webhook       | DOCKER_HUB      |
 plugin-keycloak-identity-auth            | Keycloak OIDC                             | spaceone/plugin-keycloak-identity-auth              | ENABLED | identity.Domain          | DOCKER_HUB      |
 plugin-ms-teams-noti-protocol            | MS Teams Notification Protocol            | spaceone/plugin-ms-teams-noti-protocol              | ENABLED | notification.Protocol    | DOCKER_HUB      | microsoft
 plugin-prometheus-mon-webhook            | Prometheus                                | spaceone/plugin-prometheus-mon-webhook              | ENABLED | monitoring.Webhook       | DOCKER_HUB      |
 plugin-slack-noti-protocol               | Slack Notification Protocol               | spaceone/plugin-slack-noti-protocol                 | ENABLED | notification.Protocol    | DOCKER_HUB      | slack
 plugin-telegram-noti-protocol            | Telegram Notification Protocol            | spaceone/plugin-telegram-noti-protocol              | ENABLED | notification.Protocol    | DOCKER_HUB      | telegram

 Count: 24 / 24

6) Plugin Registration 
5-1) Write a YAML specification for registering a plugin.

register_plugin.yaml
---
name: Portfolio Collector
provider: portfolio
service_type: inventory.Collector
registry_config: { }
registry_type: DOCKER_HUB
image: quasarhub/plugin-portfolio-inven-collector
capability:
  supported_schema:
    - portfolio_investment_schema
tags:
  description: Diversify and optimize your financial future with our comprehensive asset portfolio management.
  icon: https://visualpharm.com/assets/401/Rebalance%20Portfolio-595b40b75ba036ed117d88fd.svg
  long_description: This powerful plugin allows you to track and analyze various types of assets, including stocks, bonds, real estate, cryptocurrencies, and more.
labels:
  - Portfolio
  - Investment
template: { }

spacectl exec register repository.Plugin -f register_plugin.yaml
restart ↺
5-3) To check if the plugin is registered, use the following command. You can see that the plugin-portfolio-inven-collector plugin is registered.


spacectl list repository.Plugin --minimal
restart ↺
 plugin_id                                | name                                      | image                                               | state   | service_type             | registry_type   | provider
------------------------------------------+-------------------------------------------+-----------------------------------------------------+---------+--------------------------+-----------------+--------------
 plugin-api-direct-mon-webhook            | API Direct                                | spaceone/plugin-api-direct-mon-webhook              | ENABLED | monitoring.Webhook       | DOCKER_HUB      |
 plugin-aws-cloud-service-inven-collector | AWS Cloud Service Collector               | spaceone/plugin-aws-cloud-service-inven-collector   | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-aws-cloudtrail-mon-datasource     | AWS CloudTail Log DataSource              | spaceone/plugin-aws-cloudtrail-mon-datasource       | ENABLED | monitoring.DataSource    | DOCKER_HUB      | aws
 plugin-aws-cloudwatch-mon-datasource     | AWS CloudWatch Metric DataSource          | spaceone/plugin-aws-cloudwatch-mon-datasource       | ENABLED | monitoring.DataSource    | DOCKER_HUB      | aws
 plugin-aws-cost-explorer-cost-datasource | AWS Cost Explorer Data Source             | spaceone/plugin-aws-cost-explorer-cost-datasource   | ENABLED | cost_analysis.DataSource | DOCKER_HUB      | aws
 plugin-aws-ec2-inven-collector           | AWS EC2 Collector                         | spaceone/plugin-aws-ec2-inven-collector             | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-aws-phd-inven-collector           | AWS Personal Health Dashboard Collector   | spaceone/plugin-aws-phd-inven-collector             | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-aws-sns-monitoring-webhook        | AWS SNS                                   | spaceone/plugin-aws-sns-mon-webhook                 | ENABLED | monitoring.Webhook       | DOCKER_HUB      | aws
 plugin-aws-ta-inven-collector            | AWS Trusted Advisor Collector             | spaceone/plugin-aws-trusted-advisor-inven-collector | ENABLED | inventory.Collector      | DOCKER_HUB      | aws
 plugin-azure-activity-log-mon-datasource | Azure Activity Log DataSource             | spaceone/plugin-azure-activity-log-mon-datasource   | ENABLED | monitoring.DataSource    | DOCKER_HUB      | azure
 plugin-azure-cost-mgmt-cost-datasource   | Azure Cost Management Data Source         | spaceone/plugin-azure-cost-mgmt-cost-datasource     | ENABLED | cost_analysis.DataSource | DOCKER_HUB      | azure
 plugin-azure-inven-collector             | Azure Collector                           | spaceone/plugin-azure-inven-collector               | ENABLED | inventory.Collector      | DOCKER_HUB      | azure
 plugin-azure-monitor-mon-datasource      | Azure Monitoring Metric DataSource        | spaceone/plugin-azure-monitor-mon-datasource        | ENABLED | monitoring.DataSource    | DOCKER_HUB      | azure
 plugin-email-noti-protocol               | Email Notification Protocol               | spaceone/plugin-email-noti-protocol                 | ENABLED | notification.Protocol    | DOCKER_HUB      | email
 plugin-google-cloud-inven-collector      | Google Cloud Collector                    | spaceone/plugin-google-cloud-inven-collector        | ENABLED | inventory.Collector      | DOCKER_HUB      | google_cloud
 plugin-google-cloud-log-mon-datasource   | Google Cloud Log DataSource               | spaceone/plugin-google-cloud-log-mon-datasource     | ENABLED | monitoring.DataSource    | DOCKER_HUB      | google_cloud
 plugin-google-monitoring-mon-webhook     | Google Cloud Monitoring                   | spaceone/plugin-google-monitoring-mon-webhook       | ENABLED | monitoring.Webhook       | DOCKER_HUB      | google_cloud
 plugin-google-stackdriver-mon-datasource | Google Cloud Monitoring Metric DataSource | spaceone/plugin-google-stackdriver-mon-datasource   | ENABLED | monitoring.DataSource    | DOCKER_HUB      | google_cloud
 plugin-grafana-mon-webhook               | Grafana                                   | spaceone/plugin-grafana-mon-webhook                 | ENABLED | monitoring.Webhook       | DOCKER_HUB      |
 plugin-keycloak-identity-auth            | Keycloak OIDC                             | spaceone/plugin-keycloak-identity-auth              | ENABLED | identity.Domain          | DOCKER_HUB      |
 plugin-ms-teams-noti-protocol            | MS Teams Notification Protocol            | spaceone/plugin-ms-teams-noti-protocol              | ENABLED | notification.Protocol    | DOCKER_HUB      | microsoft
 plugin-prometheus-mon-webhook            | Prometheus                                | spaceone/plugin-prometheus-mon-webhook              | ENABLED | monitoring.Webhook       | DOCKER_HUB      |
 plugin-slack-noti-protocol               | Slack Notification Protocol               | spaceone/plugin-slack-noti-protocol                 | ENABLED | notification.Protocol    | DOCKER_HUB      | slack
 plugin-telegram-noti-protocol            | Telegram Notification Protocol            | spaceone/plugin-telegram-noti-protocol              | ENABLED | notification.Protocol    | DOCKER_HUB      | telegram
 plugin-portfolio-inven-collector         | Portfolio Collector                       | quasarhub/plugin-portfolio-inven-collector          | ENABLED | inventory.Collector      | DOCKER_HUB      | investment

 Count: 25 / 25

5-4) If you check in the console UI, you can see that the ‘Portfolio Collector’ is registered correctly. Click [Select].

5-5) Enter the name and click [Continue].

5-6) You can select all service accounts or only specific service accounts.

5-7) If you turn on automatic collection scheduling, the collector will automatically collect data at the time you want. Click [New Collector Creation] to collect data.



5-8) You can see that the plugin has been added to the cloud service as you specified in provider, cloud_service_group, and cloud_service_type.

5-9) Since you collected a total of 5 cryptocurrencies, the count is also 5. Click ‘Portfolio’ to see what cryptocurrencies are there.

5-10) If you click a specific cryptocurrency, you can see details, tags, etc. in the Details.

5-11) SpaceONE Dynamic UI Metadata representation result is as follows in Details.

Developing Inventory Plugin
