from pydantic import BaseModel, Field
from langchain_core.tools import tool, StructuredTool
from src.retrieval.vector_store import top_k_search
import requests
from langchain_community.tools import DuckDuckGoSearchRun
from datetime import datetime

POLICY_METADATA = {
    "HR Policy _ KESPL.pdf": {
        "version": "v2.1",
        "effective_date": "2025-01-01",
    },
    "Work From Home Policy": {
        "version": "v1.3",
        "effective_date": "2024-06-15",
    },
    "Travel & Expense Policy": {
        "version": "v3.0",
        "effective_date": "2025-04-01",
    },
}


class DocumentSearchInput(BaseModel):
    query: str = Field(
        ..., description="The user's question or search phrase, in plain text."
    )


class DocumentMetadataInput(BaseModel):
    chunk_id: str = Field(
        ...,
        description="The exact Chunk ID string returned by a previous document_search call.",
    )


class AdditionInput(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number.")


class WeatherInput(BaseModel):
    city: str = Field(
        ..., description="The city name to get current for , e.g. 'Mumbai'."
    )


class DateTimeInput(BaseModel):
    pass


def build_tools(vector_store):
    def document_search(query: str) -> str:
        """Search the uploaded documents for this user and domain, and
        return relevant information with source and page citations."""
        results = top_k_search(vector_store, query)
        if not results:
            return "NO_RELEVANT_CHUNKS_FOUND"

        formatted = []
        for doc in results:
            meta = doc.metadata
            formatted.append(
                f"[Source: {meta.get('source')} | "
                f"Page: {meta.get('page_number')} | "
                f"Chunk ID: {meta.get('chunk_id')}]\n"
                f"{doc.page_content}"
            )
        return "\n\n---\n\n".join(formatted)

    def document_metadata(chunk_id: str) -> str:
        """
        Retrieve metadata for a document chunk: source, page, chunking
        strategy, and (if tracked) policy version and effective date.
        Use this only when the user asks about document version, effective
        date, origin, or details about a previously retrieved chunk.
        """
        collection = vector_store.get(
            where={"chunk_id": chunk_id}, include=["metadatas"]
        )
        metadatas = collection.get("metadatas", [])

        if not metadatas:
            return f"No metadata found for chunk_id '{chunk_id}'."

        meta = metadatas[0]
        source = meta.get("source", "unknown")
        page_number = meta.get("page_number", "unknown")
        strategy = meta.get("strategy", "unknown")
        stored_chunk_id = meta.get("chunk_id", chunk_id)

        extra = POLICY_METADATA.get(source, {})
        version = extra.get("version", "not tracked")
        effective_date = extra.get("effective_date", "not tracked")

        return (
            f"Source: {source}\n"
            f"Page: {page_number}\n"
            f"Chunk ID: {stored_chunk_id}\n"
            f"Chunking strategy: {strategy}\n"
            f"Version: {version}\n"
            f"Effective date: {effective_date}"
        )

    def add_numbers(a: float, b: float) -> str:
        """Add two numbers together. Use this for any simple addition question."""
        result = a + b
        return f"The sum of {a} and {b} is {result}."

    def get_current_weather(city: str) -> str:
        """Fetches the current weather for a given city using a free public API."""
        try:
            geo_response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
                timeout=5,
            )

            geo_data = geo_response.json()

            if not geo_data.get("results"):
                return f"Could not find location data for '{city}'."

            location = geo_data["results"][0]
            lat, lon = location["latitude"], location["longitude"]

            weather_response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": lat, "longitude": lon, "current_weather": True},
                timeout=5,
            )

            weather_data = weather_response.json()
            current = weather_data.get("current_weather", {})

            return (
                f"Current weather in {city}:" f"{current.get('temperature')}°C",
                f"windspeed {current.get('windspeed')}km/h. ",
            )
        except requests.RequestException as e:
            return f"Failed to fetch weather data:{str(e)}"

    def get_current_datetime() -> str:
        """Returns the current date and time, Use this when the user asks what today's date is or what time it is."""
        now = datetime.now()
        return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    search_tool = StructuredTool.from_function(
        func=document_search,
        name="document_search",
        description="Searches the user's uploaded documents for this domain. Use for any content question.",
        args_schema=DocumentSearchInput,
    )
    metadata_tool = StructuredTool.from_function(
        func=document_metadata,
        name="document_metadata",
        description="Retrieves metadata about a specific chunk (source, page, version, effective date). Use only for version/origin questions.",
        args_schema=DocumentMetadataInput,
    )

    addition_tool = StructuredTool.from_function(
        func=add_numbers,
        name="add_numbers",
        description="Adds two numbers together. Use ONLY for simple arithmetic additon , never for policy content questions.",
        args_schema=AdditionInput,
    )

    weather_tool = StructuredTool.from_function(
        func=get_current_weather,
        name="get_current_weather",
        description="Fetches real-time current weather for a city. Use ONLY when the user explicitly asks about weather, never for HR policy questions.",
        args_schema=WeatherInput,
    )

    datetime_tool = StructuredTool.from_function(
        func=get_current_datetime,
        name="get_current_datetime",
        description="Returns today's date and current time. Use ONLY when explicitly asked about the current date/time.",
        args_schema=DateTimeInput,
    )
    
    duckduckgo_search_tool = DuckDuckGoSearchRun(
        name="web_search",
        description="Searches the web for general knowledge questions Not covered in the uploaded documents. ",
    )

    return [
        search_tool,
        metadata_tool,
        addition_tool,
        weather_tool,
        duckduckgo_search_tool,
        datetime_tool,
    ]
