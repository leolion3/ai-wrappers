#!/usr/bin/env python3
"""
Open-Source Perplexity API Wrapper by Leonard Haddad, 2025.
Provided in accords with the MIT License.
More on GitHub at https://leolion.tk/
"""
import time
import requests
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

import setup # TODO replace with your config
import log_handler
from log_handler import Logger, Module

logger: Logger = log_handler.get_instance()


class PerplexityWrapper:
    """
    Implements a Perplexity-API wrapper.
    """

    @staticmethod
    def _estimate_cost(pplx_response: Dict[str, any]) -> Decimal:
        """
        Computes the estimated cost of a perplexity request.
        :param pplx_response: the perplexity response json dump.
        :return: the estimated cost of the perplexity request or 0 on error.
        Note: Since the cost also includes citations (excluded in the response)
              these are not taken into account.
        Note: Token cost is USD/Million Tokens, search cost is USD/Thousand Searches.
        #> See https://docs.perplexity.ai/guides/pricing
        """
        try:
            logger.debug('PPLX response dict:', pplx_response, module=Module.PPLX)
            input_tokens: int = int((pplx_response['usage'])['prompt_tokens'])
            output_tokens: int = int((pplx_response['usage'])['completion_tokens'])
            searches: int = len(pplx_response.get('citations', []))
            estimated_cost = (
                    Decimal(input_tokens) * Decimal(setup.INPUT_TOKEN_PRICE_PPM) / Decimal(10 ** 6) +
                    Decimal(output_tokens) * Decimal(setup.OUTPUT_TOKEN_PRICE_PPM) / Decimal(10 ** 6) +
                    Decimal(searches) * Decimal(setup.SEARCH_PRICE_PPK) / Decimal(10 ** 3)
            ).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            logger.debug('Estimated cost:', estimated_cost, '$ USD', module=Module.PPLX)
            return estimated_cost
        except Exception as e:
            logger.error('Error computing cost. Trace:', e, module=Module.PPLX)
            return Decimal(0)

    @staticmethod
    def _extract_citations(pplx_response: Dict[str, any]) -> List[str]:
        """
        Extracts the citations from the perplexity response.
        :param pplx_response: the perplexity response json dump.
        :return: the citations extracted from the perplexity response or an empty list on error.
        """
        citations: List[str] = pplx_response.get('citations', [])
        logger.debug('Extracted citations:', citations, module=Module.PPLX)
        return citations

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Builds the authorization headers.
        :return: the authorization headers.
        """
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _build_query(question: str, message_history: List[any]) -> List[Dict[str, str]]:
        """
        Builds the messages list for perplexity.
        :param question: the new message from the user.
        :param message_history: old messages to add context from.
        :return: the new message list, formatted for the LLM.
        """
        new_message_history: List[any] = [{
            "role": "user",
            "content": question
        }]
        for message in message_history:
            if 'role' not in message or 'content' not in message:
                continue
            new_message_history.append({
                "role": message['role'],
                "content": message['content']
            })
        return new_message_history

    def _parse_response(self, response: requests.Response) -> Tuple[str, List[str], Decimal]:
        """
        Parses the perplexity response.
        :param response: the perplexity response.
        :return: the parsed response.
        """
        try:
            response_data: Dict[str, any] = response.json()
            answer = response_data.get('choices')[0].get('message').get('content')
            cost: Decimal = self._estimate_cost(pplx_response=response_data)
            citations: List[str] = self._extract_citations(pplx_response=response_data)
            return answer, citations, cost
        except Exception as e:
            logger.error('Error parsing perplexity response. Trace:', e, module=Module.PPLX)
            raise

    def query_perplexity(
            self,
            question: str,
            message_history: List[any],
            retries=0
    ) -> Tuple[str, List[str], Decimal]:
        """
        Queries the perplexity api.
        :param question: The question to ask.
        :param message_history: old messages to add context from.
        :param retries: The number of retries to perform.
        :return: A triple of text-answer, list of citations and request costs.
        :raise Exception: if the request fails after retrying too many times.
        """
        headers = self._get_auth_headers()
        data = {
            "model": self._llm_model,
            "messages": self._build_query(question=question, message_history=message_history),
        }

        response = requests.post(setup.API_URL, headers=headers, json=data)
        if response.status_code != 200:
            if retries < 3:
                logger.error(f'Request to Perplexity failed, retrying {retries + 1}/3...', module=Module.PPLX)
                time.sleep(1)
                return self.query_perplexity(question, message_history, retries + 1)
            logger.error('Request to Perplexity failed after 3 retries.', module=Module.PPLX)
            raise Exception(f'Request failed with status code {response.status_code}.')
        return self._parse_response(response)

    def __init__(self):
        """
        Default constructor.
        """
        try:
            logger.info('Starting Perplexity API wrapper...', module=Module.PPLX)
            # TODO Loads vars as you want
            self._api_key: str = setup.PPLX_API_KEY
            self._api_url: str = setup.API_URL
            self._llm_model: str = setup.PPLX_MODEL
            self._inp_cost_ppm: int = setup.INPUT_TOKEN_PRICE_PPM
            self._out_cost_ppm: int = setup.OUTPUT_TOKEN_PRICE_PPM
            self._web_search_cost_ppk: int = setup.SEARCH_PRICE_PPK
            logger.info('Perplexity API wrapper initialized.', module=Module.PPLX)
        except Exception as e:
            logger.error('Error initializing Perplexity API wrapper. Trace:', e, module=Module.PPLX)
            exit(-1)


pplx_wrapper: PerplexityWrapper = PerplexityWrapper()
