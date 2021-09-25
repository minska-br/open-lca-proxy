#!/bin/bash

awslocal sqs create-queue --endpoint-url=http://localstack:4566 --queue-name calculation-completed
awslocal sqs create-queue --endpoint-url=http://localstack:4566 --queue-name calculation-completed-dlq