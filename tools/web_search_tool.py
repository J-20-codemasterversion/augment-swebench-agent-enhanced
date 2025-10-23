"""Web search tool for the agent using DuckDuckGo API and GPT-5 analysis."""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from duckduckgo_search import DDGS
from utils.common import DialogMessages, LLMTool, ToolImplOutput
from utils.llm_client import get_client

logger = logging.getLogger(__name__)


class WebSearchTool(LLMTool):
    """A tool for searching the web using DuckDuckGo API and GPT-5 analysis."""

    name = "web_search"
    description = "Search the web for current information using DuckDuckGo and analyze with GPT-5."
    
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."},
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "default": 5,
                "description": "Maximum number of results to return.",
            },
        },
        "required": ["query"],
    }

    def __init__(self, use_gpt5: bool = True):
        super().__init__()
        self.use_gpt5 = use_gpt5
        self.ddgs = DDGS()
        # Rate limiting: max 1 request per 2 seconds to avoid rate limits
        self.last_search_time = 0
        self.min_search_interval = 2.0
        
        if use_gpt5:
            self.client = get_client("openai-direct", model_name="gpt-5", cot_model=True)

    def run_impl(
        self,
        tool_input: Dict[str, Any],
        dialog_messages: Optional[DialogMessages] = None,
    ) -> ToolImplOutput:
        query = tool_input["query"]
        max_results = tool_input.get("max_results", 5)

        logger.info(f"Performing web search: '{query}'")

        try:
            # Step 1: Perform real web search using DuckDuckGo
            search_results = self._perform_duckduckgo_search(query, max_results * 2)  # Get more results for GPT-5 to choose from
            
            if not search_results:
                return ToolImplOutput(
                    tool_output="No search results found.",
                    tool_result_message=f"No results found for '{query}'",
                    auxiliary_data={"success": False, "num_results": 0},
                )
            
            # Step 2: Use GPT-5 to analyze and find the most relevant information
            if self.use_gpt5:
                analyzed_results = self._analyze_with_gpt5(query, search_results, max_results)
                search_engine = "DuckDuckGo + GPT-5"
            else:
                analyzed_results = search_results[:max_results]
                search_engine = "DuckDuckGo"
            
            formatted_output = self._format_results(query, analyzed_results)
            
            return ToolImplOutput(
                tool_output=formatted_output,
                tool_result_message=f"Web search completed for '{query}' using {search_engine}",
                auxiliary_data={"success": True, "num_results": len(analyzed_results), "search_engine": search_engine},
            )
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return ToolImplOutput(
                tool_output=f"Error performing web search: {str(e)}",
                tool_result_message=f"Web search failed for '{query}'",
                auxiliary_data={"success": False, "error": str(e)},
            )

    def _perform_duckduckgo_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform real web search using DuckDuckGo API."""
        try:
            # Rate limiting: ensure we don't make requests too frequently
            current_time = time.time()
            time_since_last_search = current_time - self.last_search_time
            if time_since_last_search < self.min_search_interval:
                sleep_time = self.min_search_interval - time_since_last_search
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Perform the actual search
            logger.info(f"Searching DuckDuckGo for: {query}")
            search_results = self.ddgs.text(query, max_results=max_results)
            
            # Update last search time
            self.last_search_time = time.time()
            
            # Convert DuckDuckGo results to our format
            results = []
            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "relevance": 1.0  # DuckDuckGo doesn't provide relevance scores
                })
            
            logger.info(f"Found {len(results)} search results from DuckDuckGo")
            return results
            
        except Exception as e:
            logger.error(f"Error in DuckDuckGo search: {e}")
            # If we get rate limited, provide a helpful message
            if "Ratelimit" in str(e) or "rate limit" in str(e).lower():
                raise Exception("DuckDuckGo rate limit reached. Please wait a moment before searching again.")
            raise e

    def _analyze_with_gpt5(self, query: str, search_results: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        """Use GPT-5 to analyze search results and find the most relevant information."""
        try:
            analysis_prompt = f"""
            You are analyzing real web search results to find the most relevant information for this query: "{query}"
            
            Here are the actual search results from DuckDuckGo:
            {json.dumps(search_results, indent=2)}
            
            Please analyze these results and return the {max_results} most relevant ones in this JSON format:
            [
                {{
                    "title": "Title of the most relevant result",
                    "url": "https://actual-url.com",
                    "snippet": "Summary of the most important information from this source",
                    "relevance": 0.95,
                    "key_insights": ["Key insight 1", "Key insight 2"],
                    "source_type": "documentation|tutorial|github|stackoverflow|news|official"
                }}
            ]
            
            Focus on:
            1. Accuracy and relevance to the query
            2. Most current and useful information
            3. Official sources when available
            4. Actionable insights and facts
            
            Return only the JSON array, no other text.
            """
            
            logger.info("GPT-5 analyzing search results...")
            response = self.client.generate(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse GPT-5's analysis
            try:
                analyzed_results = json.loads(response.content)
                if isinstance(analyzed_results, list) and len(analyzed_results) > 0:
                    logger.info(f"GPT-5 analyzed and selected {len(analyzed_results)} most relevant results")
                    return analyzed_results[:max_results]
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse GPT-5 analysis as JSON: {e}")
            
            # Fallback: return original results if GPT-5 analysis fails
            logger.info("Falling back to original search results")
            return search_results[:max_results]
            
        except Exception as e:
            logger.error(f"GPT-5 analysis failed: {e}")
            # Fallback to original results
            return search_results[:max_results]

    def _format_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Format search results into a readable string."""
        if not results:
            return f"No results found for: '{query}'"

        formatted_output = f"Web search results for: '{query}'\n\n"
        for i, result in enumerate(results, 1):
            formatted_output += f"{i}. {result['title']}\n"
            formatted_output += f"   URL: {result['url']}\n"
            formatted_output += f"   Snippet: {result['snippet']}\n"
            if 'relevance' in result:
                formatted_output += f"   Relevance: {result['relevance']}\n"
            if 'key_insights' in result and result['key_insights']:
                formatted_output += f"   Key Insights: {', '.join(result['key_insights'])}\n"
            if 'source_type' in result:
                formatted_output += f"   Source Type: {result['source_type']}\n"
            formatted_output += "\n"
        
        return formatted_output

    def get_tool_start_message(self, tool_input: Dict[str, Any]) -> str:
        query = tool_input["query"]
        search_engine = "DuckDuckGo + GPT-5" if self.use_gpt5 else "DuckDuckGo"
        return f"Searching the web for '{query}' using {search_engine}"


def create_web_search_tool(use_gpt5: bool = True) -> WebSearchTool:
    """Create a web search tool instance."""
    return WebSearchTool(use_gpt5=use_gpt5)