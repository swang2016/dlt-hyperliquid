import dlt
from dlt.destinations import postgres
from hyperliquid import hyperliquid_source
import os
from dotenv import load_dotenv


def load_hyperliquid() -> None:
    # Load environment variables from .env file
    load_dotenv()

    # DUCKDB pipeline
    pipeline = dlt.pipeline(
        pipeline_name="funding_rates",
        destination='duckdb',
        dataset_name="hyperliquid",
    )

    # POSTGRES pipeline
    # db = postgres(
    #     credentials=(
    #         f"postgresql://"
    #         f"{os.getenv('POSTGRES_USER')}:"
    #         f"{os.getenv('POSTGRES_PASSWORD')}@"
    #         f"{os.getenv('POSTGRES_HOST')}:"
    #         f"{os.getenv('POSTGRES_PORT')}/"
    #         f"{os.getenv('POSTGRES_DATABASE')}"
    #     )
    # )
    # pipeline = dlt.pipeline(
    #     pipeline_name="funding_rates",
    #     destination=db,
    #     dataset_name="hyperliquid",
    # )

    load_info = pipeline.run(hyperliquid_source())
    print(load_info)  # noqa: T201


if __name__ == "__main__":
    load_hyperliquid()
