from typing import Any
from instabase.provenance.registration import register_fn
from instabase.ocr.client.libs.ibocr import ParsedIBOCRBuilder
from instabase.udf_utils.clients.udf_helpers import get_output_ibmsg_from_ibdoc
import json
import logging

@register_fn(provenance=False)
def re_extract(**kwargs):
  logging.info(f'Xxxxxxxxxxxx started BNYM.re_extract')
  
  fn_context = kwargs.get('_FN_CONTEXT_KEY')
  clients, _ = fn_context.get_by_col_name('CLIENTS')
  input_record, _ = fn_context.get_by_col_name('INPUT_RECORD')
  input_filepath = input_record['input_filepath']
  root_out, _ = fn_context.get_by_col_name('ROOT_OUTPUT_FOLDER')
  step_out_folder, _ = fn_context.get_by_col_name('STEP_FOLDER')
  
  parsed_builder, err = ParsedIBOCRBuilder.load_from_str(input_filepath, input_record['content'])
  for i, record in enumerate(parsed_builder.get_ibocr_records()):
    record_dict = record.as_dict()
    
    class_payload = record_dict['classification_payload']
    #class_label = class_payload['class_label']
    #class_score = class_payload['class_score']
    #class_payload['class_label'] = "Otherrrrrrrrr"



    refined_phrases, _ = record.get_refined_phrases()
    header_mapping = None
    for phrase in refined_phrases:
      col_name = phrase.get_column_name()
      if col_name == "Header_Mapping":
        header_mapping = json.loads(phrase.get_column_value()) # [{\"Item\": \"Header Row#\", \"Value\": \"\"}, ...
        logging.info(f'Xxxxxxxxxxxx BNYM.re_extract - header_mapping: {header_mapping}')
      elif col_name == "Intake_Sheet":
        x = json.loads(phrase.get_column_value())

        res = []
        for idx, row in enumerate(x):
          row["Value"] = str(header_mapping[idx]["Value"]) + " --- changed in reducer"
          res.append(row)
        res = json.dumps(res)
        
        phrase.set_column_value(res)
    
    builder = record.as_builder()
    builder.set_classification_payload(class_payload)
    builder.set_refined_phrases(refined_phrases)
    
    new_record, err = builder.as_record()
    parsed_builder.set_ibocr_record(i, new_record)

  content = get_output_ibmsg_from_ibdoc(step_out_folder, parsed_builder.serialize_to_string())

  return {'out_files': [{
    'filename': input_record['output_filename'],
    'content': content
  }]}
