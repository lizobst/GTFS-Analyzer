import anthropic
import pandas as pd
import json

import anthropic
import pandas as pd
import json


class GTFSChatbot:
    def __init__(self, api_key, gtfs_data, route_frequencies=None, trips_by_hour=None):
        """
        Initialize the chatbot with GTFS data context

        Args:
            api_key: Your Anthropic API key
            gtfs_data: Dictionary of GTFS dataframes
            route_frequencies: DataFrame from calculate_route_frequencies()
            trips_by_hour: DataFrame from calculate_trips_by_hour()
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.gtfs_data = gtfs_data
        self.route_frequencies = route_frequencies
        self.trips_by_hour = trips_by_hour

    def create_system_prompt(self):
        """Build the system prompt describing available data"""

        # Get sample data and column info
        stops_info = f"Columns: {self.gtfs_data['stops'].columns.tolist()}\nSample: {self.gtfs_data['stops'].head(2).to_dict('records')}"
        routes_info = f"Columns: {self.gtfs_data['routes'].columns.tolist()}\nSample: {self.gtfs_data['routes'].head(2).to_dict('records')}"

        freq_info = ""
        if self.route_frequencies is not None:
            freq_info = f"\n\nroute_frequencies DataFrame:\nColumns: {self.route_frequencies.columns.tolist()}\nSample: {self.route_frequencies.head(2).to_dict('records')}"

        prompt = f"""You are analyzing GTFS (General Transit Feed Specification) transit data.

Available data structures:

**gtfs_data['stops']** - Transit stop information
{stops_info}

**gtfs_data['routes']** - Transit route information  
{routes_info}

**gtfs_data['trips']** - Trip information
Columns: {self.gtfs_data['trips'].columns.tolist()}

**gtfs_data['stop_times']** - Stop times for each trip
Columns: {self.gtfs_data['stop_times'].columns.tolist()}
{freq_info}

When the user asks a question about the transit data:
1. Write Python pandas code to answer it
2. Use the variable names exactly as shown above (gtfs_data['stops'], route_frequencies, etc.)
3. Return ONLY the Python code, no explanations, no markdown formatting, no ```python blocks
4. The code should assign the result to a variable called 'result'
5. Make sure the result can be printed (convert to string/number if needed)

Example:
User: "How many stops are there?"
Your response: result = len(gtfs_data['stops'])

User: "What's the busiest route?"
Your response: result = route_frequencies.nsmallest(1, 'avg_headway_min')[['route_short_name', 'avg_headway_min']].to_dict('records')[0]
"""
        return prompt

    def ask(self, question):
        """
        Ask a question and get a response

        Args:
            question: Natural language question about the transit data

        Returns:
            Dictionary with 'code', 'result', and 'answer' keys
        """
        try:
            # Get code from Claude
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=self.create_system_prompt(),
                messages=[
                    {"role": "user", "content": question}
                ]
            )

            generated_code = message.content[0].text.strip()

            # Execute the code safely
            local_vars = {
                'gtfs_data': self.gtfs_data,
                'route_frequencies': self.route_frequencies,
                'trips_by_hour': self.trips_by_hour,
                'pd': pd,
                'result': None
            }

            exec(generated_code, {"__builtins__": __builtins__}, local_vars)
            result = local_vars['result']

            # Format the result nicely
            if isinstance(result, pd.DataFrame):
                answer = result.to_string()
            elif isinstance(result, dict):
                answer = json.dumps(result, indent=2)
            else:
                answer = str(result)

            return {
                'code': generated_code,
                'result': result,
                'answer': answer,
                'success': True
            }

        except Exception as e:
            return {
                'code': generated_code if 'generated_code' in locals() else None,
                'result': None,
                'answer': f"Error: {str(e)}",
                'success': False
            }