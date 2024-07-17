import streamlit as st
import csv
import json
import base64
import io
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def parse_json_from_resp(response_string):
    start_index = response_string.find('[')
    end_index = response_string.rfind(']') + 1
    json_array_string = response_string[start_index:end_index]
    try:
        response_json = json.loads(json_array_string)
        return response_json
    except:
        return []

def count_yes(arr):
    points = sum(1 for n in arr if n['answer'] == 'yes')
    return points

def make_lemur_request(transcript_id, prompt, api_key):
    url = "https://api.assemblyai.com/lemur/v3/generate/task"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "transcript_ids": [transcript_id]
    }
    response = requests.post(url, headers=headers, json=data)
    return response

def process_row(row, prompt, api_key):
    transcript_id = row['transcriptid']

    try:
        response = make_lemur_request(transcript_id, prompt, api_key)
        response.raise_for_status()
        result = response.json()
        row['lemur_response'] = result['response']
        negative_questions = parse_json_from_resp(result['response'])
    except:
        row['lemur_response'] = 'LeMUR Request Failed'
        negative_questions = []

    number_occurred = count_yes(negative_questions)
    row['number_occurred'] = number_occurred
    return row, response.headers

def process_csv(uploaded_file, prompt, api_key):
    file_contents = uploaded_file.read().decode('utf-8')
    input_file = io.StringIO(file_contents)

    reader = csv.DictReader(input_file)
    fieldnames = reader.fieldnames + ['lemur_response', 'number_occurred']

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for row in reader:
            future = executor.submit(process_row, row, prompt, api_key)
            futures.append(future)

        for future in as_completed(futures):
            row, headers = future.result()
            results.append(row)

            remaining = int(headers.get('x-ratelimit-remaining', '0'))
            reset = int(headers.get('x-ratelimit-reset', '60'))

            if remaining <= 10:
                time.sleep(reset + 1)

    return fieldnames, results

def download_csv(fieldnames, results):
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(fieldnames)
    for row in results:
        writer.writerow([row[field] for field in fieldnames])

    csv_string = output.getvalue()
    b64 = base64.b64encode(csv_string.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="output.csv">Download CSV File</a>'
    return href

def main():
    st.title("AssemblyAI LeMUR CSV Processor")

    api_key = st.text_input("Enter your AssemblyAI API key:")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    prompt = st.text_area("Enter the prompt for LeMUR:")

    if st.button("Process CSV"):
        if uploaded_file is not None and api_key:
            fieldnames, results = process_csv(uploaded_file, prompt, api_key)
            st.success("CSV processing completed.")
            st.markdown(download_csv(fieldnames, results), unsafe_allow_html=True)
        else:
            st.warning("Please upload a CSV file and enter your API key.")

if __name__ == "__main__":
    main()