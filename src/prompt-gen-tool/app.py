from flask import Flask, render_template, jsonify, request
import prompt_functions

app = Flask(__name__)

mapa_opcoes_menu = {
    'tipo_formulario': ["template", "prompt"],
    'template': prompt_functions.get_top_level_keys('prompt_templates.json'),
    'prompt': prompt_functions.get_all_prompt_template_keys('prompt_templates.json'),
    'instruction': prompt_functions.get_nested_keys('instructions.json'),
    'contexto': prompt_functions.get_nested_keys('contexts.json'),
    'formato': prompt_functions.get_nested_keys('format.json'),
    'fato': prompt_functions.get_top_level_keys('relevant_facts.json'),
    'exemplo': prompt_functions.get_top_level_keys('reference_analyses.json')
}

def obter_informacoes_formulario(tipo_formulario):
    if tipo_formulario == 'prompt':
        return {"informacao": "Informações para o formulário prompt"}
    elif tipo_formulario == 'template':
        return {"informacao": "Informações para o formulário template"}
    else:
        return {}


@app.route('/')
def index():
    opcoes = {'opcoes_tipo_formulario': mapa_opcoes_menu['tipo_formulario'],
        'opcoes_prompt': mapa_opcoes_menu['prompt'],
        'opcoes_template': mapa_opcoes_menu['template']}
    
    return render_template('index.html', opcoes_formulario=opcoes)

@app.route('/opcoes_formulario')
def opcoes_formulario():
    tipo_formulario = request.args.get('tipo_formulario', '')
    formulario_escolhido = request.args.get('formulario_escolhido', '')

    if (tipo_formulario == 'template'):
        inputs = prompt_functions.find_inputs_in_all_prompts_from_template(formulario_escolhido)

    if (tipo_formulario == 'prompt'):
        inputs = prompt_functions.find_inputs_in_selected_prompt(formulario_escolhido)

    opcoes = {}
    for variavel in inputs:
        if variavel in mapa_opcoes_menu:
            opcoes['opcoes_'+ variavel] = mapa_opcoes_menu[variavel]
    

    return jsonify(opcoes)

@app.route('/informacoes_formulario')
def informacoes_formulario():
    tipo_formulario = request.args.get('tipo_formulario', 'prompt')
    informacoes = obter_informacoes_formulario(tipo_formulario)
    return jsonify(informacoes)

@app.route('/enviarSelecoes', methods=['POST'])
def montar_prompt_por_selecoes():
    data = request.json

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

    return jsonify({"prompt": prompt_preenchido})

if __name__ == '__main__':
    app.run()
