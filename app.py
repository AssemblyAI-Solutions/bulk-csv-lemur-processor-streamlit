import streamlit as st
import csv
import threading
import assemblyai as aai
import json
import base64
import io
import csv


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

def process_row(row, results, prompt):
    transcript_id = row['transcriptid']

    try:
        transcript = aai.Transcript.get_by_id(transcript_id)
        result = transcript.lemur.task(prompt)
        row['lemur_response'] = result.response
        negative_questions = parse_json_from_resp(result.response)
    except:
        result = 'LeMUR Request Failed'
        row['lemur_response'] = 'LeMUR Request Failed'
        negative_questions = parse_json_from_resp('LeMUR Request Failed')


    number_occurred = count_yes(negative_questions)

    row['number_occurred'] = number_occurred
    results.append(row)

def process_csv(uploaded_file, prompt):
    file_contents = uploaded_file.read().decode('utf-8')
    input_file = io.StringIO(file_contents)

    reader = csv.DictReader(input_file)
    fieldnames = reader.fieldnames + ['lemur_response', 'number_occurred']

    results = []
    threads = []

    for row in reader:
        thread = threading.Thread(target=process_row, args=(row, results, prompt))
        threads.append(thread)
        thread.start()

        if len(threads) == 10:
            for thread in threads:
                thread.join()
            threads = []

    for thread in threads:
        thread.join()

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
    aai.settings.api_key = api_key

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    prompt = st.text_area("Enter the prompt for LeMUR:")

    if st.button("Process CSV"):
        if uploaded_file is not None:
            fieldnames, results = process_csv(uploaded_file, prompt)
            st.success("CSV processing completed.")
            st.markdown(download_csv(fieldnames, results), unsafe_allow_html=True)
        else:
            st.warning("Please upload a CSV file.")

if __name__ == "__main__":
    main()