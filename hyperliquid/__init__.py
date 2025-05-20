import logging
from datetime import datetime
from typing import Any, Dict, Generator, Iterable, List, Optional
import time
from dataclasses import dataclass

import dlt
from dlt.sources import DltResource
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Constants
ASSETS = ["BTC", "ETH", "HYPE", "SOL", "DOGE", "FARTCOIN"]
START_TIME = 1683849600047
API_URL = "https://api.hyperliquid.xyz/info"

@dataclass
class FundingHistoryResponse:
    """Data class for funding history response."""
    data: List[Dict[str, Any]]
    last_time: int

@dlt.source
def hyperliquid_source() -> Iterable[DltResource]:
    """
    DLT source for Hyperliquid funding history data.
    
    Returns:
        Iterable[DltResource]: A generator of DLT resources for each asset.
    """
    
    def hyperliquid_resource(
        asset: str,
        cursor = dlt.sources.incremental("time", initial_value=START_TIME)
    ) -> Generator[Dict[Any, Any], Any, None]:
        """
        Generator function for fetching funding history data for a specific asset.
        """
        
        logging.info(f"Asset: {asset}, Cursor: {cursor.last_value}")
        response = get_data(asset, cursor.last_value + 1)
        if len(response.data) == 0:
            logging.info(f"No data available for asset {asset}, cursor: {cursor.last_value}")
            return
        yield response.data
        while True:
            logging.info(f"Getting data for asset: {asset}, cursor: {cursor.last_value}")
            try:
                response = get_data(asset, cursor.last_value + 1)
                if len(response.data) == 0:
                    logging.info(f"No more data available for asset {asset}, cursor: {cursor.last_value}")
                    break
                yield response.data
            except RequestException as e:
                logging.error(f"Error fetching data for asset {asset}: {str(e)}")
                raise


    for asset in ASSETS:
        asset_name = asset.lower() + "_usd"
        yield dlt.resource(
            hyperliquid_resource,
            name=asset_name,
            write_disposition="merge",
            primary_key="time",
        )(asset)


def get_data(asset: str, cursor: int) -> FundingHistoryResponse:
    """
    Fetch funding history data from Hyperliquid API.
    
    Args:
        asset: The asset symbol to fetch data for.
        cursor: The timestamp to start fetching from.
        
    Returns:
        FundingHistoryResponse: The API response containing funding history data.
        
    Raises:
        RequestException: If the API request fails.
    """
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "type": "fundingHistory",
        "coin": asset,
        "startTime": cursor,
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        results = response.json()
        if not results:
            return FundingHistoryResponse(data=[], last_time=cursor)
        
        # Add timestamp and paired coin fields (convert time to datetime)
        for result in results:
            result["timestamp"] = datetime.fromtimestamp(result["time"] / 1000)
            result["paired_coin"] = "USD"
            
        return FundingHistoryResponse(
            data=results,
            last_time=results[-1]["time"]
        )
        
    except requests.exceptions.Timeout as e:
        raise RequestException(f"Request timed out for asset {asset}") from e
    except requests.exceptions.HTTPError as e:
        raise RequestException(
            f"HTTP error occurred for asset {asset} at cursor {cursor}. "
            f"Status code: {e.response.status_code}. Error: {str(e)}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise RequestException(f"Request failed for asset {asset}: {str(e)}") from e