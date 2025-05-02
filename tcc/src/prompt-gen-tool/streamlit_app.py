import streamlit as st
import prompt_functions

mapa_opcoes_menu = {
    'tipo_geracao': ["template", "prompt"],
    'template': prompt_functions.get_top_level_keys('prompt_templates.json'),
    'prompt': prompt_functions.get_all_prompt_template_keys('prompt_templates.json'),
    'instruction': prompt_functions.get_nested_keys('instructions.json'),
    'contexto': prompt_functions.get_nested_keys('contexts.json'),
    'formato': prompt_functions.get_nested_keys('format.json'),
    'fato': prompt_functions.get_top_level_keys('relevant_facts.json'),
    'exemplo': prompt_functions.get_top_level_keys('reference_analyses.json')
}

def obter_informacoes_prompt(tipo_geracao):
    if tipo_geracao == 'prompt':
        return "Informações sobre o prompt "
    elif tipo_geracao == 'template':
        return "Informações sobre o template "
    else:
        return ''
    
def opcoes_input_prompt(tipo_geracao, prompt_escolhido, selected_options):

    clear_selected_options(selected_options)

    if (tipo_geracao == 'template'):
        inputs = prompt_functions.find_inputs_in_all_prompts_from_template(prompt_escolhido)

    if (tipo_geracao == 'prompt'):
        inputs = prompt_functions.find_inputs_in_selected_prompt(prompt_escolhido)

    opcoes = {}
    for variavel in inputs:
        if variavel in mapa_opcoes_menu:
            opcoes[variavel] = mapa_opcoes_menu[variavel]
        
    return opcoes


def montar_prompt_por_selecoes(data):

    tipo = data.get('tipo')
    formulario = data.get('formulario')
    instrucao = data.get('instruction')
    contexto = data.get('contexto')
    fato = data.get('fato')
    referencia = data.get('exemplo')
    formato = data.get('formato')

    prompt_setup = prompt_functions.prompt_setup(instrucao, contexto, fato, referencia, formato)

    prompt_preenchido = ''

    if (tipo == 'template'):
        prompt_preenchido = prompt_functions.load_info_into_all_prompts_from_template(formulario, prompt_setup)

    if (tipo == 'prompt'):
        prompt_preenchido = prompt_functions.load_info_into_selected_prompt(formulario, prompt_setup)

    return prompt_preenchido


def create_dropdown(dropdown_name, options, selected_options):
    selected_options[dropdown_name] = st.sidebar.selectbox(str(dropdown_name).capitalize(), options)
    return selected_options


def add_dropdowns(variaveis_dict, selected_options):

    for key, value in variaveis_dict.items():
        create_dropdown(key, value, selected_options)
    
    return selected_options


def clear_selected_options(selected_options):
    selected_options.clear()


def obterSelecoesPrompt(tipo, prompt, selected_options):
    
    dadosPrompt = {
        'tipo': tipo,
        'formulario': prompt
    }

    for key, value in selected_options.items():
        dadosPrompt[key] = value
    
    return dadosPrompt


def prevent_markdown_interpretation(string):
    markdown_safe_string = string.replace("###", "### \\###")
    
    return markdown_safe_string


def main():
    st.set_page_config(page_title="Geração de Prompts", page_icon=None, layout='wide', initial_sidebar_state='expanded')
    st.title("Geração de Prompts")

    # Sidebar menu
    st.sidebar.title("Menu de opções")
    
    tipo_geracao = st.sidebar.selectbox("Tipo de geração", mapa_opcoes_menu['tipo_geracao'])
    
    if tipo_geracao == 'template':
        prompt_escolhido = st.sidebar.selectbox("Escolha um template", mapa_opcoes_menu['template'])
    elif tipo_geracao == 'prompt':
        prompt_escolhido = st.sidebar.selectbox("Escolha um prompt", mapa_opcoes_menu['prompt'])
    
    # Display selected options
    st.markdown("---")
    #st.write(f"Tipo de geração: {tipo_geracao}")
    #st.write(f"{tipo_geracao.capitalize()} escolhido: {prompt_escolhido}")

    selected_options = {}

    inputs_prompt = opcoes_input_prompt(tipo_geracao, prompt_escolhido, selected_options)
    add_dropdowns(inputs_prompt, selected_options)

    #for key, value in selected_options.items():
    #    st.write(f"{key.capitalize()} escolhido: {value}")
    
    informacoes = obter_informacoes_prompt(tipo_geracao)
    st.write(f"\n### Informações do {tipo_geracao.capitalize()}: ")
    st.write(f"{informacoes}{prompt_escolhido}...")

    st.markdown("---")

    if st.sidebar.button("Confirmar"):
        dadosPrompt = obterSelecoesPrompt(tipo_geracao, prompt_escolhido, selected_options)
        prompt_preenchido = montar_prompt_por_selecoes(dadosPrompt)
        if tipo_geracao == 'prompt':
            st.write(f"{prompt_preenchido}")
        if tipo_geracao == 'template':
            for key, value in prompt_preenchido.items():
                keystring = str(key).replace('_', ' ')
                st.title(f"{keystring.capitalize()}")
                st.write(f"{prevent_markdown_interpretation(value)}")
                st.markdown("---")



if __name__ == "__main__":
    main()
