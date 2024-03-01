let opcoes_tipo_formulario = [];

function updateOptions(opcaoSelecionada) {

    let opcoes_formulario_str = document.getElementById("opcoes-formulario").value;
    let opcoes_formulario_dict = Function('return ' + opcoes_formulario_str)();

    if (opcaoSelecionada == 'prompt') {
        opcoes_tipo_formulario = opcoes_formulario_dict.opcoes_prompt;
    } else if (opcaoSelecionada == 'template') {
        opcoes_tipo_formulario = opcoes_formulario_dict.opcoes_template
    }
    
    // Clear existing options
    const select = document.getElementById("opcao-tipo-formulario");
    select.innerHTML = "";
    
    // Add new options
    opcoes_tipo_formulario.forEach(opcao => {
        const option = document.createElement("option");
        option.value = opcao;
        option.textContent = opcao;
        select.appendChild(option);
    });
}

updateOptions(document.getElementById("tipo-formulario").value);

// Função para carregar opções de tipos de formulário do servidor
function carregarOpcoesFormulario(tipoFormulario, formularioEscolhido) {
    return fetch(`/opcoes_formulario?tipo_formulario=${tipoFormulario}&formulario_escolhido=${formularioEscolhido}`)
        .then(response => response.json());
}

function criarDropdowns(opcoes) {
    const formularioContainer = document.getElementById('formulario-container');

    for (let label in opcoes) {
        if (opcoes.hasOwnProperty(label)) {
            const campoContainer = document.createElement('div');
            campoContainer.classList.add('campo-formulario');
            const labelCampo = document.createElement('label');
            labelCampo.textContent = label.replace("opcoes_", "") + ' : ';
            campoContainer.appendChild(labelCampo);
            const dropdown = document.createElement("select");
            dropdown.id = label.toLowerCase().replace(/\s/g, '-');
            opcoes[label].forEach(opcao => {
                const option = document.createElement('option');
                option.value = opcao;
                option.textContent = opcao;
                dropdown.appendChild(option);
            });
            campoContainer.appendChild(dropdown);
            formularioContainer.appendChild(campoContainer);
        }
    }
}

function obterSelecoes(opcoes) {
    selecoes = {}

    for (let label in opcoes) {
        if (opcoes.hasOwnProperty(label)) {
            const campoId = label.toLowerCase().replace(/\s/g, '-');
            selecoes[label.replace("opcoes_", "")] = document.getElementById(campoId).value;
        }
    }

    return selecoes;
}

// Função para criar e exibir o formulário com base no tipo selecionado
function exibirFormulario(tipo, formularioSelecionado) {
    const formularioContainer = document.getElementById('formulario-container');
    formularioContainer.innerHTML = ''; 
    
    carregarOpcoesFormulario(tipo, formularioSelecionado)
        .then(opcoes => {

            criarDropdowns(opcoes);

            const btnEnviar = document.createElement('button');
            btnEnviar.textContent = 'Enviar';
            btnEnviar.addEventListener('click', function() {
                opcoesSelecionadas = obterSelecoes(opcoes);

                enviarSelecoesPrompt(tipo, formularioSelecionado, opcoesSelecionadas);
            });

            formularioContainer.appendChild(btnEnviar);
        });
}

function enviarSelecoesPrompt(tipo, formulario, informacoesSelecionadas) {
    
    const dadosPrompt = {
        tipo: tipo,
        formulario: formulario,
    };

    for (let campo in informacoesSelecionadas) {
        dadosPrompt[campo] = informacoesSelecionadas[campo];
    }

    fetch('/enviarSelecoes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dadosPrompt)
    })
    .then(response => response.json())
    .then(data => {
        const respostaContainer = document.getElementById('resposta-container');
        respostaContainer.innerHTML = '';

        if (typeof data.prompt === 'string') {
            respostaContainer.innerHTML = `<p>${data.prompt}</p>`;
        } else if (typeof data.prompt === 'object' && data.prompt !== null) {
            const lista = document.createElement('ul');

            for (const [chave, valor] of Object.entries(data.prompt)) {
                const itemLista = document.createElement('li');
                itemLista.innerHTML = `<strong>${chave}:</strong> ${valor}`;
                lista.appendChild(itemLista);
            }

            respostaContainer.appendChild(lista);
        } else {
            console.error('Tipo de resposta não suportado:', typeof data.prompt);
        }
    })
    .catch(error => {
        console.error('Erro ao realizar ação:', error);
    });
}

document.getElementById('confirmar-btn').addEventListener('click', function() {
    const tipoFormulario = document.getElementById('tipo-formulario').value;
    const formularioEscolhido = document.getElementById('opcao-tipo-formulario').value;
    const resposta = document.getElementById("resposta-container");
    resposta.innerHTML = "";
    exibirFormulario(tipoFormulario, formularioEscolhido);
});
