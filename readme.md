# AssemblyAI LeMUR CSV Processor

This repository contains a Streamlit application that processes a CSV file using AssemblyAI's LeMUR (Language Model Understanding and Reasoning) API. The application allows you to input your AssemblyAI API key, upload a CSV file, provide a custom prompt, and then process the CSV file using LeMUR. The processed results are then available for download as a new CSV file.

## Features

- Input your AssemblyAI API key for authentication
- Upload a CSV file containing transcript IDs
- Provide a custom prompt for LeMUR processing
- Process the CSV file using LeMUR API
- Download the processed results as a new CSV file

## Requirements

- Python 3.6 or higher
- Streamlit
- AssemblyAI Python SDK

## Installation

1. Clone the repository:

```
git clone https://github.com/your-username/assemblyai-lemur-csv-processor.git
```

2. Change into the project directory:

```
cd assemblyai-lemur-csv-processor
```

3. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:

```
streamlit run app.py
```

2. Open the application in your web browser using the provided URL.

3. Enter your AssemblyAI API key in the designated input field.

4. Upload a CSV file containing the transcript IDs you want to process. The CSV file should have a column named "transcriptid".

5. Provide a custom prompt for LeMUR processing in the text area. The prompt will be used to guide the LeMUR model in analyzing the transcripts.

6. Click the "Process CSV" button to start processing the CSV file using LeMUR.

7. Once the processing is complete, a success message will be displayed, and a "Download CSV File" link will appear.

8. Click on the "Download CSV File" link to download the processed results as a new CSV file. The downloaded file will contain the original columns from the input CSV, along with two new columns: "lemur_response" (containing the LeMUR response) and "number_occurred" (indicating the number of "yes" answers in the LeMUR response).

## Customization

You can customize the application by modifying the `app.py` file. The main components of the application are:

- `parse_json_from_resp`: Extracts the JSON array from the LeMUR response string.
- `count_yes`: Counts the number of "yes" answers in the LeMUR response.
- `process_row`: Processes a single row of the CSV file using LeMUR.
- `process_csv`: Processes the entire CSV file using multithreading.
- `download_csv`: Generates the download link for the processed CSV file.

Feel free to modify these functions to suit your specific requirements.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [AssemblyAI](https://www.assemblyai.com/) for providing the LeMUR API
- [Streamlit](https://streamlit.io/) for the web application framework