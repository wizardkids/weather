# Weather CLI

This Python script is a command-line interface (CLI) tool that allows you to retrieve current weather information for a specified location. It uses the OpenWeatherMap API to fetch weather data and displays it in a user-friendly format.

## Prerequisites

Before running this script, you need to have the following:

- Python 3.x installed on your system
- An API key from OpenWeatherMap (you can sign up for a free account at https://openweathermap.org/api)

## Installation

1. Clone or download this repository to your local machine.
2. Navigate to the `python cli/weather` directory.
3. Install the required Python packages by running the following command:

pip install -r requirements.txt

## Usage

To use the Weather CLI, run the following command:

python weather.py [OPTIONS] [LOCATION]


Replace `[LOCATION]` with the name of the city or the ZIP code for which you want to retrieve weather information.

### Options

- `--units` (default: `metric`): Specify the units for temperature. Accepted values are `metric` (Celsius) or `imperial` (Fahrenheit).
- `--api-key`: Provide your OpenWeatherMap API key. If not specified, the script will look for the `OWM_API_KEY` environment variable.

### Examples

- Get the current weather for New York City:

python weather.py "New York City"


- Get the current weather for ZIP code 90001 in Fahrenheit units:

python weather.py --units imperial 90001


- Use your OpenWeatherMap API key:

python weather.py --api-key YOUR_API_KEY_HERE "London"


## Acknowledgments

This project uses the [OpenWeatherMap API](https://openweathermap.org/api) to retrieve weather data.