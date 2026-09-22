from utils.config_loader import logger
from errors.retryable import *
from errors.unretryable import *
import functools
import time
import requests
import json

def retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        last_error = None

        for i in range(3):
            try:
                logger.info(f"running {func.__name__}, attempt {i+1} of 3")
                return func(*args, **kwargs)

            except RetryableError as e:
                last_error = str(e)
                logger.error(f"Error caused: {last_error}")
                sleep_time = 0.3 * (2 ** i)
                logger.info(f"retrying {func.__name__}, (attempt {i+1} of 3)")
                time.sleep(sleep_time)
                continue

        logger.error(f"failed {func.__name__}")
        raise RetriesExhaustedError(f"{func.__name__} failed after 3 attempts",
                                    context = {"last_error": str(last_error), "attempts": 3})
    return wrapper


def safe_api_call(func):
    """
    Wraps Alpaca API calls:
    - catches ALL exceptions
    - classifies them
    - translates them into your hierarchy
    - logs them
    - re-raises clean exceptions
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            response = func(self, *args, **kwargs)

        except requests.exceptions.Timeout:
            raise NetworkError("Network timeout during Alpaca request.")

        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection error while contacting Alpaca.")

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code

            if status == 401:
                raise AuthenticationError("Invalid Alpaca API credentials.")
            elif status == 403:
                raise AccountError("Account restricted or insufficient permissions.")
            elif status == 429:
                raise RateLimitError("Rate limit exceeded.")
            elif 500 <= status < 600:
                raise ServerError(f"Alpaca server error {status}.")
            else:
                raise UnretryableError(f"Unexpected HTTP error {status}.")

        except json.JSONDecodeError:
            raise DataError("Malformed JSON from Alpaca.")

        except Exception as e:
            raise UnretryableError(f"Unexpected error: {str(e)}")

        # Validate response structure
        if response is None:
            raise DataError("Empty response from Alpaca.")


        logger.info("safe_api_call finished")
        return response

    return wrapper