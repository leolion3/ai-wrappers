# Perplexity AI API Wrapper

This module implements an API Wrapper for the Perplexity AI API.

## Requirements

The module requires only the `requests` module

```bash
pip install requests
```

## Logging

As with all modules in this repo, the logging module used can be found [here](https://github.com/leolion3/Portfolio/tree/master/Python/Logger).

To add the Perplexity module logs, add the following Key-Value pair to the `Logger.Module` enum mapping:

```python
PPLX = 'Perplexity'
```

## Configuration

This module requires the following parameters to be set, either in a setup or a `.env` file:

```bash
PPLX_API_KEY="your pplx api key"
API_URL="API URL, should be set to `https://api.perplexity.ai/chat/completions` by default"
PPLX_MODEL="Model to use, current models are `sonar` and `sonar-pro`"
# For pricing, see https://docs.perplexity.ai/guides/pricing
INPUT_TOKEN_PRICE_PPM=3    # 3$  / 1 Million for sonar pro, 1.5 for sonar
OUTPUT_TOKEN_PRICE_PPM=15  # 15$ / 1 Million for sonar pro, 5$ for sonar
SEARCH_PRICE_PPK=5         # 5$  / 1000 requests, default
```

## Usage

To use the module, simply import the `pplx_wrapper` and call `query_perplexity` to query the Perplexity API.

```python3
import perplexity_wrapper
from perplexity_wrapper import PerplexityWrapper

pplx_wrapper: PerplexityWrapper = perplexity_wrapper.pplx_wrapper
response: Tuple[str, List[str], Decimal] = pplx_wrapper.query_perplexity(
		'question': 'Hello, how are you?',
		# Note: as usual, the messages are in reverse oder - the latest message is the first element.
		'message_history': [
			{
				'role': 'user/assistant',
				'content': 'message content'
			}, ...
		]
	)
answer, sources, estimated_cost = response
print(answer)
```

The method returns a triple:

- The first element is the model's textual response.
- The second element are the sources cited through web-search.
- The third element is the estimated cost and is computed based on the `_inp_cost_ppm`, `_out_cost_ppm` and `_web_search_cost_ppk` variables.
