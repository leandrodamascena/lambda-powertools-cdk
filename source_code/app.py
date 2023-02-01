import random
from time import gmtime, strftime
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()
metrics = Metrics()

@app.get("/hello")
@tracer.capture_method
def hello():

    random_number = random.randint(1,4)
    # adding custom metrics
    metrics.add_metric(name="HelloWorldInvocations", unit=MetricUnit.Count, value=1)

    # adding subgements, annotations and metadata
    with tracer.provider.in_subsegment("## random_number") as subsegment:
        subsegment.put_annotation(key="RandomNumber", value=random_number)
        subsegment.put_metadata(key="date", value=strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    # Emulating an HTTP code response based on a random number.
    if random_number < 9:
        # structured log
        logger.info("INFO LOG - The service is healthy - HTTP 200")
        return {"status": "healthy"}, 200
    else:
        # structured log
        logger.error("ERROR LOG - The service is unhealthy - HTTP 500")
        return {"status": "unhealthy"}, 500

# lambda_handler
# Logging Lambda invocation
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
# Adding tracer
@tracer.capture_lambda_handler
# ensures metrics are flushed upon request completion/failure and capturing ColdStart metric
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
