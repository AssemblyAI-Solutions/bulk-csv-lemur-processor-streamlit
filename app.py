import streamlit as st
import csv
import json
import base64
import io
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

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

def get_transcript_id(row):
    if 'transcriptid' in row:
        return row['transcriptid']
    elif 'transcript_id' in row:
        return row['transcript_id']
    else:
        raise ValueError("CSV must contain a column named either 'transcriptid' or 'transcript_id'")

def process_row(row, prompt, api_key):
    transcript_id = get_transcript_id(row)

    try:
        response = make_lemur_request(transcript_id, prompt, api_key)
        response.raise_for_status()
        result = response.json()
        row['lemur_response'] = result['response']
    except:
        row['lemur_response'] = 'LeMUR Request Failed'

    return row, response.headers

def process_batch(batch, prompt, api_key):
    results = []
    headers = None
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_row, row, prompt, api_key) for row in batch]
        for future in as_completed(futures):
            row, row_headers = future.result()
            results.append(row)
            headers = row_headers  # Keep the last headers
    return results, headers

def process_csv(uploaded_file, prompt, api_key):
    file_contents = uploaded_file.read().decode('utf-8')
    input_file = io.StringIO(file_contents)

    reader = csv.DictReader(input_file)
    
    if 'transcriptid' not in reader.fieldnames and 'transcript_id' not in reader.fieldnames:
        st.error("CSV must contain a column named either 'transcriptid' or 'transcript_id'")
        return None, None

    fieldnames = reader.fieldnames + ['lemur_response']

    results = []
    total_rows = sum(1 for row in csv.DictReader(io.StringIO(file_contents)))
    progress_bar = st.progress(0)
    status_text = st.empty()
    rate_limit_info = st.empty()
    time_elapsed = st.empty()

    batch = []
    batch_size = 10
    processed_count = 0
    start_time = time.time()

    for row in reader:
        batch.append(row)
        
        if len(batch) == batch_size:
            batch_results, headers = process_batch(batch, prompt, api_key)
            results.extend(batch_results)
            processed_count += len(batch_results)

            progress = processed_count / total_rows
            progress_bar.progress(progress)
            status_text.text(f"Completed {processed_count}/{total_rows} requests")

            elapsed = time.time() - start_time
            time_elapsed.text(f"Time elapsed: {str(timedelta(seconds=int(elapsed)))}")

            limit = int(headers.get('x-ratelimit-limit', '0'))
            remaining = int(headers.get('x-ratelimit-remaining', '0'))
            reset = int(headers.get('x-ratelimit-reset', '60'))
            rate_limit_info.text(f"Rate Limit: {limit}, Remaining: {remaining}, Reset: {reset} seconds")

            if remaining <= 10:
                wait_message = st.empty()
                wait_message.warning(f"Rate limit approaching. Waiting for {reset + 1} seconds.")
                time.sleep(reset + 1)
                wait_message.empty()
                
                single_result, headers = process_batch([batch[0]], prompt, api_key)
                results.extend(single_result)
                processed_count += 1
                
                remaining = int(headers.get('x-ratelimit-remaining', '0'))
                rate_limit_info.text(f"Rate Limit: {limit}, Remaining: {remaining}, Reset: {reset} seconds")
            
            if remaining <= 20:
                batch_size = max(1, remaining - 10)  # Ensure batch size is at least 1
            else:
                batch_size = 10
            
            batch = []

    if batch:
        batch_results, _ = process_batch(batch, prompt, api_key)
        results.extend(batch_results)
        processed_count += len(batch_results)

    progress_bar.progress(1.0)
    status_text.text(f"Completed all {total_rows} requests")
    
    elapsed = time.time() - start_time
    time_elapsed.text(f"Total processing time: {str(timedelta(seconds=int(elapsed)))}")

    return fieldnames, results

def download_csv(fieldnames, results):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

    csv_string = output.getvalue()
    b64 = base64.b64encode(csv_string.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="processed_results.csv">Download Processed CSV File</a>'
    return href

def main():
    st.title("AssemblyAI LeMUR CSV Processor")

    st.write("""
    **Note:** Processing time depends on your rate limit and file size. 
    Streamlit requests timeout after about 10-15 minutes.
    The number of rows you can process is based on your rate limit. 
    A conservative estimate for the maximum number of rows you can process is:
    (Your Rate Limit - 10) * 10
    
    For example, if your rate limit is 30, you should limit your file to about 200 rows.
    Larger files can be processed but may take significantly longer due to rate limiting pauses.
    
    The CSV must contain a column named either 'transcriptid' or 'transcript_id'.
    """)

    api_key = st.text_input("Enter your AssemblyAI API key:")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    prompt = st.text_area("Enter the prompt for LeMUR:")

    if st.button("Process CSV"):
        if uploaded_file is not None and api_key:
            fieldnames, results = process_csv(uploaded_file, prompt, api_key)
            if fieldnames and results:
                st.success("CSV processing completed.")
                st.markdown(download_csv(fieldnames, results), unsafe_allow_html=True)
        else:
            st.warning("Please upload a CSV file and enter your API key.")

if __name__ == "__main__":
    main()