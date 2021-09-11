
create-queue:
	aws sqs create-queue --endpoint-url=http://localhost:4566 --queue-name calculation-completed
	aws sqs create-queue --endpoint-url=http://localhost:4566 --queue-name calculation-completed-dlq