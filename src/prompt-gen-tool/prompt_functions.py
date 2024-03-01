from pathlib import Path
import json
import re

PROJECT_NAME = 'polarity_ratings'

PROJECT_ROOT_DIR = ''

PROMPT_TEMPLATES_JSON = 'prompt_templates.json'
CONTEXTS_JSON = 'contexts.json'
INSTRUCTIONS_JSON = 'instructions.json'
REFERENCE_ANALYSES_JSON = 'reference_analyses.json'
MATERIAL_FACTS_JSON = 'relevant_facts.json'
FORMAT_JSON = 'format.json'

def get_project_root_dir():
    
    global PROJECT_ROOT_DIR
    current_dir = Path(__file__).parent

    while (current_dir.name != PROJECT_NAME):
        current_dir = current_dir.parent
        PROJECT_ROOT_DIR = current_dir


def load_from_json(json_file: str) -> dict:
    
    get_project_root_dir()

    with open(PROJECT_ROOT_DIR / 'data//prompts_modules' / json_file, encoding='utf-8') as arq:
        dictionary = json.load(arq)

    return dictionary

def load_info_into_all_prompts_from_template (template_title: str, input_variables: dict) -> dict:
    
    template = load_from_json(PROMPT_TEMPLATES_JSON).get(template_title)
    prompts = {}
    loaded_prompts = {}

    for key in template.keys():
        if str(key).find('prompt') > -1:
            prompts[key] = template[key]

    for key, value in prompts.items():
        formated_prompt = format_template_variables(value, input_variables)
        loaded_prompts.update({key: formated_prompt})

    return loaded_prompts


def format_template_variables(input_string: str, variable_values: dict) -> str:
    
    valid_variables = {var: value for var, value in variable_values.items() if var in input_string}
    return input_string.format(**valid_variables)

def load_info_into_selected_prompt (selected_prompt: str, input_variables: dict) -> str:
    
    templates = load_from_json(PROMPT_TEMPLATES_JSON)
    prompt = find_item_by_key(templates, selected_prompt)
    return format_template_variables(prompt, input_variables)


def load_info_from_selected_key_item (json_file: str, selected_item: str) -> str:
    
    dictionary = load_from_json(json_file=json_file)
    return find_item_by_key(dictionary, selected_item)


def find_item_by_key(data, target):
    for key, value in data.items():
        if key == target:
            return value
        elif isinstance(value, dict):
            result = find_item_by_key(value, target)
            if result is not None:
                return result
    return None

def get_all_keys(data):
    keys = set()

    if isinstance(data, dict):
        for key, value in data.items():
            keys.add(key)
            if isinstance(value, (dict, list)):
                keys.update(get_all_keys(value))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                keys.update(get_all_keys(item))

    return keys


def get_all_nested_keys_within_target_key(data, target_key):
    nested_keys = set()
    
    if isinstance(data, dict):
        if target_key in data:
            value = data[target_key]
            if isinstance(value, dict):
                nested_keys.update(value.keys())
                for sub_value in value.values():
                    if isinstance(sub_value, (dict, list)):
                        nested_keys.update(get_all_nested_keys_within_target_key(sub_value, target_key))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, (dict, list)):
                        nested_keys.update(get_all_nested_keys_within_target_key(item, target_key))

    return nested_keys


def get_all_prompt_template_keys(json_file):
    data = load_from_json(json_file)
    keys = set()
    prompt_keys = set()

    keys = get_all_keys(data)

    for key in keys:
        if str(key).find('prompt') > -1:
            prompt_keys.add(key)

    return list(prompt_keys)


def get_all_prompts_from_template_key(json_file, template):
    data = load_from_json(json_file)
    template_nested_keys = set()
    prompt_keys = set()

    template_nested_keys = get_all_nested_keys_within_target_key(data, template)

    for key in template_nested_keys:
        if str(key).find('prompt') > -1:
            prompt_keys.add(key)

    return list(prompt_keys)


def get_top_level_keys(json_file):
    data = load_from_json(json_file)
    top_level_keys = set()

    if isinstance(data, dict):
        top_level_keys.update(data.keys())

    return list(top_level_keys)


def get_nested_keys(json_file):
    nested_keys = set()

    top_level_keys = get_top_level_keys(json_file)
    data = load_from_json(json_file)
    all_keys = get_all_keys(data)

    for key in all_keys:
        if key not in top_level_keys:
            nested_keys.add(key)

    return list(nested_keys)


def find_inputs_in_prompt(prompt):
    pattern = r'\{([^}]+)\}'
    variables = re.findall(pattern, prompt)
    return variables


def find_inputs_in_all_prompts_from_template(template):
    prompts_from_template = get_all_prompts_from_template_key(PROMPT_TEMPLATES_JSON, template)

    all_variables = list()

    for prompt in prompts_from_template:
        selected_prompt = load_info_from_selected_key_item(PROMPT_TEMPLATES_JSON, prompt)
        prompt_variables = find_inputs_in_prompt(selected_prompt)
        all_variables += prompt_variables

    return all_variables


def find_inputs_in_selected_prompt(prompt):
    selected_prompt = load_info_from_selected_key_item(PROMPT_TEMPLATES_JSON, prompt)
    return find_inputs_in_prompt(selected_prompt)



def prompt_setup(selected_instruction: str = '', selected_context: str = '', selected_material_fact: str = '', selected_reference_analyses: str = '', selected_format: str = ''):
    
    prompt_info = {}

    if selected_instruction != '' and selected_instruction != None:
        prompt_info.update({'instruction': load_info_from_selected_key_item(INSTRUCTIONS_JSON, selected_instruction)})

    if selected_context != '' and selected_context != None:
        prompt_info.update({'contexto': load_info_from_selected_key_item(CONTEXTS_JSON, selected_context)})

    if selected_format != '' and selected_format != None:
        prompt_info.update({'formato': load_info_from_selected_key_item(FORMAT_JSON, selected_format)})

    if selected_material_fact != '' and selected_material_fact != None:
        fato = load_info_from_selected_key_item(MATERIAL_FACTS_JSON, selected_material_fact)

        with open(PROJECT_ROOT_DIR / fato.__getitem__('path'), encoding='utf-8') as arq:
            material_fact_text = arq.read()
        
        prompt_info.update({'tema': fato.__getitem__('tema')})
        prompt_info.update({'empresa': fato.__getitem__('empresa')})
        prompt_info.update({'fato': material_fact_text})

    if selected_reference_analyses != '' and selected_reference_analyses != None:
        analise_exemplo = load_info_from_selected_key_item(REFERENCE_ANALYSES_JSON, selected_reference_analyses)

        with open(PROJECT_ROOT_DIR / analise_exemplo.__getitem__('path'), encoding='utf-8') as arq:
            analise_exemplo_text = arq.read()

        prompt_info.update({'exemplo': analise_exemplo_text})

    return prompt_info
